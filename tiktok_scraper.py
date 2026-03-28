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
from tiktok_discover import scrape_tiktok, login_to_tiktok, scrape_tiktok_by_caption, scrape_accounts_from_captions, scrape_account, set_active_niche
from telegram_sender import send_urls_sync, send_and_download_sync, telegram_login_sync
from telegram_pull import pull_videos_sync

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
            likes_str = f"{r.get('likes', 0):,}" if r.get("likes") else "0"
            ratio = f"{r['likes']/r['views']*100:.1f}%" if r.get("views") and r.get("likes") else "n/a"
            f.write(f"{timestamp} | {r['keyword']} | {views_str} views | {likes_str} likes | {ratio} eng | {r['url']}\n")


def run_niche(niche_name, keywords, args, existing_urls):
    """Scrape + download for a single niche. One browser, saves after EACH keyword."""
    set_active_niche(niche_name)
    download_dir = os.path.join(cfg.DOWNLOAD_DIR, niche_name)

    print(f"\n{'═' * 54}")
    print(f"  NICHE: {niche_name}")
    print(f"  Keywords: {', '.join(keywords)}")
    print(f"  Download: {download_dir}")
    print(f"{'═' * 54}")

    total_new = 0

    def on_keyword_done(keyword, new_results):
        """Called after each keyword — save URLs and optionally download."""
        nonlocal total_new

        # Filter out already-scraped URLs
        fresh = [r for r in new_results if r["url"] not in existing_urls]
        for r in fresh:
            existing_urls.add(r["url"])

        if not fresh:
            return

        # Save immediately
        save_urls(fresh, args.output)
        total_new += len(fresh)

        # Show top results
        for r in fresh[:5]:
            views = f"{r['views']:>10,}" if r["views"] else "   unknown"
            ratio = f"{r['likes']/r['views']*100:.1f}%" if r.get("views") and r.get("likes") else "  n/a"
            print(f"    {views} views | {ratio:>5} eng | {r['url']}")
        if len(fresh) > 5:
            print(f"    ... and {len(fresh) - 5} more")

        # Download if Telegram is enabled
        if not args.no_telegram:
            urls = [r["url"] for r in fresh]
            if args.no_download:
                sent, failed = send_urls_sync(urls)
                print(f"  📱  Sent {sent}, failed {failed}")
            else:
                sent, downloaded, failed = send_and_download_sync(
                    urls, download_dir=download_dir
                )
                print(f"  📱  Sent {sent}, downloaded {downloaded}, failed {failed}")

        print(f"  ✅  Running total: {total_new} new videos saved")

    # One browser session for ALL keywords — callback saves after each
    scrape_tiktok(
        keywords=keywords,
        max_per_keyword=args.max,
        min_views=args.min_views,
        min_likes=args.min_likes,
        scroll_count=args.scrolls,
        headless=not args.no_headless,
        min_engagement_ratio=args.min_engagement,
        min_interactions=args.min_interactions,
        on_keyword_done=on_keyword_done,
    )

    print(f"\n  📊  {niche_name}: {total_new} total new videos")
    return total_new


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
        "--min-interactions", type=int, default=cfg.MIN_INTERACTIONS,
        help=f"Min total interactions: likes+comments+shares (default: {cfg.MIN_INTERACTIONS:,})"
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
        "--caption-search", action="store_true",
        help="Search for videos using the viral caption instead of keywords"
    )
    parser.add_argument(
        "--caption", type=str, default=None,
        help="Custom viral caption to search for (default: uses config)"
    )
    parser.add_argument(
        "--account", type=str, nargs="+", default=None,
        help="Scrape account(s) for videos + harvest captions (e.g. --account @flopolos)"
    )
    parser.add_argument(
        "--bulk", action="store_true",
        help="Bulk mode: search multiple captions → find accounts → scrape their profiles"
    )
    parser.add_argument(
        "--skip-profiles", action="store_true",
        help="In bulk mode, skip Phase 2 (account scraping) and just keep caption-matched videos"
    )
    parser.add_argument(
        "--pull-chat", type=str, default=None,
        help='Pull videos from a Telegram chat (e.g. --pull-chat "Friend Name")'
    )
    parser.add_argument(
        "--pull-limit", type=int, default=200,
        help="Max messages to scan in the chat (default: 200)"
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

    # ─── Pull from Telegram chat ──────────────────────────────────
    if args.pull_chat:
        niche_name = args.niche[0] if args.niche else "memes"
        download_dir = os.path.join(cfg.DOWNLOAD_DIR, niche_name)
        print(f"  Mode:         TELEGRAM PULL")
        print(f"  Chat:         \"{args.pull_chat}\"")
        print(f"  Scan limit:   {args.pull_limit} messages")
        print(f"  Download to:  {download_dir}")
        print()
        count = pull_videos_sync(args.pull_chat, download_dir, limit=args.pull_limit)
        print(f"\n{'═' * 54}")
        print(f"  DONE! {count} videos pulled from Telegram.")
        print(f"{'═' * 54}\n")
        sys.exit(0)

    # ─── Account scrape mode ──────────────────────────────────────
    if args.account:
        niche_name = args.niche[0] if args.niche else "memes"
        set_active_niche(niche_name)
        download_dir = os.path.join(cfg.DOWNLOAD_DIR, niche_name)

        print(f"  Mode:         ACCOUNT SCRAPE")
        print(f"  Accounts:     {', '.join(args.account)}")
        print(f"  Niche:        {niche_name}")
        print(f"  Download to:  {download_dir}")
        print()

        existing = load_existing_urls(args.output)
        all_new = []
        all_captions = []

        for acct in args.account:
            videos, captions = scrape_account(
                username=acct,
                max_videos=args.max,
                scroll_count=args.scrolls,
                headless=not args.no_headless,
                min_views=args.min_views,
            )
            new_vids = [v for v in videos if v["url"] not in existing]
            for v in new_vids:
                existing.add(v["url"])
            all_new.extend(new_vids)
            all_captions.extend(captions)

        print(f"\n  📊  {len(all_new)} new videos from {len(args.account)} account(s)")

        if all_new:
            save_urls(all_new, args.output)

            for r in all_new[:15]:
                views = f"{r['views']:>10,}" if r["views"] else "   unknown"
                cap = r.get("caption", "")[:40]
                print(f"  {views} views | {cap}...")
            if len(all_new) > 15:
                print(f"  ... and {len(all_new) - 15} more")

            if not args.no_telegram:
                urls = [r["url"] for r in all_new]
                if args.no_download:
                    sent, failed = send_urls_sync(urls)
                    print(f"\n  📱  Sent {sent}, failed {failed}")
                else:
                    sent, downloaded, failed = send_and_download_sync(
                        urls, download_dir=download_dir
                    )
                    print(f"\n  📱  Sent {sent}, downloaded {downloaded}, failed {failed}")

        # Save harvested captions
        if all_captions:
            captions_file = os.path.join(os.path.dirname(__file__), "harvested_captions.txt")
            with open(captions_file, "a", encoding="utf-8") as f:
                for cap in all_captions:
                    f.write(cap.replace("\n", " ").strip() + "\n")
            print(f"\n  📝  {len(all_captions)} captions saved to harvested_captions.txt")
            print(f"      Copy the best ones into VIRAL_CAPTIONS in scraper_config.py")
            print(f"      Then run:  py tiktok_scraper.py --bulk --niche {niche_name}")

        print(f"\n{'═' * 54}")
        print(f"  DONE! {len(all_new)} videos from account scrape.")
        print(f"{'═' * 54}\n")
        sys.exit(0)

    # ─── List niches ─────────────────────────────────────────────
    if args.niches:
        print("  Available niches:\n")
        for name, kws in cfg.NICHES.items():
            print(f"    {name:15s} → {', '.join(kws[:5])}{'...' if len(kws) > 5 else ''}")
        print(f"\n  Usage:  py tiktok_scraper.py --niche {list(cfg.NICHES.keys())[0]}")
        print(f"  All:    py tiktok_scraper.py --niche {' '.join(cfg.NICHES.keys())}")
        sys.exit(0)

    # ─── Bulk mode: multi-caption → account discovery → profile scrape ─
    if args.bulk:
        captions = cfg.VIRAL_CAPTIONS
        if not captions:
            print("  ❌  No captions configured in VIRAL_CAPTIONS.")
            print("  Add captions to scraper_config.py VIRAL_CAPTIONS list.")
            sys.exit(1)

        niche_name = args.niche[0] if args.niche else "memes"
        set_active_niche(niche_name)
        download_dir = os.path.join(cfg.DOWNLOAD_DIR, niche_name)

        print(f"  Mode:         BULK (caption → account → profile scrape)")
        print(f"  Captions:     {len(captions)}")
        print(f"  Max/account:  {cfg.MAX_VIDEOS_PER_ACCOUNT}")
        print(f"  Niche:        {niche_name}")
        print(f"  Download to:  {download_dir}")
        print()

        existing = load_existing_urls(args.output)
        results = scrape_accounts_from_captions(
            captions_list=captions,
            max_account_videos=cfg.MAX_VIDEOS_PER_ACCOUNT,
            scroll_count=args.scrolls,
            headless=not args.no_headless,
            min_views=args.min_views,
            match_threshold=cfg.CAPTION_MATCH_THRESHOLD,
            skip_profiles=args.skip_profiles,
            min_interactions=args.min_interactions,
        )

        new_results = [r for r in results if r["url"] not in existing]
        print(f"\n  📊  {len(results)} total, {len(new_results)} new")

        if new_results:
            save_urls(new_results, args.output)

            # Show by account
            by_author = {}
            for r in new_results:
                auth = r.get("author", "unknown")
                by_author.setdefault(auth, []).append(r)

            for auth, vids in by_author.items():
                total_views = sum(v["views"] for v in vids if v["views"])
                print(f"    @{auth:20s} → {len(vids):3d} videos | {total_views:>12,} total views")

            if not args.no_telegram:
                urls = [r["url"] for r in new_results]
                if args.no_download:
                    sent, failed = send_urls_sync(urls)
                    print(f"\n  📱  Sent {sent}, failed {failed}")
                else:
                    sent, downloaded, failed = send_and_download_sync(
                        urls, download_dir=download_dir
                    )
                    print(f"\n  📱  Sent {sent}, downloaded {downloaded}, failed {failed}")

        print(f"\n{'═' * 54}")
        print(f"  DONE! {len(new_results)} new videos from {len(captions)} captions.")
        print(f"{'═' * 54}\n")
        sys.exit(0)

    # ─── Caption search mode ─────────────────────────────────────
    if args.caption_search:
        caption = args.caption or cfg.VIRAL_CAPTION_SEARCH
        if not caption:
            print("  ❌  No viral caption configured.")
            print("  Set VIRAL_CAPTION_SEARCH in scraper_config.py or use --caption \"...\"")
            sys.exit(1)

        niche_name = args.niche[0] if args.niche else "memes"
        set_active_niche(niche_name)
        download_dir = os.path.join(cfg.DOWNLOAD_DIR, niche_name)

        print(f"  Mode:         CAPTION SEARCH")
        print(f"  Caption:      \"{caption[:60]}...\"")
        print(f"  Niche:        {niche_name}")
        print(f"  Download to:  {download_dir}")
        print()

        existing = load_existing_urls(args.output)
        results = scrape_tiktok_by_caption(
            viral_caption=caption,
            max_videos=args.max,
            scroll_count=args.scrolls,
            headless=not args.no_headless,
            min_views=args.min_views,
            match_threshold=cfg.CAPTION_MATCH_THRESHOLD,
        )

        new_results = [r for r in results if r["url"] not in existing]
        print(f"\n  📊  {len(results)} matched, {len(new_results)} new")

        if new_results:
            save_urls(new_results, args.output)
            for r in new_results[:10]:
                views = f"{r['views']:>10,}" if r["views"] else "   unknown"
                cap_preview = r.get("caption", "")[:40]
                print(f"  {views} views | {cap_preview}...")
            if len(new_results) > 10:
                print(f"  ... and {len(new_results) - 10} more")

            if not args.no_telegram:
                urls = [r["url"] for r in new_results]
                if args.no_download:
                    sent, failed = send_urls_sync(urls)
                    print(f"  📱  Sent {sent}, failed {failed}")
                else:
                    sent, downloaded, failed = send_and_download_sync(
                        urls, download_dir=download_dir
                    )
                    print(f"  📱  Sent {sent}, downloaded {downloaded}, failed {failed}")

        print(f"\n{'═' * 54}")
        print(f"  DONE! {len(new_results)} new videos from caption search.")
        print(f"{'═' * 54}\n")
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
