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
from datetime import datetime, timedelta, timezone
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
        print(f"  {label}: {timer_str} remaining...", flush=True)
        time.sleep(1)
        remaining -= 1

    print(f"  {label}: done!", flush=True)


# ─── Thumbnail Extraction ──────────────────────────────────────────

def generate_branded_thumbnail(video_path: str = "") -> str | None:
    """
    Always uses thumbnail.jpg from the project folder.
    Returns path to temp .jpg or None if thumbnail.jpg not found.
    """
    if not config.USE_FFMPEG_THUMBNAIL:
        return None

    try:
        import shutil

        project_dir = os.path.dirname(os.path.abspath(__file__))
        thumb_src = os.path.join(project_dir, "thumbnail.jpg")

        if os.path.exists(thumb_src):
            thumb_path = os.path.join(
                tempfile.gettempdir(),
                f"fader_thumb_{uuid.uuid4().hex[:8]}.jpg",
            )
            shutil.copy2(thumb_src, thumb_path)
            if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
                return thumb_path

        print("  [thumbnail] thumbnail.jpg not found in project folder — uploading without cover")
        return None

    except Exception as e:
        print(f"  [thumbnail] error: {e}")
        return None




# ─── Client Setup ──────────────────────────────────────────────────

def create_client(session_file: str | None = None) -> Client:
    """
    Create & configure an instagrapi Client with today's device profile.
    Loads existing session if available, otherwise logs in fresh.
    Uses ONE consistent device per day (rotating mid-session is a red flag).
    """
    cl = Client()

    # Apply proxy if configured
    if config.PROXY:
        cl.set_proxy(config.PROXY)
        print(f"  [proxy] Using proxy: {config.PROXY.split('@')[-1] if '@' in config.PROXY else config.PROXY}")

    # Apply today's device fingerprint (consistent for the whole day)
    dev = devices.get_device()
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
        # If re-login fails, create a fresh client (still same device for today)
        cl = create_client(session_file)

    if session_file:
        cl.dump_settings(session_file)

    print("  [relogin] Session restored.\n")
    return cl


# ─── Watermark Overlay ────────────────────────────────────────────

def apply_watermark(video_path: str) -> str | None:
    """
    Burn a text watermark onto the video using ffmpeg.
    Returns path to the watermarked temp file, or None on failure.
    Original file is NOT modified.
    """
    if not config.WATERMARK_ENABLED:
        return None

    text = config.WATERMARK_TEXT
    fontsize = config.WATERMARK_FONTSIZE
    opacity = config.WATERMARK_OPACITY
    color = config.WATERMARK_COLOR
    position = config.WATERMARK_POSITION
    font_file = config.WATERMARK_FONT

    # Map position to ffmpeg drawtext x:y expressions
    # Add padding from edges
    pad = 20
    pos_map = {
        "top_left":     f"x={pad}:y={pad}",
        "top_right":    f"x=w-tw-{pad}:y={pad}",
        "bottom_left":  f"x={pad}:y=h-th-{pad}",
        "bottom_right": f"x=w-tw-{pad}:y=h-th-{pad}",
        "center":       f"x=(w-tw)/2:y=(h-th)/2",
    }
    xy = pos_map.get(position, pos_map["bottom_right"])

    # Build drawtext filter
    # Escape special characters for ffmpeg
    escaped_text = text.replace("'", "'\\''").replace(":", "\\:")
    font_arg = f":fontfile='{font_file}'" if font_file else ""
    alpha = f":alpha={opacity}" if opacity < 1.0 else ""

    drawtext = (
        f"drawtext=text='{escaped_text}'"
        f":fontsize={fontsize}"
        f":fontcolor={color}{alpha}"
        f":{xy}"
        f"{font_arg}"
        f":borderw=2:bordercolor=black@0.5"
    )

    # Output to temp file
    out_path = os.path.join(
        tempfile.gettempdir(),
        f"fader_wm_{uuid.uuid4().hex[:8]}.mp4",
    )

    try:
        result = subprocess.run(
            [config.FFMPEG_PATH,
             "-i", video_path,
             "-vf", drawtext,
             "-codec:a", "copy",
             "-y", out_path],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            print(f"  [watermark] ffmpeg error: {result.stderr[:200]}")
            return None

        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return out_path

    except Exception as e:
        print(f"  [watermark] Error (non-fatal): {e}")

    return None


# ─── Pinned Comment ───────────────────────────────────────────────

def pin_comment_on_reel(cl: Client, media_id: str, media_pk: str = "") -> bool:
    """Post a comment and pin it on the uploaded reel."""
    if not config.PIN_COMMENT_ENABLED:
        return False

    comment_text = random.choice(config.PIN_COMMENTS)
    try:
        # Post the comment
        comment = cl.media_comment(media_id, comment_text)
        comment_pk = comment.pk
        time.sleep(random.uniform(2, 5))

        # Pin using media_pk (numeric ID) — Instagram's pin endpoint needs this
        pin_id = media_pk or media_id
        try:
            cl.comment_pin(pin_id, comment_pk)
            print(f"  [pin] Pinned: \"{comment_text}\"")
        except Exception as pin_err:
            # If pin fails, try with the other ID format
            alt_id = media_id if pin_id == media_pk else media_pk
            if alt_id and alt_id != pin_id:
                try:
                    cl.comment_pin(alt_id, comment_pk)
                    print(f"  [pin] Pinned (alt): \"{comment_text}\"")
                except Exception:
                    print(f"  [pin] Comment posted but pin failed: {pin_err}")
            else:
                print(f"  [pin] Comment posted but pin failed: {pin_err}")
        return True
    except Exception as e:
        print(f"  [pin] Comment/pin error (non-fatal): {e}")
        return False


# ─── Upload Logic ──────────────────────────────────────────────────

def upload_reel(cl: Client, video_path: str) -> str | None:
    """
    Upload a single Reel. Returns the media ID on success, None on failure.
    Applies watermark if enabled, pins comment after upload.
    """
    # Pick from the 3 preset captions, or use the random generator
    if config.USE_SAME_CAPTION:
        caption = random.choice(config.VIRAL_CAPTIONS)
    else:
        caption = captions.generate_caption()
    thumbnail = generate_branded_thumbnail(video_path)

    # Apply watermark overlay
    watermarked = apply_watermark(video_path)
    upload_path = watermarked or video_path

    kwargs = {
        "path":    upload_path,
        "caption": caption,
    }
    if thumbnail:
        kwargs["thumbnail"] = thumbnail

    try:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(cl.clip_upload, **kwargs)
            try:
                media = future.result(timeout=300)  # 5 min max per upload
            except concurrent.futures.TimeoutError:
                print(f"\n  [!!] Upload timed out after 5 minutes — skipping")
                return None
        media_pk = str(media.pk) if hasattr(media, "pk") else str(media)
        media_full_id = media.id if hasattr(media, "id") else media_pk

        # Clean up temp files
        if thumbnail and os.path.exists(thumbnail):
            os.remove(thumbnail)
        if watermarked and os.path.exists(watermarked):
            os.remove(watermarked)

        # Pin comment on the new reel
        time.sleep(random.uniform(2, 5))
        pin_comment_on_reel(cl, media_full_id, media_pk=media_pk)

        return str(media_pk)

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
        if watermarked and os.path.exists(watermarked):
            try:
                os.remove(watermarked)
            except OSError:
                pass


def check_and_prune(cl: Client) -> bool:
    """
    Fetch recent reels, delete dead posts, and check for viral momentum.
    Returns True if surge mode should be active (a post crossed SURGE_THRESHOLD).
    """
    min_views = getattr(config, "PRUNE_MIN_VIEWS", 10)
    grace_minutes = getattr(config, "PRUNE_GRACE_MINUTES", 180)
    surge_threshold = getattr(config, "SURGE_THRESHOLD", 10_000)
    surge_enabled = getattr(config, "SURGE_ENABLED", False)
    prune_enabled = getattr(config, "PRUNE_ENABLED", False)
    grace_cutoff = datetime.now(timezone.utc) - timedelta(minutes=grace_minutes)

    print(f"\n  [check] Scanning recent posts...")

    try:
        medias = cl.user_medias(cl.user_id, amount=50)
    except Exception as e:
        print(f"  [check] Could not fetch posts: {e}")
        return False

    deleted = 0
    skipped_grace = 0
    surge_active = False

    for media in medias:
        try:
            media_type = getattr(media, "media_type", None)
            product_type = getattr(media, "product_type", "")
            if media_type not in (2,) and product_type != "clips":
                continue

            taken_at = getattr(media, "taken_at", None)
            if taken_at is None:
                continue
            if taken_at.tzinfo is None:
                taken_at = taken_at.replace(tzinfo=timezone.utc)

            views = getattr(media, "view_count", None) or getattr(media, "video_view_count", 0) or 0

            # Surge check — any post going viral?
            if surge_enabled and views >= surge_threshold:
                print(f"  [SURGE] Post {media.pk} has {views:,} views — SURGE MODE ON")
                surge_active = True

            # Skip grace period for pruning
            if taken_at > grace_cutoff:
                skipped_grace += 1
                continue

            # Prune dead posts
            if prune_enabled and views < min_views:
                cl.media_delete(str(media.pk))
                print(f"  [prune] Deleted {media.pk} ({views} views)")
                deleted += 1
                time.sleep(random.uniform(2, 4))

        except Exception as e:
            print(f"  [check] Error on media {getattr(media, 'pk', '?')}: {e}")
            continue

    print(f"  [check] Done — deleted {deleted}, skipped {skipped_grace} in grace | surge={'ON' if surge_active else 'off'}\n")
    return surge_active


def log_success(filename: str, media_id: str) -> None:
    """Append to success.txt exactly like old Fader."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} | {filename} | Media ID: {media_id}\n"
    with open(config.SUCCESS_LOG, "a", encoding="utf-8") as f:
        f.write(line)


# ─── Duplicate Check ──────────────────────────────────────────────

def load_posted_filenames() -> set:
    """Load filenames already posted from success.txt."""
    posted = set()
    if os.path.exists(config.SUCCESS_LOG):
        with open(config.SUCCESS_LOG, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(" | ")
                if len(parts) >= 2:
                    posted.add(parts[1].strip())
    return posted


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

def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        probe = subprocess.run(
            [config.FFMPEG_PATH.replace("ffmpeg", "ffprobe"),
             "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1",
             video_path],
            capture_output=True, text=True, timeout=15,
        )
        return float(probe.stdout.strip())
    except Exception:
        return 0.0


def get_video_height(video_path: str) -> int:
    """Get video height in pixels using ffprobe."""
    try:
        probe = subprocess.run(
            [config.FFMPEG_PATH.replace("ffmpeg", "ffprobe"),
             "-v", "error",
             "-select_streams", "v:0",
             "-show_entries", "stream=height",
             "-of", "default=noprint_wrappers=1:nokey=1",
             video_path],
            capture_output=True, text=True, timeout=15,
        )
        return int(probe.stdout.strip())
    except Exception:
        return 0


def get_video_queue() -> list[str]:
    """Gather all .mp4 files, auto-delete long or low-quality videos."""
    pattern = os.path.join(config.VIDEO_DIR, "*.mp4")
    all_videos = sorted(glob.glob(pattern))

    if not all_videos:
        print(f"[!!] No .mp4 files found in {config.VIDEO_DIR}")
        sys.exit(1)

    max_dur = getattr(config, "MAX_VIDEO_DURATION", 0)
    min_height = getattr(config, "MIN_VIDEO_HEIGHT", 0)

    if not max_dur and not min_height:
        return all_videos

    videos = []
    removed_dur = 0
    removed_quality = 0

    print(f"[*] Filtering videos (max {max_dur}s, min {min_height}p)...")

    for vpath in all_videos:
        fname = os.path.basename(vpath)

        # Check duration
        if max_dur:
            dur = get_video_duration(vpath)
            if dur > max_dur:
                print(f"  [--] {fname} — too long ({dur:.0f}s)")
                os.remove(vpath)
                removed_dur += 1
                continue

        # Check resolution
        if min_height:
            height = get_video_height(vpath)
            if height > 0 and height < min_height:
                print(f"  [--] {fname} — low quality ({height}p)")
                os.remove(vpath)
                removed_quality += 1
                continue

        videos.append(vpath)

    if removed_dur or removed_quality:
        print(f"  [--] Removed: {removed_dur} too long, {removed_quality} low quality\n")

    if not videos:
        print(f"[!!] No videos passed filters in {config.VIDEO_DIR}")
        sys.exit(1)

    # Remove any videos that were already posted (check success.txt)
    posted = load_posted_filenames()
    already_posted = []
    clean_videos = []
    for vpath in videos:
        fname = os.path.basename(vpath)
        if fname in posted:
            already_posted.append(fname)
            os.remove(vpath)
        else:
            clean_videos.append(vpath)

    if already_posted:
        print(f"  [--] Removed {len(already_posted)} already-posted duplicates\n")

    if not clean_videos:
        print(f"[!!] No unposted videos in {config.VIDEO_DIR}")
        sys.exit(1)

    # Shuffle so we don't post in the same order every restart
    random.shuffle(clean_videos)

    return clean_videos


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
    print(f"  Caption:    {'rotating (3 presets)' if config.USE_SAME_CAPTION else 'fully randomized'}")
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
    batch_num = 0
    video_idx = 0
    session_start = datetime.now()
    surge_mode = False

    # ─── Main Upload Loop ───────────────────────────────────────
    while video_idx < total_videos:

        # ── Rest window / active window check ───────────────────
        now_hour = datetime.now().hour
        rest_start = getattr(config, "REST_WINDOW_START", 2)
        rest_end = getattr(config, "REST_WINDOW_END", 6)
        active_start = getattr(config, "ACTIVE_WINDOW_START", 11)
        active_end = getattr(config, "ACTIVE_WINDOW_END", 26)  # 26 = wraps past midnight

        # Normalize active_end for comparison (26 means next day up to 2am)
        in_active = (now_hour >= active_start) or (active_end > 24 and now_hour < (active_end - 24))

        if getattr(config, "REST_WINDOW_ENABLED", False) and rest_start <= now_hour < rest_end:
            resume = datetime.now().replace(hour=rest_end, minute=random.randint(0, 15), second=0, microsecond=0)
            sleep_sec = max(0, int((resume - datetime.now()).total_seconds()))
            print(f"\n  [rest] Sleeping until {resume.strftime('%H:%M')} — rest window")
            countdown_timer(sleep_sec, "Rest window")
            human_sim.warmup_session(cl)
        elif getattr(config, "ACTIVE_WINDOW_ENABLED", False) and not in_active:
            resume = datetime.now().replace(hour=active_start, minute=random.randint(0, 10), second=0, microsecond=0)
            if resume < datetime.now():
                resume = resume.replace(day=resume.day + 1)
            sleep_sec = max(0, int((resume - datetime.now()).total_seconds()))
            print(f"\n  [waiting] Outside active hours — resuming at {resume.strftime('%H:%M')}")
            countdown_timer(sleep_sec, "Waiting for active window")
            human_sim.warmup_session(cl)

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

            # Short pause before upload
            human_sim.pre_upload_pause()

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
                cl = relogin_client(cl, session_file)
                result = upload_reel(cl, vpath)

            if result == "LOGIN_EXPIRED":
                cl = relogin_client(cl, session_file)
                result = upload_reel(cl, vpath)

            if result and result not in ("THROTTLED", "CHALLENGE", "LOGIN_EXPIRED"):
                # Success!
                print(f"  [++] Successfully uploaded: {filename}")
                log_success(filename, result)

                if config.DELETE_AFTER_UPLOAD:
                    # Force-close any lingering file handles from instagrapi
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

                # Short pause after upload
                human_sim.post_upload_pause()
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

        # ── Check posts + prune every N batches ─────────────────
        prune_interval = getattr(config, "PRUNE_INTERVAL_BATCHES", 4)
        if batch_num % prune_interval == 0:
            surge_mode = check_and_prune(cl)

        # Inter-batch delay — cut in half during surge
        if video_idx < total_videos and uploads_today < daily_cap:
            if surge_mode and getattr(config, "SURGE_ENABLED", False):
                delay = gaussian_delay(
                    config.SURGE_INTER_BATCH_CENTER,
                    config.INTER_BATCH_SPREAD,
                    config.SURGE_INTER_BATCH_FLOOR,
                    config.SURGE_INTER_BATCH_CEIL,
                )
                print(f"  SURGE MODE — batch delay: {delay // 60}m {delay % 60}s")
            else:
                delay = gaussian_delay(
                    config.INTER_BATCH_CENTER,
                    config.INTER_BATCH_SPREAD,
                    config.INTER_BATCH_FLOOR,
                    config.INTER_BATCH_CEIL,
                )
                print(f"  Batch delay: {delay // 60}m {delay % 60}s")
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
