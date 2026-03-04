"""
╔═══════════════════════════════════════════════════════════════╗
║               FADER v2 — Instagram Reels Uploader            ║
║          Survival-optimized · Humanized · March 2026         ║
╚═══════════════════════════════════════════════════════════════╝

Bulk uploads Reels from a local folder via instagrapi with heavy
humanization to maximize account lifespan and follower growth.

Usage:
    python fader_reels.py [--username USER] [--session SESSION_FILE]

Requires: pip install instagrapi Pillow
Optional: ffmpeg on PATH for random thumbnail extraction
"""

import argparse
import glob
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from instagrapi import Client
from instagrapi.exceptions import (
    ChallengeRequired,
    FeedbackRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
    RateLimitError,
)

import config
import captions
import devices
import human_sim


# ─── Fancy Countdown Timer (matches old Fader style) ───────────────

def countdown_timer(seconds: int, label: str = "Batch delay") -> None:
    """Print a live countdown like the original Fader bot."""
    end_time = datetime.now() + timedelta(seconds=seconds)
    next_upload_str = end_time.strftime("%H:%M:%S")
    print(f"  Next upload at: {next_upload_str}")

    remaining = seconds
    while remaining > 0:
        mins, secs = divmod(remaining, 60)
        if mins > 0:
            timer_str = f"{mins}m {secs}s"
        else:
            timer_str = f"{secs}s"
        print(f"\r  {label}: {timer_str} remaining...   ", end="", flush=True)
        time.sleep(1)
        remaining -= 1

    print(f"\r  {label}: done!                          ", flush=True)


# ─── Thumbnail Extraction ──────────────────────────────────────────

def extract_random_thumbnail(video_path: str) -> str | None:
    """
    Use ffmpeg to extract a frame at a random offset.
    Returns path to temp .jpg or None on failure.
    """
    if not config.USE_FFMPEG_THUMBNAIL:
        return None

    try:
        # Get video duration via ffprobe
        probe = subprocess.run(
            [config.FFMPEG_PATH.replace("ffmpeg", "ffprobe"),
             "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1",
             video_path],
            capture_output=True, text=True, timeout=15,
        )
        duration = float(probe.stdout.strip())
        if duration < 1:
            return None

        # Pick a random frame position (avoid first/last 10%)
        offset = random.uniform(duration * 0.1, duration * 0.9)

        thumb_path = os.path.join(
            tempfile.gettempdir(),
            f"fader_thumb_{uuid.uuid4().hex[:8]}.jpg",
        )

        subprocess.run(
            [config.FFMPEG_PATH,
             "-ss", str(offset),
             "-i", video_path,
             "-vframes", "1",
             "-q:v", "2",
             "-y", thumb_path],
            capture_output=True, timeout=15,
        )

        if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
            return thumb_path
    except Exception as e:
        print(f"  [thumbnail] ffmpeg error (non-fatal): {e}")

    return None


# ─── Client Setup ──────────────────────────────────────────────────

def create_client(session_file: str | None = None) -> Client:
    """
    Create & configure an instagrapi Client with random device settings.
    Loads existing session if available, otherwise logs in fresh.
    """
    cl = Client()

    # Apply random device fingerprint
    dev = devices.random_device_settings()
    cl.set_device(dev)

    # Random request delays to look human
    cl.delay_range = [2, 6]

    # Try loading existing session
    if session_file and os.path.exists(session_file):
        try:
            cl.load_settings(session_file)
            cl.login(config.USERNAME, config.PASSWORD)
            print(f"  [session] Resumed from {session_file}")
            return cl
        except Exception as e:
            print(f"  [session] Could not resume ({e}), logging in fresh...")

    # Fresh login
    cl.login(config.USERNAME, config.PASSWORD)
    print(f"  [session] Fresh login as @{config.USERNAME}")

    # Save session for next time
    if session_file:
        os.makedirs(os.path.dirname(session_file), exist_ok=True)
        cl.dump_settings(session_file)
        print(f"  [session] Saved to {session_file}")

    return cl


def refresh_session(cl: Client, session_file: str) -> Client:
    """
    Rotate device fingerprint and re-login.
    Called every N posts to avoid fingerprint staleness.
    """
    print("\n  [refresh] Rotating device fingerprint & re-logging in...")
    dev = devices.random_device_settings()
    cl.set_device(dev)

    try:
        cl.login(config.USERNAME, config.PASSWORD)
    except Exception:
        # If re-login fails, try a completely fresh client
        cl = create_client(session_file)

    if session_file:
        cl.dump_settings(session_file)

    print("  [refresh] New session active.\n")
    return cl


# ─── Upload Logic ──────────────────────────────────────────────────

def upload_reel(cl: Client, video_path: str) -> str | None:
    """
    Upload a single Reel. Returns the media ID on success, None on failure.
    """
    # Use the same viral caption every time (the method) or randomize
    if config.USE_SAME_CAPTION:
        caption = config.VIRAL_CAPTION
    else:
        caption = captions.generate_caption()
    thumbnail = extract_random_thumbnail(video_path)

    kwargs = {
        "path":    video_path,
        "caption": caption,
    }
    if thumbnail:
        kwargs["thumbnail"] = thumbnail

    try:
        media = cl.clip_upload(**kwargs)
        media_id = media.pk if hasattr(media, "pk") else str(media)

        # Clean up temp thumbnail
        if thumbnail and os.path.exists(thumbnail):
            os.remove(thumbnail)

        return str(media_id)

    except (PleaseWaitFewMinutes, RateLimitError) as e:
        print(f"\n  [!!] Rate limited: {e}")
        return "THROTTLED"

    except (ChallengeRequired, FeedbackRequired) as e:
        print(f"\n  [!!] Challenge/Feedback required: {e}")
        return "CHALLENGE"

    except LoginRequired:
        print("\n  [!!] Login expired mid-session!")
        return "LOGIN_EXPIRED"

    except Exception as e:
        print(f"\n  [!!] Upload error: {e}")
        return None

    finally:
        if thumbnail and os.path.exists(thumbnail):
            try:
                os.remove(thumbnail)
            except OSError:
                pass


def log_success(filename: str, media_id: str) -> None:
    """Append to success.txt exactly like old Fader."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} | {filename} | Media ID: {media_id}\n"
    with open(config.SUCCESS_LOG, "a", encoding="utf-8") as f:
        f.write(line)


# ─── Gaussian Jitter Delay ─────────────────────────────────────────

def gaussian_delay(center: float, spread: float,
                   floor: float, ceil: float) -> int:
    """
    Generate a delay from a Gaussian distribution, clamped to [floor, ceil].
    This produces natural-looking variation (not uniform random).
    """
    delay = random.gauss(center, spread)
    delay = max(floor, min(ceil, delay))
    return int(delay)


# ─── Main Loop ─────────────────────────────────────────────────────

def get_video_queue() -> list[str]:
    """Gather all .mp4 files from the video directory, sorted by name."""
    pattern = os.path.join(config.VIDEO_DIR, "*.mp4")
    videos = sorted(glob.glob(pattern))
    if not videos:
        print(f"[!!] No .mp4 files found in {config.VIDEO_DIR}")
        sys.exit(1)
    return videos


def main() -> None:
    parser = argparse.ArgumentParser(description="Fader v2 — Instagram Reels Uploader")
    parser.add_argument("--username", "-u", default=None, help="Override IG username")
    parser.add_argument("--session", "-s", default=None, help="Path to session.json")
    parser.add_argument("--skip-warmup", action="store_true", help="Skip warm-up phase")
    parser.add_argument("--daily-cap", type=int, default=None, help="Override daily cap")
    args = parser.parse_args()

    # Apply overrides
    if args.username:
        config.USERNAME = args.username
        config.SESSION_FILE = os.path.join(config.SESSION_DIR, f"{args.username}_session.json")
    session_file = args.session or config.SESSION_FILE
    daily_cap = args.daily_cap or random.randint(config.DAILY_MIN, config.DAILY_MAX)

    # ─── Banner ─────────────────────────────────────────────────
    print(r"""
    ╔═══════════════════════════════════════════════╗
    ║     F A D E R  v2  —  Reels Uploader Bot     ║
    ║         Survival-Optimized Edition            ║
    ╚═══════════════════════════════════════════════╝
    """)
    print(f"  Account:    @{config.USERNAME}")
    print(f"  Daily cap:  {daily_cap} Reels")
    print(f"  Batch size: {config.BATCH_SIZE} every ~{config.INTER_BATCH_CENTER // 60}min")
    print(f"  Caption:    {'SAME viral caption' if config.USE_SAME_CAPTION else 'randomized'}")
    print(f"  Video dir:  {config.VIDEO_DIR}")
    print(f"  Session:    {session_file}")
    print()

    # ─── Login ──────────────────────────────────────────────────
    print("[*] Logging in...")
    cl = create_client(session_file)

    # ─── Warm-up ────────────────────────────────────────────────
    if not args.skip_warmup:
        human_sim.warmup_session(cl)
    else:
        print("[*] Warm-up skipped (--skip-warmup)")

    # ─── Load Queue ─────────────────────────────────────────────
    videos = get_video_queue()
    total_videos = len(videos)
    total_batches = (total_videos + config.BATCH_SIZE - 1) // config.BATCH_SIZE

    print(f"\n[*] Found {total_videos} videos → {total_batches} batches")
    print(f"[*] Today's target: {daily_cap} uploads\n")

    # ─── Session State ──────────────────────────────────────────
    uploads_today = 0
    uploads_since_refresh = 0
    batch_num = 0
    video_idx = 0
    session_start = datetime.now()

    # ─── Main Upload Loop ───────────────────────────────────────
    while video_idx < total_videos:

        # ── Daily cap check ─────────────────────────────────────
        if uploads_today >= daily_cap:
            now = datetime.now()
            tomorrow = (now + timedelta(days=1)).replace(
                hour=random.randint(7, 11),
                minute=random.randint(0, 59),
                second=0, microsecond=0,
            )
            sleep_sec = int((tomorrow - now).total_seconds())
            print(f"\n{'='*60}")
            print(f"  DAILY CAP REACHED ({uploads_today}/{daily_cap})")
            print(f"  Sleeping until {tomorrow.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")
            countdown_timer(sleep_sec, "Daily pause")

            # Reset for new day
            uploads_today = 0
            daily_cap = random.randint(config.DAILY_MIN, config.DAILY_MAX)
            print(f"\n[*] New day — target: {daily_cap} uploads\n")

            # Re-warm-up at start of new day
            human_sim.warmup_session(cl)

        # ── Session refresh check ───────────────────────────────
        if uploads_since_refresh >= config.REFRESH_EVERY_N_POSTS:
            cl = refresh_session(cl, session_file)
            uploads_since_refresh = 0

        # ── Build batch ─────────────────────────────────────────
        batch_num += 1
        batch_end = min(video_idx + config.BATCH_SIZE, total_videos)
        batch_videos = videos[video_idx:batch_end]

        print(f"{'─'*60}")
        print(f"  Batch {batch_num}/{total_batches}  |  "
              f"Day total: {uploads_today}/{daily_cap}  |  "
              f"Queue: {total_videos - video_idx} remaining")
        print(f"{'─'*60}")

        # ── Upload each video in batch ──────────────────────────
        for i, vpath in enumerate(batch_videos):
            filename = os.path.basename(vpath)

            # Pre-upload human actions
            human_sim.pre_upload_actions(cl)

            print(f"\n  Uploading [{video_idx + 1}/{total_videos}]: {filename}")
            result = upload_reel(cl, vpath)

            if result == "THROTTLED":
                # Rate limited — long sleep then retry once
                sleep_sec = random.randint(
                    config.THROTTLE_SLEEP_MIN, config.THROTTLE_SLEEP_MAX
                )
                print(f"  [throttle] Sleeping {sleep_sec // 60}m before retry...")
                countdown_timer(sleep_sec, "Throttle cooldown")
                result = upload_reel(cl, vpath)

            if result == "CHALLENGE":
                print("  [!!] Challenge detected — pausing 2 hours.")
                print("  [!!] You may need to manually verify on the app.")
                countdown_timer(7200, "Challenge pause")
                # Try re-login
                cl = refresh_session(cl, session_file)
                result = upload_reel(cl, vpath)

            if result == "LOGIN_EXPIRED":
                cl = refresh_session(cl, session_file)
                result = upload_reel(cl, vpath)

            if result and result not in ("THROTTLED", "CHALLENGE", "LOGIN_EXPIRED"):
                # Success!
                print(f"  [++] Successfully uploaded: {filename}")
                log_success(filename, result)

                if config.DELETE_AFTER_UPLOAD:
                    try:
                        os.remove(vpath)
                        print(f"  [--] Deleted local file: {filename}")
                    except OSError as e:
                        print(f"  [!!] Could not delete {filename}: {e}")

                uploads_today += 1
                uploads_since_refresh += 1

                # Post-upload actions
                human_sim.post_upload_actions(cl)
            else:
                print(f"  [!!] Failed to upload: {filename} (skipping)")

            video_idx += 1

            # Intra-batch delay (not after last video in batch)
            if i < len(batch_videos) - 1:
                delay = random.randint(
                    config.INTRA_BATCH_MIN, config.INTRA_BATCH_MAX
                )
                countdown_timer(delay, "Intra-batch delay")

            # Check daily cap mid-batch
            if uploads_today >= daily_cap:
                break

        # ── Batch complete ──────────────────────────────────────
        print(f"\n  Batch {batch_num}/{total_batches} complete!")

        # Inter-batch delay (Gaussian jitter)
        if video_idx < total_videos and uploads_today < daily_cap:
            delay = gaussian_delay(
                config.INTER_BATCH_CENTER,
                config.INTER_BATCH_SPREAD,
                config.INTER_BATCH_FLOOR,
                config.INTER_BATCH_CEIL,
            )
            mins, secs = divmod(delay, 60)
            print(f"  Batch delay: {mins}m {secs}s")
            countdown_timer(delay, "Batch delay")

    # ─── Done ───────────────────────────────────────────────────
    elapsed = datetime.now() - session_start
    print(f"\n{'='*60}")
    print(f"  ALL DONE!")
    print(f"  Total uploaded: {uploads_today}")
    print(f"  Session time:   {elapsed}")
    print(f"  Log file:       {config.SUCCESS_LOG}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
