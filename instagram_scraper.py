#!/usr/bin/env python3
"""
Instagram Reel Scraper
======================
Scrapes trending Reels by hashtag and downloads them directly via instagrapi.
No Telegram bot, no Playwright — just Instagram's own API browsing.

Content scraped from Instagram is already proven to work on Instagram.

Usage:
    python instagram_scraper.py                      # scrape motion niche (default)
    python instagram_scraper.py --amount 100         # grab more videos
    python instagram_scraper.py --min-views 300000   # lower view threshold
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


def download_reel(cl: Client, media, download_dir: str) -> str | None:
    """Download reel to folder. Returns local file path or None."""
    os.makedirs(download_dir, exist_ok=True)
    try:
        path = cl.video_download(media.pk, folder=download_dir)
        return str(path)
    except Exception as e:
        print(f"  [scraper] Download failed for {media.pk}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Scrape Instagram Reels for the motion niche")
    parser.add_argument("--amount",    type=int,   default=200,       help="Target number of videos to download")
    parser.add_argument("--min-views", type=int,   default=MIN_VIEWS, help=f"Min view count (default: {MIN_VIEWS:,})")
    parser.add_argument("--hashtags",  nargs="+",  default=None,      help="Custom hashtags (without #)")
    parser.add_argument("--dry-run",   action="store_true",           help="Find videos but don't download")
    args = parser.parse_args()

    print("""
╔══════════════════════════════════════════════════════╗
║     Instagram Reel Scraper — Motion Niche            ║
║     Browse hashtags → filter → download direct       ║
╚══════════════════════════════════════════════════════╝
""")

    hashtags   = args.hashtags or MOTION_HASHTAGS
    target     = args.amount
    min_views  = args.min_views
    seen_ids   = load_seen_ids()
    downloaded = 0
    checked    = 0

    print(f"  Target:    {target} videos")
    print(f"  Min views: {min_views:,}")
    print(f"  Max dur:   {MAX_DURATION}s")
    print(f"  Hashtags:  {len(hashtags)}")
    print(f"  Already have: {len(seen_ids)} videos")
    print(f"  Save to:   {DOWNLOAD_DIR}\n")

    print("  Logging in...")
    cl = login()
    print()

    # Shuffle hashtags so we don't always start with the same ones
    hashtags = list(hashtags)
    random.shuffle(hashtags)

    for hashtag in hashtags:
        if downloaded >= target:
            break

        print(f"  #{hashtag}")
        medias = get_reels_for_tag(cl, hashtag, AMOUNT_PER_TAG)

        # Deduplicate within this batch
        seen_pks = set()
        unique = []
        for m in medias:
            pk = str(m.pk)
            if pk not in seen_pks:
                seen_pks.add(pk)
                unique.append(m)

        tag_downloaded = 0
        for media in unique:
            if downloaded >= target:
                break

            checked += 1
            pk      = str(media.pk)
            views   = getattr(media, "view_count", 0) or 0
            dur     = getattr(media, "video_duration", 0) or 0

            passes, reason = passes_filters(media, min_views, seen_ids)

            if not passes:
                continue

            user = getattr(getattr(media, "user", None), "username", "unknown")
            print(f"    [{downloaded+1}] @{user} — {views:,} views, {dur:.0f}s — pk:{pk[:10]}...")

            if args.dry_run:
                print(f"         [dry-run] would download")
                mark_seen(pk)
                seen_ids.add(pk)
                downloaded += 1
                tag_downloaded += 1
                continue

            path = download_reel(cl, media, DOWNLOAD_DIR)
            if path:
                mark_seen(pk)
                seen_ids.add(pk)
                downloaded += 1
                tag_downloaded += 1
                print(f"         saved: {os.path.basename(path)}")

                # Human-like pause between downloads
                time.sleep(random.uniform(2, 5))
            else:
                print(f"         failed — skipping")

        if tag_downloaded > 0:
            print(f"  #{hashtag} done — got {tag_downloaded} videos\n")

        # Pause between hashtags to avoid rate limiting
        if downloaded < target:
            sleep = random.uniform(5, 12)
            time.sleep(sleep)

    print(f"\n{'='*54}")
    print(f"  Done! Downloaded {downloaded} new videos")
    print(f"  Checked {checked} reels across {len(hashtags)} hashtags")
    print(f"  Saved to: {DOWNLOAD_DIR}")
    print(f"  Total in folder: {len([f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.mp4')] if os.path.exists(DOWNLOAD_DIR) else [])}")
    print(f"{'='*54}\n")


if __name__ == "__main__":
    main()
