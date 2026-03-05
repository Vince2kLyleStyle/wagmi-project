#!/usr/bin/env python3
"""
TikTok Scraper — CLI Entry Point
Scrapes trending TikTok videos by keyword and sends URLs to a Telegram download bot.

Usage:
    python tiktok_scraper.py -k gym motivation --max 15
    python tiktok_scraper.py -k cooking --min-views 500000 --no-telegram
    python tiktok_scraper.py -k dance --no-headless   # show browser for debugging
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
║       Scrape → Filter → Send to Telegram             ║
╚══════════════════════════════════════════════════════╝
"""


def load_existing_urls(filepath):
    """Load previously scraped URLs to avoid duplicates."""
    if not os.path.exists(filepath):
        return set()
    urls = set()
    with open(filepath, "r") as f:
        for line in f:
            # Format: "timestamp | keyword | views | url"
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


def main():
    print(BANNER)

    parser = argparse.ArgumentParser(description="Scrape viral TikTok videos by keyword")
    parser.add_argument(
        "--login", action="store_true",
        help="Open browser to log into TikTok (one-time setup, saves session)"
    )
    parser.add_argument(
        "--telegram-login", action="store_true",
        help="Log into Telegram (one-time setup, saves session for sending URLs)"
    )
    parser.add_argument(
        "-k", "--keywords", nargs="+", default=cfg.KEYWORDS,
        help="Keywords to search (default: from config)"
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
        help=f"Scroll count for loading more results (default: {cfg.SCROLL_COUNT})"
    )
    parser.add_argument(
        "--no-telegram", action="store_true",
        help="Skip sending URLs to Telegram bot"
    )
    parser.add_argument(
        "--no-download", action="store_true",
        help="Send URLs to bot but don't auto-download videos"
    )
    parser.add_argument(
        "--download-dir", default=cfg.DOWNLOAD_DIR,
        help=f"Folder to save downloaded videos (default: {cfg.DOWNLOAD_DIR})"
    )
    parser.add_argument(
        "--no-headless", action="store_true",
        help="Show browser window (useful for debugging/CAPTCHAs)"
    )
    parser.add_argument(
        "-o", "--output", default=cfg.OUTPUT_FILE,
        help=f"Output file path (default: {cfg.OUTPUT_FILE})"
    )

    args = parser.parse_args()

    # ─── Login modes ─────────────────────────────────────────────
    if args.login:
        login_to_tiktok()
        print("   You can now run the scraper:  py tiktok_scraper.py -k trading")
        sys.exit(0)

    if args.telegram_login:
        telegram_login_sync()
        sys.exit(0)

    # ─── Summary ──────────────────────────────────────────────────
    print(f"  Keywords:     {', '.join(args.keywords)}")
    print(f"  Max/keyword:  {args.max}")
    print(f"  Min views:    {args.min_views:,}")
    print(f"  Headless:     {not args.no_headless}")
    print(f"  Telegram:     {'OFF' if args.no_telegram else 'ON → @' + cfg.TELEGRAM_BOT_USERNAME}")
    print(f"  Output:       {args.output}")
    print()

    # ─── Scrape ───────────────────────────────────────────────────
    print("═" * 54)
    print("  PHASE 1: Scraping TikTok")
    print("═" * 54)

    results = scrape_tiktok(
        keywords=args.keywords,
        max_per_keyword=args.max,
        min_views=args.min_views,
        min_likes=args.min_likes,
        scroll_count=args.scrolls,
        headless=not args.no_headless,
    )

    if not results:
        print("\n⚠  No videos found. Try different keywords or lower the view filter.")
        sys.exit(0)

    # ─── Deduplicate ──────────────────────────────────────────────
    existing = load_existing_urls(args.output)
    new_results = [r for r in results if r["url"] not in existing]

    print(f"\n📊  Results: {len(results)} total, {len(new_results)} new")

    if not new_results:
        print("   All videos already scraped. Nothing new to send.")
        sys.exit(0)

    # ─── Save ─────────────────────────────────────────────────────
    save_urls(new_results, args.output)
    print(f"💾  Saved {len(new_results)} URLs to {args.output}")

    # ─── Print results ────────────────────────────────────────────
    print(f"\n{'─' * 54}")
    for r in new_results:
        views = f"{r['views']:>10,}" if r["views"] else "   unknown"
        print(f"  {views} views | {r['url']}")
    print(f"{'─' * 54}")

    # ─── Telegram ─────────────────────────────────────────────────
    if args.no_telegram:
        print("\n📱  Telegram: SKIPPED (--no-telegram)")
    else:
        print(f"\n{'═' * 54}")
        if args.no_download:
            print("  PHASE 2: Sending to Telegram Bot")
        else:
            print("  PHASE 2: Sending to Telegram Bot + Auto-Download")
        print("═" * 54)

        urls = [r["url"] for r in new_results]

        if args.no_download:
            sent, failed = send_urls_sync(urls)
            print(f"\n📱  Telegram: {sent} sent, {failed} failed")
        else:
            sent, downloaded, failed = send_and_download_sync(
                urls, download_dir=args.download_dir
            )
            print(f"\n📱  Telegram: {sent} sent, {downloaded} downloaded, {failed} failed")
            if downloaded > 0:
                print(f"📂  Videos saved to: {args.download_dir}")

    # ─── Done ─────────────────────────────────────────────────────
    print(f"\n✅  Done! {len(new_results)} videos collected.")
    if not args.no_telegram and not args.no_download:
        print(f"   Videos are in: {args.download_dir}")
    elif not args.no_telegram:
        print(f"   Check @{cfg.TELEGRAM_BOT_USERNAME} in Telegram for download links.")
    print()


if __name__ == "__main__":
    main()
