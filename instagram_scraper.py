#!/usr/bin/env python3
"""
Instagram Reel Scraper
======================
Scrapes trending Reels by hashtag via instagrapi, then routes each video
URL through the Telegram download bot to get a clean, watermark-free file.

Flow: browse hashtags → filter → send URL to Telegram bot → save file

Content scraped from Instagram is already proven to work on Instagram.

Usage:
    python instagram_scraper.py                      # scrape motion niche (default)
    python instagram_scraper.py --amount 100         # grab more videos
    python instagram_scraper.py --min-views 300000   # lower view threshold
    python instagram_scraper.py --no-telegram        # direct download (no Telegram)
"""

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime

from instagrapi import Client
from instagrapi.exceptions import (
    ChallengeRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
    RateLimitError,
)

import config
import scraper_config as tg_cfg
from telegram_sender import send_and_download_sync

# ─── Competitor accounts to scrape ────────────────────────────────
# Reels from these accounts skip the high view threshold (trusted sources).
# Add more usernames here anytime.
COMPETITOR_ACCOUNTS = [
    "memeyahu",
    "twinkpotato",
    "womenconsumer",
    "uncrustamemes",
]
ACCOUNT_MIN_VIEWS   = 50_000   # lower bar — we trust these accounts
AMOUNT_PER_ACCOUNT  = 30       # reels to pull per account

# ─── Hashtags for the motion niche ────────────────────────────────
# Mix of high-volume and niche-specific tags
MOTION_HASHTAGS = [
    # Sigma / mindset
    "sigma", "sigmamale", "sigmagrindset", "villainarc",
    # Motivation / money
    "motivation", "moneymotivation", "successmindset", "grindset",
    "money", "hustle", "entrepreneur", "mindset",
    # Movie/show edits — proven viral format
    "wolfofwallstreet", "breakingbad", "peakyblinders",
    "americanpsycho", "fightclub", "thesopranos", "joker",
    # Broader reach
    "luxurylifestyle", "fyp", "reels", "viral",
    # Aura / rizz
    "aura", "rizz", "pov",
]

# ─── Filters ──────────────────────────────────────────────────────
MIN_VIEWS       = 200_000    # minimum views to download
MAX_DURATION    = 30         # seconds — short clips rewatched = explore push
MIN_DURATION    = 3          # skip sub-3-second clips
AMOUNT_PER_TAG  = 15         # how many posts to check per hashtag (top + recent)

# ─── Paths ────────────────────────────────────────────────────────
DOWNLOAD_DIR    = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")
SEEN_LOG        = os.path.join(os.path.dirname(__file__), "ig_scraped.txt")
SESSION_FILE    = config.SESSION_FILE


def load_seen_ids() -> set:
    """Load media PKs we've already downloaded."""
    if not os.path.exists(SEEN_LOG):
        return set()
    with open(SEEN_LOG) as f:
        return {line.strip() for line in f if line.strip()}


def mark_seen(pk: str):
    with open(SEEN_LOG, "a") as f:
        f.write(pk + "\n")


def login() -> Client:
    cl = Client()
    if config.PROXY:
        cl.set_proxy(config.PROXY)
    cl.delay_range = [3, 8]

    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(config.USERNAME, config.PASSWORD)
            print(f"  [scraper] Logged in as @{config.USERNAME} (session)")
            return cl
        except Exception:
            pass

    cl.login(config.USERNAME, config.PASSWORD)
    cl.dump_settings(SESSION_FILE)
    print(f"  [scraper] Logged in as @{config.USERNAME} (fresh)")
    return cl


def get_reels_for_tag(cl: Client, hashtag: str, amount: int) -> list:
    """Fetch top + recent reels for a hashtag, return Media list."""
    medias = []
    try:
        top = cl.hashtag_medias_top(hashtag, amount=amount)
        medias.extend(top)
        time.sleep(random.uniform(1.5, 3.5))
    except (PleaseWaitFewMinutes, RateLimitError):
        print(f"  [scraper] Rate limited on #{hashtag} — sleeping 60s")
        time.sleep(60)
    except Exception as e:
        print(f"  [scraper] #{hashtag} top error: {e}")

    try:
        recent = cl.hashtag_medias_recent(hashtag, amount=amount)
        medias.extend(recent)
        time.sleep(random.uniform(1.5, 3.5))
    except (PleaseWaitFewMinutes, RateLimitError):
        print(f"  [scraper] Rate limited on #{hashtag} recent — sleeping 60s")
        time.sleep(60)
    except Exception as e:
        print(f"  [scraper] #{hashtag} recent error: {e}")

    return medias


def get_reels_for_account(cl: Client, username: str, amount: int) -> list:
    """Fetch recent Reels from a specific account."""
    try:
        user_id = cl.user_id_from_username(username)
        time.sleep(random.uniform(1, 2))
        clips = cl.user_clips(user_id, amount=amount)
        print(f"  @{username} — found {len(clips)} reels")
        return clips
    except (PleaseWaitFewMinutes, RateLimitError):
        print(f"  [scraper] Rate limited on @{username} — sleeping 60s")
        time.sleep(60)
        return []
    except Exception as e:
        print(f"  [scraper] @{username} error: {e}")
        return []


def is_reel(media) -> bool:
    """Check if media is a Reel (not a photo or carousel)."""
    media_type   = getattr(media, "media_type",   None)
    product_type = getattr(media, "product_type", "")
    return media_type == 2 or product_type == "clips"


def passes_filters(media, min_views: int, seen_ids: set) -> tuple[bool, str]:
    """Returns (passes, reason_if_rejected)."""
    pk = str(media.pk)

    if pk in seen_ids:
        return False, "already downloaded"

    if not is_reel(media):
        return False, "not a reel"

    views = getattr(media, "view_count", 0) or 0
    if views < min_views:
        return False, f"views too low ({views:,})"

    duration = getattr(media, "video_duration", 0) or 0
    if duration > MAX_DURATION:
        return False, f"too long ({duration:.0f}s)"
    if duration < MIN_DURATION:
        return False, f"too short ({duration:.1f}s)"

    return True, ""


def reel_url(media) -> str:
    """Build the public Instagram Reel URL from media object."""
    code = getattr(media, "code", None) or str(media.pk)
    return f"https://www.instagram.com/reel/{code}/"


def download_via_telegram(url: str, download_dir: str) -> bool:
    """Send URL to Telegram bot, wait for video reply, save file. Returns True on success."""
    os.makedirs(download_dir, exist_ok=True)
    sent, downloaded, failed = send_and_download_sync(
        [url],
        bot_username=tg_cfg.TELEGRAM_BOT_USERNAME,
        download_dir=download_dir,
    )
    return downloaded == 1


def download_reel_direct(cl: Client, media, download_dir: str) -> str | None:
    """Fallback: download directly via instagrapi (may have watermark metadata)."""
    os.makedirs(download_dir, exist_ok=True)
    try:
        path = cl.video_download(media.pk, folder=download_dir)
        return str(path)
    except Exception as e:
        print(f"  [scraper] Direct download failed for {media.pk}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Scrape Instagram Reels for the motion niche")
    parser.add_argument("--amount",         type=int,  default=200,       help="Target number of videos to download")
    parser.add_argument("--min-views",       type=int,  default=MIN_VIEWS, help=f"Min view count for hashtags (default: {MIN_VIEWS:,})")
    parser.add_argument("--hashtags",        nargs="+", default=None,      help="Custom hashtags (without #)")
    parser.add_argument("--dry-run",         action="store_true",          help="Find videos but don't download")
    parser.add_argument("--no-telegram",     action="store_true",          help="Skip Telegram — download directly via instagrapi")
    parser.add_argument("--accounts-only",   action="store_true",          help="Only scrape competitor accounts, skip hashtags")
    parser.add_argument("--hashtags-only",   action="store_true",          help="Only scrape hashtags, skip accounts")
    args = parser.parse_args()

    print("""
╔══════════════════════════════════════════════════════╗
║     Instagram Reel Scraper — Motion Niche            ║
║     Accounts → Hashtags → Telegram → Save            ║
╚══════════════════════════════════════════════════════╝
""")

    hashtags     = args.hashtags or MOTION_HASHTAGS
    target       = args.amount
    min_views    = args.min_views
    seen_ids     = load_seen_ids()
    downloaded   = 0
    checked      = 0
    use_telegram = not args.no_telegram

    print(f"  Target:    {target} videos")
    print(f"  Accounts:  {', '.join('@' + a for a in COMPETITOR_ACCOUNTS)} (min {ACCOUNT_MIN_VIEWS:,} views)")
    print(f"  Hashtags:  {len(hashtags)} tags (min {min_views:,} views)")
    print(f"  Max dur:   {MAX_DURATION}s")
    print(f"  Download:  {'Telegram bot (@' + tg_cfg.TELEGRAM_BOT_USERNAME + ')' if use_telegram else 'direct (instagrapi)'}")
    print(f"  Already have: {len(seen_ids)} videos")
    print(f"  Save to:   {DOWNLOAD_DIR}\n")

    print("  Logging in...")
    cl = login()
    print()

    def process_media_list(medias, source_label, threshold):
        """Deduplicate, filter, and download a list of media. Returns count downloaded."""
        nonlocal downloaded, checked
        count = 0

        seen_pks = set()
        unique = []
        for m in medias:
            pk = str(m.pk)
            if pk not in seen_pks:
                seen_pks.add(pk)
                unique.append(m)

        for media in unique:
            if downloaded >= target:
                break

            checked += 1
            pk    = str(media.pk)
            views = getattr(media, "view_count", 0) or 0
            dur   = getattr(media, "video_duration", 0) or 0

            passes, reason = passes_filters(media, threshold, seen_ids)
            if not passes:
                continue

            user = getattr(getattr(media, "user", None), "username", "unknown")
            print(f"    [{downloaded+1}] @{user} — {views:,} views, {dur:.0f}s")

            if args.dry_run:
                mark_seen(pk)
                seen_ids.add(pk)
                downloaded += 1
                count += 1
                continue

            success = False
            if use_telegram:
                url = reel_url(media)
                print(f"         → {url}")
                success = download_via_telegram(url, DOWNLOAD_DIR)
            else:
                path = download_reel_direct(cl, media, DOWNLOAD_DIR)
                success = path is not None
                if success:
                    print(f"         saved: {os.path.basename(path)}")

            if success:
                mark_seen(pk)
                seen_ids.add(pk)
                downloaded += 1
                count += 1
                time.sleep(random.uniform(2, 5))
            else:
                print(f"         failed — skipping")

        return count

    # ── Phase 1: Competitor accounts (trusted, lower view bar) ─────
    if not args.hashtags_only:
        print(f"{'─'*54}")
        print(f"  PHASE 1 — Scraping {len(COMPETITOR_ACCOUNTS)} competitor accounts")
        print(f"{'─'*54}")
        for username in COMPETITOR_ACCOUNTS:
            if downloaded >= target:
                break
            medias = get_reels_for_account(cl, username, AMOUNT_PER_ACCOUNT)
            got = process_media_list(medias, f"@{username}", ACCOUNT_MIN_VIEWS)
            if got:
                print(f"  @{username} → {got} videos downloaded\n")
            time.sleep(random.uniform(5, 10))

    # ── Phase 2: Hashtags (fill remaining quota) ───────────────────
    if not args.accounts_only and downloaded < target:
        print(f"\n{'─'*54}")
        print(f"  PHASE 2 — Filling remaining {target - downloaded} from hashtags")
        print(f"{'─'*54}")
        hashtags = list(hashtags)
        random.shuffle(hashtags)

        for hashtag in hashtags:
            if downloaded >= target:
                break

            print(f"\n  #{hashtag}")
            medias = get_reels_for_tag(cl, hashtag, AMOUNT_PER_TAG)
            got = process_media_list(medias, f"#{hashtag}", min_views)
            if got:
                print(f"  #{hashtag} → {got} videos\n")
            time.sleep(random.uniform(5, 12))

    print(f"\n{'='*54}")
    print(f"  Done! Downloaded {downloaded} new videos")
    print(f"  Checked {checked} reels total")
    print(f"  Saved to: {DOWNLOAD_DIR}")
    print(f"  Total in folder: {len([f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.mp4')] if os.path.exists(DOWNLOAD_DIR) else [])}")
    print(f"{'='*54}\n")


if __name__ == "__main__":
    main()
