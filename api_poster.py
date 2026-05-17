"""
API Reel Poster — uploads reels via instagrapi (no BlueStacks UI needed).
Posts from tiktok_videos/motion/ with viral captions.

Usage:
    python api_poster.py              # post all videos in queue
    python api_poster.py --once       # post one and exit
"""

import argparse
import glob
import os
import random
import sys
import time
from datetime import datetime

# Fix Windows console encoding for emoji
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from instagrapi import Client
from instagrapi.exceptions import (
    ChallengeRequired,
    FeedbackRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
    RateLimitError,
)

import config
from video_processor import process_video

VIDEO_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")
SUCCESS_LOG = config.SUCCESS_LOG


def login() -> Client:
    cl = Client()
    cl.delay_range = [3, 8]
    if config.PROXY:
        cl.set_proxy(config.PROXY)

    if os.path.exists(config.SESSION_FILE):
        try:
            cl.load_settings(config.SESSION_FILE)
            cl.login(config.USERNAME, config.PASSWORD)
            cl.dump_settings(config.SESSION_FILE)
            print(f"[+] Logged in as @{config.USERNAME} (session)")
            return cl
        except Exception as e:
            print(f"[~] Session login failed: {e}, trying fresh...")

    cl.login(config.USERNAME, config.PASSWORD)
    cl.dump_settings(config.SESSION_FILE)
    print(f"[+] Logged in as @{config.USERNAME} (fresh)")
    return cl


def load_posted() -> set:
    posted = set()
    if os.path.exists(SUCCESS_LOG):
        with open(SUCCESS_LOG, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(" | ")
                if len(parts) >= 2:
                    posted.add(parts[1].strip())
    return posted


def log_success(filename: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SUCCESS_LOG, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {filename} | API\n")


def get_queue() -> list[str]:
    videos = sorted(glob.glob(os.path.join(VIDEO_DIR, "*.mp4")))
    posted = load_posted()
    queue = [v for v in videos if os.path.basename(v) not in posted]
    random.shuffle(queue)
    return queue


def pick_caption() -> str:
    if hasattr(config, "VIRAL_CAPTIONS") and config.VIRAL_CAPTIONS:
        return random.choice(config.VIRAL_CAPTIONS)
    return "motion"


def post_reel(cl: Client, video_path: str, caption: str) -> bool:
    filename = os.path.basename(video_path)
    print(f"\n{'='*50}")
    print(f"  Posting: {filename}")
    print(f"  Caption: {caption[:80]}...")
    print(f"{'='*50}")

    # Process video (add watermark)
    print("  [proc] Processing video...")
    proc_ok = process_video(video_path, video_path)
    if not proc_ok:
        print("  [~] Processing failed — posting original")

    # Upload via API
    print("  [upload] Uploading reel via API...")
    try:
        media = cl.clip_upload(video_path, caption)
        print(f"  [++] SUCCESS! Media ID: {media.pk}")
        if hasattr(media, 'code') and media.code:
            print(f"  [++] URL: https://www.instagram.com/reel/{media.code}/")
        return True
    except (PleaseWaitFewMinutes, RateLimitError) as e:
        print(f"  [!!] Rate limited: {e}")
        print("  [!!] Sleeping 5 minutes...")
        time.sleep(300)
        return False
    except LoginRequired as e:
        print(f"  [!!] Login required: {e}")
        print("  [!!] Session expired — will re-login next attempt")
        return False
    except (ChallengeRequired, FeedbackRequired) as e:
        print(f"  [!!] Challenge/Feedback required: {e}")
        print("  [!!] Account may need manual verification")
        return False
    except Exception as e:
        print(f"  [!!] Upload failed: {type(e).__name__}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="API Reel Poster")
    parser.add_argument("--once", action="store_true", help="Post one and exit")
    args = parser.parse_args()

    print()
    print("=" * 50)
    print("  API Reel Poster — instagrapi")
    print("  Direct upload, no UI automation")
    print("=" * 50)
    print()

    # Login
    cl = login()

    # Posting loop
    posts_today = 0
    daily_cap = config.DAILY_MAX

    while True:
        queue = get_queue()
        if not queue:
            print("\n[!!] No videos in queue")
            print("     Run: python bluestacks_scraper.py --amount 20")
            if args.once:
                break
            print("     Waiting 10 minutes...")
            time.sleep(600)
            continue

        print(f"\n[*] {len(queue)} videos in queue, {posts_today}/{daily_cap} posted today")

        # Post a batch
        batch_size = config.BATCH_SIZE
        for i in range(batch_size):
            queue = get_queue()
            if not queue:
                break
            if posts_today >= daily_cap:
                print(f"\n[*] Daily cap reached ({daily_cap})")
                break

            video_path = queue[0]
            caption = pick_caption()

            success = post_reel(cl, video_path, caption)

            if success:
                log_success(os.path.basename(video_path))
                posts_today += 1
                if config.DELETE_AFTER_UPLOAD:
                    try:
                        os.remove(video_path)
                        print(f"  [--] Deleted local file")
                    except OSError:
                        pass

                if args.once:
                    print("\n[*] --once flag, exiting.")
                    return
            else:
                # Re-login on failure
                print("  [~] Re-logging in...")
                try:
                    cl = login()
                except Exception:
                    print("  [!!] Re-login failed, waiting 5 min...")
                    time.sleep(300)

            # Short delay between posts in batch
            if i < batch_size - 1:
                delay = random.randint(config.INTRA_BATCH_MIN, config.INTRA_BATCH_MAX)
                print(f"  [batch] Next in {delay}s")
                time.sleep(delay)

        if args.once:
            break

        # Wait between batches
        inter_delay = random.randint(config.INTER_BATCH_FLOOR, config.INTER_BATCH_CEIL)
        next_time = datetime.now().strftime("%H:%M")
        print(f"\n[*] Batch done. Next batch in {inter_delay//60}m (at ~{next_time})")
        time.sleep(inter_delay)


if __name__ == "__main__":
    main()
