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


def load_completed_keywords(niche_name):
    """Load set of already-completed keywords for a niche (for resume support)."""
    path = os.path.join(os.path.dirname(cfg.OUTPUT_FILE) or ".", f"{niche_name}_progress.txt")
    if not os.path.exists(path):
        return set(), path
    with open(path) as f:
        return {line.strip() for line in f if line.strip()}, path


def mark_keyword_done(progress_path, keyword):
    """Append a completed keyword to the progress file."""
    with open(progress_path, "a") as f:
        f.write(keyword + "\n")


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
            likes_str = f"{r.get('likes', 0):,}" if r.get("likes") else "0"
            ratio = f"{r['likes']/r['views']*100:.1f}%" if r.get("views") and r.get("likes") else "n/a"
            f.write(f"{timestamp} | {r['keyword']} | {views_str} views | {likes_str} likes | {ratio} eng | {r['url']}\n")


def run_niche(niche_name, keywords, args, existing_urls):
    """Scrape + download for a single niche. Returns count of new videos."""
    download_dir = os.path.join(cfg.DOWNLOAD_DIR, niche_name)

    # Resume support — skip already-completed keywords
    completed, progress_path = load_completed_keywords(niche_name)
    remaining = [k for k in keywords if k not in completed]
    if completed:
        print(f"\n  ⏭  Resuming — skipping {len(completed)} already-done keywords, {len(remaining)} remaining")
    if not remaining:
        print(f"  ✅  All keywords already scraped for '{niche_name}'. Delete {niche_name}_progress.txt to re-scrape.")
        return 0

    print(f"\n{'═' * 54}")
    print(f"  NICHE: {niche_name}")
    print(f"  Keywords: {', '.join(remaining)}")
    print(f"  Download: {download_dir}")
    print(f"{'═' * 54}")

    total_new = [0]  # use list for mutation inside closure

    def on_keyword_done(keyword, results):
        new_results = [r for r in results if r["url"] not in existing_urls]
        for r in new_results:
            existing_urls.add(r["url"])

        mark_keyword_done(progress_path, keyword)

        if not new_results:
            return

        save_urls(new_results, args.output)
        total_new[0] += len(new_results)

        for r in new_results[:5]:
            views = f"{r['views']:>10,}" if r["views"] else "   unknown"
            ratio = f"{r['likes']/r['views']*100:.1f}%" if r.get("views") and r.get("likes") else "  n/a"
            print(f"  {views} views | {ratio:>5} eng | {r['url']}")
        if len(new_results) > 5:
            print(f"  ... and {len(new_results) - 5} more")

        if args.no_telegram:
            return
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

    scrape_tiktok(
        keywords=remaining,
        max_per_keyword=args.max,
        min_views=args.min_views,
        min_likes=args.min_likes,
        scroll_count=args.scrolls,
        headless=not args.no_headless,
        min_engagement_ratio=args.min_engagement,
        on_keyword_done=on_keyword_done,
    )

    return total_new[0]


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
        "--min-engagement", type=float, default=cfg.MIN_ENGAGEMENT_RATIO,
        help=f"Min likes/views ratio (default: {cfg.MIN_ENGAGEMENT_RATIO})"
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
