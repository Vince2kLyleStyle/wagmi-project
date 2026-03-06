"""
Fader v2 — Instagram Reels Uploader
Survival-optimized with progressive ramp-up, per-niche captions,
and safety-driven rate limiting.

Usage:
    python fader_reels.py [--username USER] [--niche NICHE] [--session FILE]

Requires: pip install instagrapi Pillow
Optional: ffmpeg on PATH for random thumbnail extraction
"""

import argparse
import gc
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
import safety
import niche_config


# ─── Fancy Countdown Timer ──────────────────────────────────────────

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

def create_client(session_file: str | None = None, username: str | None = None) -> Client:
    """
    Create & configure an instagrapi Client with a consistent device profile.
    Uses ONE device per account (persisted across sessions).
    """
    cl = Client()

    # Apply persistent device fingerprint for this account
    acct_name = username or config.USERNAME
    dev = devices.get_device(acct_name)
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


def relogin_client(cl: Client, session_file: str) -> Client:
    """
    Re-login with the SAME device profile (no rotation).
    Only used when the session expires or gets challenged.
    """
    print("\n  [relogin] Re-authenticating (same device)...")

    try:
        cl.login(config.USERNAME, config.PASSWORD)
    except Exception:
        cl = create_client(session_file)

    if session_file:
        cl.dump_settings(session_file)

    print("  [relogin] Session restored.\n")
    return cl


# ─── Upload Logic ──────────────────────────────────────────────────

def upload_reel(cl: Client, video_path: str, niche: str = "") -> str | None:
    """
    Upload a single Reel. Returns the media ID on success, None on failure.
    Uses niche-specific captions when available.
    """
    # Pick caption based on niche
    if config.USE_SAME_CAPTION and config.VIRAL_CAPTIONS:
        caption = random.choice(config.VIRAL_CAPTIONS)
    elif niche and niche in niche_config.NICHE_PROFILES:
        caption = niche_config.get_niche_caption(niche)
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


def log_success(filename: str, media_id: str, niche: str = "") -> None:
    """Append to success.txt with niche tag."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    niche_tag = f" | Niche: {niche}" if niche else ""
    line = f"{timestamp} | {filename} | Media ID: {media_id}{niche_tag}\n"
    with open(config.SUCCESS_LOG, "a", encoding="utf-8") as f:
        f.write(line)


# ─── Gaussian Jitter Delay ─────────────────────────────────────────

def gaussian_delay(center: float, spread: float,
                   floor: float, ceil: float) -> int:
    """
    Generate a delay from a Gaussian distribution, clamped to [floor, ceil].
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
        return []
    return videos


def main() -> None:
    parser = argparse.ArgumentParser(description="Fader v2 — Instagram Reels Uploader")
    parser.add_argument("--username", "-u", default=None, help="Override IG username")
    parser.add_argument("--session", "-s", default=None, help="Path to session.json")
    parser.add_argument("--niche", "-n", default=None, help="Niche for captions (trading, memes, etc.)")
    parser.add_argument("--skip-warmup", action="store_true", help="Skip warm-up phase")
    parser.add_argument("--daily-cap", type=int, default=None, help="Override daily cap")
    parser.add_argument("--warmup-intensity", default=None, help="Warm-up intensity: light, normal, full")
    args = parser.parse_args()

    # Apply overrides
    if args.username:
        config.USERNAME = args.username
        config.SESSION_FILE = os.path.join(config.SESSION_DIR, f"{args.username}_session.json")

    niche = args.niche or config.CURRENT_NICHE or ""
    session_file = args.session or config.SESSION_FILE
    warmup_intensity = args.warmup_intensity or config.WARMUP_INTENSITY

    # Get safe daily limit from safety module
    if args.daily_cap:
        daily_cap = args.daily_cap
    else:
        daily_cap = safety.get_daily_limit(config.USERNAME)

    # ─── Banner ─────────────────────────────────────────────────
    print(r"""
    ╔═══════════════════════════════════════════════╗
    ║     F A D E R  v2  —  Reels Uploader Bot     ║
    ║       Safety-First · Multi-Niche Edition      ║
    ╚═══════════════════════════════════════════════╝
    """)
    print(f"  Account:    @{config.USERNAME}")
    print(f"  Niche:      {niche or 'generic'}")
    print(f"  Daily cap:  {daily_cap} Reels (safety-managed)")
    print(f"  Batch size: {config.BATCH_SIZE}")
    print(f"  Caption:    {'legacy presets' if config.USE_SAME_CAPTION else f'niche: {niche}' if niche else 'randomized'}")
    print(f"  Video dir:  {config.VIDEO_DIR}")
    print(f"  Session:    {session_file}")
    print()

    # ─── Safety Status ──────────────────────────────────────────
    safety.print_account_status(config.USERNAME)

    # ─── Pre-flight Safety Check ────────────────────────────────
    can, reason = safety.can_upload(config.USERNAME)
    if not can:
        if "Daily limit" in reason:
            print(f"[!!] {reason}")
            print("[!!] Account has hit its safe daily limit. Exiting.")
            sys.exit(0)
        elif "Cooling down" in reason:
            print(f"[!!] {reason}")
            print("[!!] Waiting for cooldown to expire...")
            # Wait for cooldown
            state = safety._load_state(config.USERNAME)
            if state.get("cooldown_until"):
                cooldown_end = datetime.fromisoformat(state["cooldown_until"])
                wait_sec = max(0, (cooldown_end - datetime.now()).total_seconds())
                if wait_sec > 0:
                    countdown_timer(int(wait_sec), "Cooldown")

    # ─── Login ──────────────────────────────────────────────────
    print("[*] Logging in...")
    cl = create_client(session_file, config.USERNAME)

    # ─── Warm-up ────────────────────────────────────────────────
    if not args.skip_warmup:
        human_sim.warmup_session(cl, intensity=warmup_intensity)
    else:
        print("[*] Warm-up skipped (--skip-warmup)")

    # ─── Load Queue ─────────────────────────────────────────────
    videos = get_video_queue()
    if not videos:
        print("[*] No videos to upload. Exiting.")
        sys.exit(0)

    total_videos = len(videos)
    total_batches = (total_videos + config.BATCH_SIZE - 1) // config.BATCH_SIZE

    print(f"\n[*] Found {total_videos} videos -> {total_batches} batches")
    print(f"[*] Today's target: {daily_cap} uploads\n")

    # ─── Session State ──────────────────────────────────────────
    uploads_today = 0
    batch_num = 0
    video_idx = 0
    session_start = datetime.now()

    # ─── Main Upload Loop ───────────────────────────────────────
    while video_idx < total_videos:

        # ── Safety check before each batch ─────────────────────
        can, reason = safety.can_upload(config.USERNAME)
        if not can:
            if "Daily limit" in reason:
                print(f"\n[*] Safety limit reached: {reason}")
                break
            elif "Too soon" in reason:
                # Wait for the gap
                gap = safety.get_post_gap(config.USERNAME)
                print(f"\n[*] Safety gap: waiting {gap//60}min before next upload")
                countdown_timer(gap, "Safety gap")
                continue
            elif "Cooling down" in reason:
                print(f"\n[*] {reason}")
                break
            else:
                print(f"\n[*] Safety block: {reason}")
                break

        # ── Daily cap check ─────────────────────────────────────
        if uploads_today >= daily_cap:
            print(f"\n{'='*60}")
            print(f"  DAILY CAP REACHED ({uploads_today}/{daily_cap})")
            print(f"  Session complete. Exiting gracefully.")
            print(f"{'='*60}\n")
            break

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

            human_sim.pre_upload_pause()

            print(f"\n  Uploading [{video_idx + 1}/{total_videos}]: {filename}")
            result = upload_reel(cl, vpath, niche=niche)

            if result == "THROTTLED":
                safety.record_failure(config.USERNAME, "rate_limited")
                print(f"  [!!] Rate limited — applying safety cooldown")
                break

            if result == "CHALLENGE":
                safety.record_failure(config.USERNAME, "challenge")
                print(f"  [!!] Challenge detected — stopping session for safety")
                print(f"  [!!] You may need to manually verify on the app.")
                # Don't retry — exit the session entirely
                video_idx = total_videos  # break outer loop
                break

            if result == "LOGIN_EXPIRED":
                cl = relogin_client(cl, session_file)
                result = upload_reel(cl, vpath, niche=niche)

            if result and result not in ("THROTTLED", "CHALLENGE", "LOGIN_EXPIRED"):
                print(f"  [++] Successfully uploaded: {filename}")
                log_success(filename, result, niche=niche)
                safety.record_upload(config.USERNAME)

                if config.DELETE_AFTER_UPLOAD:
                    gc.collect()
                    deleted = False
                    for attempt in range(5):
                        try:
                            os.remove(vpath)
                            print(f"  [--] Deleted local file: {filename}")
                            deleted = True
                            break
                        except OSError:
                            time.sleep(1)
                    if not deleted:
                        print(f"  [!!] Could not delete {filename} (will retry next run)")

                uploads_today += 1
                human_sim.post_upload_pause()
            elif result is None:
                safety.record_failure(config.USERNAME, "upload_failed")
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
        print(f"\n  Batch {batch_num} complete!")

        # Inter-batch delay (use safety module's recommended gap)
        if video_idx < total_videos and uploads_today < daily_cap:
            delay = safety.get_post_gap(config.USERNAME)
            mins, secs = divmod(delay, 60)
            print(f"  Safety-managed gap: {mins}m {secs}s")

            # Mid-session organic activity during the wait
            human_sim.between_session_activity(cl)

            countdown_timer(delay, "Post gap")

    # ─── Done ───────────────────────────────────────────────────
    elapsed = datetime.now() - session_start
    print(f"\n{'='*60}")
    print(f"  SESSION COMPLETE")
    print(f"  Total uploaded: {uploads_today}")
    print(f"  Session time:   {elapsed}")
    print(f"  Log file:       {config.SUCCESS_LOG}")
    safety.print_account_status(config.USERNAME)
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
