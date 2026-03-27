#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║          CONTENT PIPELINE — TikTok → Instagram                ║
║   Scrape trending content → Download → Post to IG accounts   ║
╚═══════════════════════════════════════════════════════════════╝

Workflow:
    1. Scrapes TikTok for each niche (trading, gambling, hustle, etc.)
    2. Downloads videos via Telegram bot into niche folders
    3. Posts videos to the matching Instagram account via Fader v2

Setup:
    1. py tiktok_scraper.py --login         (log into TikTok once)
    2. py tiktok_scraper.py --telegram-login (log into Telegram once)
    3. Create accounts.json (see accounts.example.json)
    4. py pipeline.py                        (run the full pipeline)

Usage:
    py pipeline.py                           # scrape all niches + post
    py pipeline.py --scrape-only             # just scrape, don't post
    py pipeline.py --post-only               # just post existing videos
    py pipeline.py --niche trading           # only one niche
    py pipeline.py --no-headless             # show browser for debugging
"""

import argparse
import json
import os
import sys
import subprocess
from datetime import datetime

import scraper_config as cfg

BANNER = r"""
╔═══════════════════════════════════════════════════════════════╗
║          CONTENT PIPELINE — TikTok → Instagram                ║
║       Spot a trend → Scrape → Download → Post automatically  ║
╚═══════════════════════════════════════════════════════════════╝
"""

ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), "accounts.json")


def load_accounts():
    """Load IG accounts from accounts.json."""
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    with open(ACCOUNTS_FILE, "r") as f:
        accounts = json.load(f)
    # Index by niche for easy lookup
    by_niche = {}
    for acct in accounts:
        niche = acct.get("niche", "default")
        by_niche[niche] = acct
    return by_niche


def run_scraper(niches, no_headless=False, no_telegram=False):
    """Run the TikTok scraper for specified niches."""
    print(f"\n{'═' * 60}")
    print(f"  STEP 1: Scraping TikTok")
    print(f"{'═' * 60}")

    cmd = [sys.executable, "tiktok_scraper.py", "--niche"] + niches
    if no_headless:
        cmd.append("--no-headless")
    if no_telegram:
        cmd.append("--no-telegram")

    result = subprocess.run(cmd, cwd=os.path.dirname(__file__) or ".")
    return result.returncode == 0


def run_nsfw_filter(niches, dry_run=False):
    """Run NSFW filter on all niche video folders."""
    print(f"\n{'═' * 60}")
    print(f"  STEP 1.5: NSFW Content Filter")
    print(f"{'═' * 60}")

    cmd = [sys.executable, "nsfw_filter.py", "--all-niches"]
    if dry_run:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, cwd=os.path.dirname(__file__) or ".")
    return result.returncode == 0


def run_poster(accounts_by_niche, niches):
    """Run fader_reels.py for each niche that has an IG account and videos."""
    print(f"\n{'═' * 60}")
    print(f"  STEP 2: Posting to Instagram")
    print(f"{'═' * 60}")

    for niche in niches:
        niche_dir = os.path.join(cfg.DOWNLOAD_DIR, niche)

        # Check if there are videos to post
        if not os.path.exists(niche_dir):
            print(f"\n  ⚠  No download folder for '{niche}' — skipping")
            continue

        videos = [f for f in os.listdir(niche_dir) if f.endswith('.mp4')]
        if not videos:
            print(f"\n  ⚠  No videos in {niche_dir} — skipping")
            continue

        # Check if we have an IG account for this niche
        acct = accounts_by_niche.get(niche)
        if not acct:
            print(f"\n  ⚠  No IG account mapped to '{niche}' in accounts.json")
            print(f"      {len(videos)} videos waiting in {niche_dir}")
            continue

        username = acct["username"]
        print(f"\n  📱  Posting {len(videos)} videos to @{username} (niche: {niche})")

        # Run fader_reels with this account's settings
        env = os.environ.copy()
        env["IG_USERNAME"] = acct["username"]
        env["IG_PASSWORD"] = acct["password"]

        cmd = [
            sys.executable, "fader_reels.py",
            "--username", acct["username"],
        ]

        # Override video_dir via config (temporary)
        import config as ig_config
        original_video_dir = ig_config.VIDEO_DIR
        ig_config.VIDEO_DIR = niche_dir

        try:
            subprocess.run(cmd, cwd=os.path.dirname(__file__) or ".",
                         env=env)
        finally:
            ig_config.VIDEO_DIR = original_video_dir


def main():
    print(BANNER)

    parser = argparse.ArgumentParser(description="TikTok → Instagram Content Pipeline")
    parser.add_argument(
        "--niche", nargs="+", default=None,
        help="Specific niche(s) to process (default: all)"
    )
    parser.add_argument("--scrape-only", action="store_true",
                       help="Only scrape + download, don't post to IG")
    parser.add_argument("--post-only", action="store_true",
                       help="Only post existing videos, don't scrape")
    parser.add_argument("--no-headless", action="store_true",
                       help="Show browser window during scraping")
    parser.add_argument("--no-telegram", action="store_true",
                       help="Skip Telegram (scrape URLs only, no download)")
    parser.add_argument("--skip-nsfw-filter", action="store_true",
                       help="Skip NSFW content filter")
    parser.add_argument("--nsfw-dry-run", action="store_true",
                       help="Preview NSFW filter results without quarantining")

    args = parser.parse_args()

    # Determine niches
    niches = args.niche or list(cfg.NICHES.keys())

    # Validate niches
    for n in niches:
        if n not in cfg.NICHES:
            print(f"  ❌  Unknown niche: '{n}'")
            print(f"  Available: {', '.join(cfg.NICHES.keys())}")
            sys.exit(1)

    accounts = load_accounts()

    print(f"  Niches:     {', '.join(niches)}")
    print(f"  IG accounts: {len(accounts)} loaded")
    print(f"  Mode:       {'scrape only' if args.scrape_only else 'post only' if args.post_only else 'full pipeline'}")
    print(f"  Time:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Show niche → account mapping
    print(f"\n  Niche → Account mapping:")
    for niche in niches:
        acct = accounts.get(niche)
        niche_dir = os.path.join(cfg.DOWNLOAD_DIR, niche)
        video_count = 0
        if os.path.exists(niche_dir):
            video_count = len([f for f in os.listdir(niche_dir) if f.endswith('.mp4')])
        ig_name = f"@{acct['username']}" if acct else "⚠ not configured"
        print(f"    {niche:15s} → {ig_name:25s} ({video_count} videos ready)")

    # Step 1: Scrape
    if not args.post_only:
        run_scraper(niches, no_headless=args.no_headless,
                   no_telegram=args.no_telegram)

    # Step 1.5: NSFW Filter
    if not args.post_only and not getattr(args, 'skip_nsfw_filter', False):
        run_nsfw_filter(niches, dry_run=getattr(args, 'nsfw_dry_run', False))

    # Step 2: Post
    if not args.scrape_only:
        if not accounts:
            print(f"\n  ⚠  No accounts.json found!")
            print(f"  Create one — see accounts.example.json for the format.")
            print(f"  Videos are downloaded and ready in {cfg.DOWNLOAD_DIR}/")
        else:
            run_poster(accounts, niches)

    print(f"\n{'═' * 60}")
    print(f"  Pipeline complete!")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
