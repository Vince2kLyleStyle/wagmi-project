#!/usr/bin/env python3
"""
Download IG Reels from pasted URLs via yt-dlp.

Usage:
    python download_urls.py url1 url2 url3 ...
    echo "url1\nurl2" | python download_urls.py -
"""
import os
import sys
import subprocess
import re

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")


def extract_shortcode(url: str) -> str | None:
    m = re.search(r"instagram\.com/(?:reel|p|tv)/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else None


def download(url: str) -> bool:
    shortcode = extract_shortcode(url) or f"url_{hash(url) % 10000}"
    filename = f"ig_{shortcode}.mp4"
    out_path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(out_path):
        print(f"  [skip] {filename} already downloaded")
        return True
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    # Use python -m yt_dlp so we don't depend on the bin being in PATH
    result = subprocess.run(
        ["python", "-m", "yt_dlp",
         "-f", "mp4/best",
         "--merge-output-format", "mp4",
         "-o", out_path,
         "--no-progress",
         "--quiet",
         url],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode == 0 and os.path.exists(out_path):
        size = os.path.getsize(out_path)
        print(f"  [ok] {filename} ({size:,} bytes)")
        return True
    print(f"  [fail] {url}")
    if result.stderr:
        print(f"         {result.stderr.strip()[:200]}")
    return False


def main():
    args = sys.argv[1:]
    if not args:
        print("usage: python download_urls.py url1 url2 ...")
        sys.exit(1)
    if args == ["-"]:
        urls = [line.strip() for line in sys.stdin if line.strip()]
    else:
        urls = args
    ok = 0
    for url in urls:
        if download(url):
            ok += 1
    print(f"\n{ok}/{len(urls)} downloaded to {DOWNLOAD_DIR}")


if __name__ == "__main__":
    main()
