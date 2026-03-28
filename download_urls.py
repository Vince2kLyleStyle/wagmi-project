#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║          DOWNLOAD — Batch download from scraped_urls.txt      ║
║          Reads URLs, sends to Telegram bot, saves videos      ║
╚═══════════════════════════════════════════════════════════════╝

Usage:
    python download_urls.py                          # download all undownloaded URLs
    python download_urls.py --dir tiktok_videos/motion
    python download_urls.py --limit 50               # only download 50

Reads from scraped_urls.txt, skips URLs that already have a matching
video file in the download folder.
"""

import argparse
import os
import re
import sys

import scraper_config as cfg
from telegram_sender import send_and_download_sync


def extract_video_id(url):
    """Pull the video ID from a TikTok URL."""
    match = re.search(r'/video/(\d+)', url)
    return match.group(1) if match else None


def load_urls_from_file(filepath):
    """Load TikTok URLs from scraped_urls.txt."""
    if not os.path.exists(filepath):
        return []
    urls = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(" | ")
            if len(parts) >= 4:
                url = parts[-1].strip()
                if "tiktok.com" in url:
                    urls.append(url)
    return urls


def get_downloaded_ids(download_dir):
    """Get set of video IDs already downloaded."""
    if not os.path.exists(download_dir):
        return set()
    ids = set()
    for fname in os.listdir(download_dir):
        if fname.endswith(".mp4"):
            match = re.search(r'(\d{15,})', fname)
            if match:
                ids.add(match.group(1))
    return ids


def main():
    parser = argparse.ArgumentParser(description="Download videos from scraped_urls.txt")
    parser.add_argument(
        "--dir", "-d", default=None,
        help="Download directory (default: tiktok_videos/motion)"
    )
    parser.add_argument(
        "--input", "-i", default=None,
        help="URL file to read from (default: scraped_urls.txt)"
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=0,
        help="Max URLs to download (0 = all)"
    )
    parser.add_argument(
        "--batch", "-b", type=int, default=20,
        help="Download in batches of N (default: 20)"
    )
    args = parser.parse_args()

    download_dir = args.dir or os.path.join(cfg.DOWNLOAD_DIR, "motion")
    url_file = args.input or cfg.OUTPUT_FILE

    print(r"""
    ╔═══════════════════════════════════════════════╗
    ║     DOWNLOAD — Batch Video Downloader         ║
    ║     scraped_urls.txt → Telegram → .mp4        ║
    ╚═══════════════════════════════════════════════╝
    """)

    # Load all URLs
    all_urls = load_urls_from_file(url_file)
    if not all_urls:
        print(f"  No URLs found in {url_file}")
        sys.exit(1)

    print(f"  URL file:     {url_file}")
    print(f"  Total URLs:   {len(all_urls)}")

    # Filter out already downloaded
    downloaded_ids = get_downloaded_ids(download_dir)
    pending_urls = []
    for url in all_urls:
        vid_id = extract_video_id(url)
        if vid_id and vid_id not in downloaded_ids:
            pending_urls.append(url)

    print(f"  Already have: {len(all_urls) - len(pending_urls)}")
    print(f"  To download:  {len(pending_urls)}")
    print(f"  Download to:  {download_dir}")

    if not pending_urls:
        print("\n  Nothing to download!")
        return

    if args.limit > 0:
        pending_urls = pending_urls[:args.limit]
        print(f"  Limited to:   {len(pending_urls)}")

    print()

    # Download in batches
    batch_size = args.batch
    total_downloaded = 0
    total_failed = 0

    for i in range(0, len(pending_urls), batch_size):
        batch = pending_urls[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(pending_urls) + batch_size - 1) // batch_size

        print(f"  ── Batch {batch_num}/{total_batches} ({len(batch)} URLs) ──")

        sent, downloaded, failed = send_and_download_sync(
            batch, download_dir=download_dir
        )
        total_downloaded += downloaded
        total_failed += failed

        print(f"  Batch result: {downloaded} downloaded, {failed} failed")
        print(f"  Running total: {total_downloaded} downloaded\n")

    # Auto-delete videos over max duration
    max_dur = 30  # seconds
    removed = 0
    for fname in os.listdir(download_dir):
        if not fname.endswith(".mp4"):
            continue
        fpath = os.path.join(download_dir, fname)
        try:
            import subprocess
            probe = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1",
                 fpath],
                capture_output=True, text=True, timeout=15,
            )
            dur = float(probe.stdout.strip())
            if dur > max_dur:
                os.remove(fpath)
                removed += 1
                print(f"  [--] Removed {fname} ({dur:.0f}s > {max_dur}s)")
        except Exception:
            pass
    if removed:
        print(f"  [--] Auto-removed {removed} videos over {max_dur}s\n")

    print(f"{'═' * 54}")
    print(f"  DONE!")
    print(f"  Downloaded: {total_downloaded}")
    print(f"  Failed:     {total_failed}")
    print(f"  Saved to:   {download_dir}")
    print(f"{'═' * 54}\n")


if __name__ == "__main__":
    main()
