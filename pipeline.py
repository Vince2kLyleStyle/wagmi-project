#!/usr/bin/env python3
"""
Content Pipeline — TikTok -> Instagram
Scrape trending content -> Download -> Post to IG accounts

Now with:
  - Per-niche configuration (captions, hashtags, safety limits)
  - Telegram status notifications
  - Safety-managed posting limits

Usage:
    py pipeline.py                           # scrape all niches + post
    py pipeline.py --scrape-only             # just scrape, don't post
    py pipeline.py --post-only               # just post existing videos
    py pipeline.py --niche trading memes     # only specific niches
    py pipeline.py --status                  # show account safety status
"""

import argparse
import json
import os
import sys
import subprocess
from datetime import datetime

import scraper_config as cfg
import safety


BANNER = r"""
╔═══════════════════════════════════════════════════════════════╗
║          CONTENT PIPELINE — TikTok -> Instagram                ║
║    Scrape viral content -> Download -> Post (safety-managed)   ║
╚═══════════════════════════════════════════════════════════════╝
"""

ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), "accounts.json")


def notify(message: str) -> None:
    """Send a Telegram notification if configured."""
    if not cfg.TELEGRAM_NOTIFY_ENABLED:
        return
    try:
        from telegram_sender import create_client as tg_create
        import asyncio

        async def _send():
            client = await tg_create()
            if client:
                try:
                    await client.send_message(cfg.TELEGRAM_NOTIFY_CHAT, message)
                finally:
                    await client.disconnect()

        asyncio.run(_send())
    except Exception as e:
        print(f"  [notify] Failed to send notification: {e}")


def load_accounts():
    """Load IG accounts from accounts.json."""
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    with open(ACCOUNTS_FILE, "r") as f:
        accounts = json.load(f)
    by_niche = {}
    for acct in accounts:
        niche = acct.get("niche", "default")
        by_niche[niche] = acct
    return by_niche


def run_scraper(niches, no_headless=False, no_telegram=False):
    """Run the TikTok scraper for specified niches."""
    print(f"\n{'=' * 60}")
    print(f"  STEP 1: Scraping TikTok")
    print(f"{'=' * 60}")

    cmd = [sys.executable, "tiktok_scraper.py", "--niche"] + niches
    if no_headless:
        cmd.append("--no-headless")
    if no_telegram:
        cmd.append("--no-telegram")

    result = subprocess.run(cmd, cwd=os.path.dirname(__file__) or ".")
    return result.returncode == 0


def run_poster(accounts_by_niche, niches):
    """Run fader_reels.py for each niche that has an IG account and videos."""
    print(f"\n{'=' * 60}")
    print(f"  STEP 2: Posting to Instagram (safety-managed)")
    print(f"{'=' * 60}")

    total_uploaded = 0

    for niche in niches:
        niche_dir = os.path.join(cfg.DOWNLOAD_DIR, niche)

        if not os.path.exists(niche_dir):
            print(f"\n  [skip] No download folder for '{niche}'")
            continue

        videos = [f for f in os.listdir(niche_dir) if f.endswith('.mp4')]
        if not videos:
            print(f"\n  [skip] No videos in {niche_dir}")
            continue

        acct = accounts_by_niche.get(niche)
        if not acct:
            print(f"\n  [skip] No IG account mapped to '{niche}' in accounts.json")
            print(f"         {len(videos)} videos waiting in {niche_dir}")
            continue

        username = acct["username"]

        # Safety pre-check
        can, reason = safety.can_upload(username)
        if not can:
            print(f"\n  [safety] @{username} blocked: {reason}")
            continue

        safe_limit = safety.get_daily_limit(username)
        print(f"\n  Posting to @{username} (niche: {niche}, "
              f"{len(videos)} videos, limit: {safe_limit}/day)")

        notify(f"[Pipeline] Starting uploads for @{username} ({niche}) -- "
               f"{len(videos)} videos, limit {safe_limit}/day")

        # Run fader_reels with this account's settings
        env = os.environ.copy()
        env["IG_USERNAME"] = acct["username"]
        env["IG_PASSWORD"] = acct["password"]
        env["IG_NICHE"] = niche

        cmd = [
            sys.executable, "fader_reels.py",
            "--username", acct["username"],
            "--niche", niche,
        ]

        warmup = acct.get("warmup_intensity", "normal")
        cmd.extend(["--warmup-intensity", warmup])

        # Set video dir via environment (avoids config mutation issues)
        import config as ig_config
        original_video_dir = ig_config.VIDEO_DIR
        ig_config.VIDEO_DIR = niche_dir

        try:
            subprocess.run(cmd, cwd=os.path.dirname(__file__) or ".", env=env)
        finally:
            ig_config.VIDEO_DIR = original_video_dir

        # Count what was uploaded
        remaining = len([f for f in os.listdir(niche_dir) if f.endswith('.mp4')])
        uploaded = len(videos) - remaining
        total_uploaded += uploaded

        notify(f"[Pipeline] @{username} ({niche}) done -- {uploaded} uploaded, "
               f"{remaining} remaining")

    return total_uploaded


def show_status(accounts_by_niche, niches):
    """Show safety status for all accounts."""
    print(f"\n  {'─'*55}")
    print(f"  Account Safety Status")
    print(f"  {'─'*55}")

    for niche in niches:
        acct = accounts_by_niche.get(niche)
        if not acct:
            print(f"  {niche:15s}  (no account configured)")
            continue

        username = acct["username"]
        status = safety.get_account_status(username)
        can, reason = status["can_upload"]
        flag = "READY" if can else f"BLOCKED: {reason}"

        niche_dir = os.path.join(cfg.DOWNLOAD_DIR, niche)
        video_count = 0
        if os.path.exists(niche_dir):
            video_count = len([f for f in os.listdir(niche_dir) if f.endswith('.mp4')])

        print(f"  {niche:15s}  @{username:20s}")
        print(f"  {'':15s}  Age: {status['days_automated']}d  |  "
              f"Today: {status['uploads_today']}/{status['daily_limit']}  |  "
              f"Total: {status['total_uploads']}  |  "
              f"Videos: {video_count}")
        print(f"  {'':15s}  Status: {flag}")
        print()

    print(f"  {'─'*55}\n")


def main():
    print(BANNER)

    parser = argparse.ArgumentParser(description="TikTok -> Instagram Content Pipeline")
    parser.add_argument("--niche", nargs="+", default=None,
                        help="Specific niche(s) to process (default: all)")
    parser.add_argument("--scrape-only", action="store_true",
                        help="Only scrape + download, don't post to IG")
    parser.add_argument("--post-only", action="store_true",
                        help="Only post existing videos, don't scrape")
    parser.add_argument("--no-headless", action="store_true",
                        help="Show browser window during scraping")
    parser.add_argument("--no-telegram", action="store_true",
                        help="Skip Telegram (scrape URLs only, no download)")
    parser.add_argument("--status", action="store_true",
                        help="Show account safety status and exit")

    args = parser.parse_args()

    # Determine niches
    niches = args.niche or list(cfg.NICHES.keys())

    # Validate niches
    for n in niches:
        if n not in cfg.NICHES:
            print(f"  [error] Unknown niche: '{n}'")
            print(f"  Available: {', '.join(cfg.NICHES.keys())}")
            sys.exit(1)

    accounts = load_accounts()

    # Status mode
    if args.status:
        show_status(accounts, niches)
        sys.exit(0)

    print(f"  Niches:      {', '.join(niches)}")
    print(f"  IG accounts: {len(accounts)} loaded")
    print(f"  Mode:        {'scrape only' if args.scrape_only else 'post only' if args.post_only else 'full pipeline'}")
    print(f"  Time:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Show niche -> account mapping with safety info
    print(f"\n  Niche -> Account mapping:")
    for niche in niches:
        acct = accounts.get(niche)
        niche_dir = os.path.join(cfg.DOWNLOAD_DIR, niche)
        video_count = 0
        if os.path.exists(niche_dir):
            video_count = len([f for f in os.listdir(niche_dir) if f.endswith('.mp4')])

        if acct:
            username = acct["username"]
            status = safety.get_account_status(username)
            limit = status["daily_limit"]
            today = status["uploads_today"]
            ig_name = f"@{username} ({today}/{limit} today)"
        else:
            ig_name = "[not configured]"

        print(f"    {niche:15s} -> {ig_name:35s} ({video_count} videos ready)")

    notify(f"[Pipeline] Starting -- niches: {', '.join(niches)}")

    # Step 1: Scrape
    if not args.post_only:
        run_scraper(niches, no_headless=args.no_headless,
                    no_telegram=args.no_telegram)

    # Step 2: Post
    if not args.scrape_only:
        if not accounts:
            print(f"\n  [warn] No accounts.json found!")
            print(f"  Create one -- see accounts.example.json for the format.")
            print(f"  Videos are downloaded and ready in {cfg.DOWNLOAD_DIR}/")
        else:
            total = run_poster(accounts, niches)
            notify(f"[Pipeline] Complete -- {total} total uploads across all niches")

    print(f"\n{'=' * 60}")
    print(f"  Pipeline complete!")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
