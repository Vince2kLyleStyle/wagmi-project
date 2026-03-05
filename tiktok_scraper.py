#!/usr/bin/env python3
"""
TikTok Scraper — CLI Entry Point
Scrapes trending TikTok videos by niche/keyword, downloads via Telegram bot,
and saves to niche-specific folders for Instagram posting.

Usage:
    py tiktok_scraper.py --niche trading              # scrape trading niche
    py tiktok_scraper.py --niche trading gambling      # scrape multiple niches
    py tiktok_scraper.py -k "custom keyword"           # custom keywords
    py tiktok_scraper.py --niches                      # list available niches
"""

import argparse
import os
import sys
from datetime import datetime

import scraper_config as cfg
from tiktok_discover import scrape_tiktok, login_to_tiktok
from telegram_sender import send_urls_sync, send_and_download_sync, telegram_login_sync

BANNER = """
╔══════════════════════════════════════════════════════╗
║       TikTok Scraper — Find Viral Content            ║
║       Scrape → Download → Instagram Pipeline         ║
╚══════════════════════════════════════════════════════╝
"""


def load_existing_urls(filepath):
    """Load previously scraped URLs to avoid duplicates."""
    if not os.path.exists(filepath):
        return set()
    urls = set()
    with open(filepath, "r") as f:
        for line in f:
            parts = line.strip().split(" | ")
            if len(parts) >= 4:
                urls.add(parts[-1])
    return urls


def save_urls(results, filepath):
    """Append new results to the output file."""
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "a") as f:
        for r in results:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            views_str = f"{r['views']:,}" if r["views"] else "unknown"
            f.write(f"{timestamp} | {r['keyword']} | {views_str} views | {r['url']}\n")


def run_niche(niche_name, keywords, args, existing_urls):
    """Scrape + download for a single niche. Returns count of new videos."""
    download_dir = os.path.join(cfg.DOWNLOAD_DIR, niche_name)

    print(f"\n{'═' * 54}")
    print(f"  NICHE: {niche_name}")
    print(f"  Keywords: {', '.join(keywords)}")
    print(f"  Download: {download_dir}")
    print(f"{'═' * 54}")

    results = scrape_tiktok(
        keywords=keywords,
        max_per_keyword=args.max,
        min_views=args.min_views,
        min_likes=args.min_likes,
        scroll_count=args.scrolls,
        headless=not args.no_headless,
    )

    if not results:
        print(f"\n  ⚠  No videos found for '{niche_name}'")
        return 0

    new_results = [r for r in results if r["url"] not in existing_urls]
    # Add to existing set so cross-niche dedup works
    for r in new_results:
        existing_urls.add(r["url"])

    print(f"\n  📊  {niche_name}: {len(results)} found, {len(new_results)} new")

    if not new_results:
        print(f"  All videos already scraped for '{niche_name}'.")
        return 0

    save_urls(new_results, args.output)

    # Print results
    for r in new_results[:10]:  # Show first 10
        views = f"{r['views']:>10,}" if r["views"] else "   unknown"
        print(f"  {views} views | {r['url']}")
    if len(new_results) > 10:
        print(f"  ... and {len(new_results) - 10} more")

    # Download via Telegram
    if args.no_telegram:
        pass
    else:
        urls = [r["url"] for r in new_results]
        if args.no_download:
            sent, failed = send_urls_sync(urls)
            print(f"  📱  Sent {sent}, failed {failed}")
        else:
            sent, downloaded, failed = send_and_download_sync(
                urls, download_dir=download_dir
            )
            print(f"  📱  Sent {sent}, downloaded {downloaded}, failed {failed}")
            if downloaded > 0:
                print(f"  📂  Saved to: {download_dir}")

    return len(new_results)


def main():
    print(BANNER)

    parser = argparse.ArgumentParser(description="Scrape viral TikTok videos by niche")
    parser.add_argument(
        "--login", action="store_true",
        help="Open browser to log into TikTok (one-time setup)"
    )
    parser.add_argument(
        "--telegram-login", action="store_true",
        help="Log into Telegram (one-time setup)"
    )
    parser.add_argument(
        "--niches", action="store_true",
        help="List all available niches and their keywords"
    )
    parser.add_argument(
        "--niche", nargs="+", default=None,
        help="Niche(s) to scrape (e.g. --niche trading gambling)"
    )
    parser.add_argument(
        "-k", "--keywords", nargs="+", default=None,
        help="Custom keywords (downloads to tiktok_videos/custom/)"
    )
    parser.add_argument(
        "--max", type=int, default=cfg.MAX_VIDEOS_PER_KEYWORD,
        help=f"Max videos per keyword (default: {cfg.MAX_VIDEOS_PER_KEYWORD})"
    )
    parser.add_argument(
        "--min-views", type=int, default=cfg.MIN_VIEWS,
        help=f"Minimum view count filter (default: {cfg.MIN_VIEWS:,})"
    )
    parser.add_argument(
        "--min-likes", type=int, default=cfg.MIN_LIKES,
        help=f"Minimum like count filter (default: {cfg.MIN_LIKES:,})"
    )
    parser.add_argument(
        "--scrolls", type=int, default=cfg.SCROLL_COUNT,
        help=f"Scroll count (default: {cfg.SCROLL_COUNT})"
    )
    parser.add_argument(
        "--no-telegram", action="store_true",
        help="Skip sending URLs to Telegram bot"
    )
    parser.add_argument(
        "--no-download", action="store_true",
        help="Send URLs to bot but don't auto-download"
    )
    parser.add_argument(
        "--no-headless", action="store_true",
        help="Show browser window"
    )
    parser.add_argument(
        "-o", "--output", default=cfg.OUTPUT_FILE,
        help=f"URL log file (default: {cfg.OUTPUT_FILE})"
    )

    args = parser.parse_args()

    # ─── Login modes ─────────────────────────────────────────────
    if args.login:
        login_to_tiktok()
        print("   You can now run:  py tiktok_scraper.py --niche trading")
        sys.exit(0)

    if args.telegram_login:
        telegram_login_sync()
        sys.exit(0)

    # ─── List niches ─────────────────────────────────────────────
    if args.niches:
        print("  Available niches:\n")
        for name, kws in cfg.NICHES.items():
            print(f"    {name:15s} → {', '.join(kws[:5])}{'...' if len(kws) > 5 else ''}")
        print(f"\n  Usage:  py tiktok_scraper.py --niche {list(cfg.NICHES.keys())[0]}")
        print(f"  All:    py tiktok_scraper.py --niche {' '.join(cfg.NICHES.keys())}")
        sys.exit(0)

    # ─── Determine what to scrape ────────────────────────────────
    # Build list of (niche_name, keywords) pairs
    scrape_jobs = []

    if args.niche:
        for niche_name in args.niche:
            if niche_name not in cfg.NICHES:
                print(f"  ❌  Unknown niche: '{niche_name}'")
                print(f"  Available: {', '.join(cfg.NICHES.keys())}")
                print(f"  Or use -k for custom keywords.")
                sys.exit(1)
            scrape_jobs.append((niche_name, cfg.NICHES[niche_name]))
    elif args.keywords:
        scrape_jobs.append(("custom", args.keywords))
    else:
        # Default: scrape ALL niches
        for name, kws in cfg.NICHES.items():
            scrape_jobs.append((name, kws))

    # ─── Summary ─────────────────────────────────────────────────
    niche_names = [j[0] for j in scrape_jobs]
    total_keywords = sum(len(j[1]) for j in scrape_jobs)
    print(f"  Niches:       {', '.join(niche_names)}")
    print(f"  Keywords:     {total_keywords} total")
    print(f"  Max/keyword:  {args.max}")
    print(f"  Headless:     {not args.no_headless}")
    print(f"  Telegram:     {'OFF' if args.no_telegram else 'ON → @' + cfg.TELEGRAM_BOT_USERNAME}")
    print(f"  Download to:  {cfg.DOWNLOAD_DIR}/<niche>/")
    print()

    # ─── Run each niche ──────────────────────────────────────────
    existing = load_existing_urls(args.output)
    total_new = 0

    for niche_name, keywords in scrape_jobs:
        count = run_niche(niche_name, keywords, args, existing)
        total_new += count

    # ─── Done ────────────────────────────────────────────────────
    print(f"\n{'═' * 54}")
    print(f"  ALL DONE! {total_new} new videos collected.")
    if total_new > 0:
        print(f"  Videos organized by niche in: {cfg.DOWNLOAD_DIR}/")
        for name, _ in scrape_jobs:
            niche_dir = os.path.join(cfg.DOWNLOAD_DIR, name)
            if os.path.exists(niche_dir):
                count = len([f for f in os.listdir(niche_dir) if f.endswith('.mp4')])
                print(f"    {name:15s} → {count} videos")
    print(f"{'═' * 54}\n")


if __name__ == "__main__":
    main()
