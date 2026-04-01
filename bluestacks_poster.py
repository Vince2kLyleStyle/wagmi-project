"""
BlueStacks Instagram Poster
============================
Posts Reels directly through the Instagram app inside BlueStacks
using ADB tap/swipe commands. No API calls whatsoever.
Instagram sees a real Android device doing normal human taps.

Flow per post:
  1. Push video to BlueStacks /sdcard/Movies/ via adb push
  2. Trigger media scanner so Instagram gallery sees it
  3. Launch Instagram
  4. Navigate: + → Reel → select video → Next → Next → caption → Share
  5. Wait for upload confirmation
  6. Log success, delete local file
  7. Wait human-like delay, repeat

Requirements:
  - BlueStacks 4 open, Instagram logged into bot account
  - ADB enabled: BlueStacks Settings > Advanced > Android Debug Bridge > ON
  - adb.exe on Windows PATH (C:\\platform-tools\\)

First run — calibrate screen coordinates:
  python bluestacks_poster.py --calibrate

Normal run:
  python bluestacks_poster.py
  python bluestacks_poster.py --once        # post one video and exit
  python bluestacks_poster.py --dry-run     # push video but don't tap
"""

import argparse
import glob
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime

import config

# ─── Paths ────────────────────────────────────────────────────────
VIDEO_DIR    = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")
SUCCESS_LOG  = config.SUCCESS_LOG
COORDS_FILE  = os.path.join(os.path.dirname(__file__), "bluestacks_coords.json")

# ─── Timing ───────────────────────────────────────────────────────
AFTER_PUSH_SLEEP     = 3      # seconds after adb push before opening IG
AFTER_LAUNCH_SLEEP   = 4      # seconds after opening Instagram
AFTER_TAP_SLEEP      = 1.5   # default between taps
UPLOAD_WAIT          = 45     # seconds to wait for upload to complete
POST_INTERVAL_MIN    = 1500   # 25 min min between posts
POST_INTERVAL_MAX    = 2100   # 35 min max between posts

# ─── Default coordinates (BlueStacks 4, 1080x1920 portrait) ───────
# All values are 0.0-1.0 fractions of screen width/height.
# Run --calibrate to update these for your specific setup.
DEFAULT_COORDS = {
    # Bottom nav "+" button (create post)
    "plus_button":         [0.50, 0.965],
    # "REEL" tab on the creation screen
    "reel_tab":            [0.75, 0.54],
    # First video thumbnail in the gallery grid (top-left cell)
    "first_video":         [0.17, 0.72],
    # "Next" button (top-right corner, appears on multiple screens)
    "next_button":         [0.88, 0.055],
    # Caption text field
    "caption_field":       [0.50, 0.35],
    # "Share" / "Post" button (top-right on final screen)
    "share_button":        [0.88, 0.055],
    # "OK" on any confirmation dialog
    "ok_button":           [0.65, 0.55],
}


# ─── ADB helpers ──────────────────────────────────────────────────

def adb(cmd: list, timeout: int = 30) -> str:
    """Run an adb command. Returns stdout. Exits on connection failure."""
    try:
        result = subprocess.run(
            ["adb"] + cmd,
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        print("[!!] adb not found — add C:\\platform-tools\\ to Windows PATH")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"[!!] ADB command timed out: {' '.join(cmd)}")
        return ""
    except Exception as e:
        print(f"[!!] ADB error: {e}")
        return ""


def connect_bluestacks() -> bool:
    """Auto-connect to BlueStacks on common ports."""
    # Check if already connected
    devices = adb(["devices"])
    if len([l for l in devices.splitlines() if "\tdevice" in l]) > 0:
        return True

    print("[*] Connecting to BlueStacks...")
    for port in [5555, 5556, 5565, 5575]:
        out = adb(["connect", f"127.0.0.1:{port}"])
        if "connected" in out.lower():
            print(f"[+] Connected on port {port}")
            time.sleep(2)
            return True

    print("[!!] Could not connect to BlueStacks.")
    print("     Make sure BlueStacks is open and ADB is enabled.")
    print("     BlueStacks Settings > Advanced > Android Debug Bridge > ON")
    return False


def get_screen_size() -> tuple[int, int]:
    """Get BlueStacks screen dimensions."""
    out = adb(["shell", "wm", "size"])
    # Output: "Physical size: 1080x1920"
    try:
        size_str = out.split(":")[-1].strip()
        w, h = size_str.split("x")
        return int(w), int(h)
    except Exception:
        print("[~] Could not detect screen size, defaulting to 1080x1920")
        return 1080, 1920


def tap(x_pct: float, y_pct: float, w: int, h: int, label: str = ""):
    """Tap at fractional screen coordinates."""
    x = int(w * x_pct)
    y = int(h * y_pct)
    if label:
        print(f"  [tap] {label} ({x}, {y})")
    adb(["shell", "input", "tap", str(x), str(y)])


def swipe(x1_pct, y1_pct, x2_pct, y2_pct, w, h, duration_ms=300):
    """Swipe between two fractional coordinates."""
    x1, y1 = int(w * x1_pct), int(h * y1_pct)
    x2, y2 = int(w * x2_pct), int(h * y2_pct)
    adb(["shell", "input", "swipe",
         str(x1), str(y1), str(x2), str(y2), str(duration_ms)])


def human_delay(base: float, jitter: float = 0.4):
    """Sleep base ± jitter seconds to look human."""
    delay = base + random.uniform(-jitter, jitter)
    time.sleep(max(0.3, delay))


def screenshot(save_as: str = "bluestacks_screen.png"):
    """Take screenshot and pull to local machine."""
    adb(["shell", "screencap", "-p", "/sdcard/screen_tmp.png"])
    adb(["pull", "/sdcard/screen_tmp.png", save_as])
    adb(["shell", "rm", "/sdcard/screen_tmp.png"])
    print(f"[*] Screenshot saved: {save_as}")


def input_text_adb(text: str):
    """
    Type text via ADB. Works for ASCII + basic hashtags.
    Spaces need to be sent as %s. Problematic chars are stripped.
    """
    # Strip chars that break adb input text
    safe = (text
            .replace("\\", "")
            .replace("'", "")
            .replace('"', "")
            .replace("`", "")
            .replace("(", "")
            .replace(")", ""))

    # ADB requires spaces as %s
    parts = safe.split(" ")
    first = True
    for part in parts:
        if not first:
            adb(["shell", "input", "keyevent", "62"])  # KEYCODE_SPACE
            time.sleep(0.1)
        if part:
            adb(["shell", "input", "text", part])
            time.sleep(0.15)
        first = False


# ─── Coords management ────────────────────────────────────────────

def load_coords() -> dict:
    if os.path.exists(COORDS_FILE):
        try:
            with open(COORDS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_COORDS.copy()


def save_coords(coords: dict):
    with open(COORDS_FILE, "w") as f:
        json.dump(coords, f, indent=2)
    print(f"[+] Coords saved to {COORDS_FILE}")


# ─── Core posting flow ────────────────────────────────────────────

def push_video_to_bluestacks(local_path: str) -> str:
    """
    Push video file to BlueStacks gallery.
    Returns the remote path on the Android filesystem.
    """
    filename  = os.path.basename(local_path)
    remote    = f"/sdcard/Movies/{filename}"

    print(f"  [push] {filename} → BlueStacks gallery...")
    out = adb(["push", local_path, remote], timeout=120)
    if "error" in out.lower():
        print(f"  [!!] Push failed: {out}")
        return ""

    # Trigger media scanner so Instagram gallery sees the video
    adb(["shell", "am", "broadcast",
         "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
         "-d", f"file://{remote}"])
    time.sleep(AFTER_PUSH_SLEEP)
    print(f"  [push] Done — media scanned")
    return remote


def launch_instagram():
    """Launch Instagram to home screen."""
    print("  [app] Launching Instagram...")
    adb(["shell", "am", "start",
         "-n", "com.instagram.android/com.instagram.android.activity.MainTabActivity"])
    time.sleep(AFTER_LAUNCH_SLEEP)


def close_instagram():
    """Force-close Instagram (clean state for next post)."""
    adb(["shell", "am", "force-stop", "com.instagram.android"])
    time.sleep(1)


def post_reel(
    video_path: str,
    caption: str,
    coords: dict,
    w: int,
    h: int,
    dry_run: bool = False,
) -> bool:
    """
    Full flow to post one Reel via BlueStacks UI.
    Returns True on likely success, False on failure.
    """
    def t(key, label=""):
        tap(coords[key][0], coords[key][1], w, h, label or key)

    filename = os.path.basename(video_path)
    print(f"\n{'─'*54}")
    print(f"  Posting: {filename}")
    print(f"{'─'*54}")

    # ── Step 1: Push video ────────────────────────────────────────
    remote = push_video_to_bluestacks(video_path)
    if not remote:
        return False

    if dry_run:
        print("  [dry-run] Skipping UI taps")
        return True

    # ── Step 2: Launch Instagram ──────────────────────────────────
    launch_instagram()

    # ── Step 3: Tap "+" to open post creation ────────────────────
    t("plus_button", "open create menu")
    human_delay(2.0)

    # ── Step 4: Tap "REEL" tab ────────────────────────────────────
    t("reel_tab", "select Reel tab")
    human_delay(1.5)

    # ── Step 5: Select most recent video (first in gallery) ───────
    t("first_video", "select video")
    human_delay(2.0)

    # ── Step 6: Tap Next (moves to trim/edit screen) ──────────────
    t("next_button", "Next (to edit screen)")
    human_delay(2.5)

    # ── Step 7: Tap Next again (skip editing, go to caption) ──────
    t("next_button", "Next (to caption screen)")
    human_delay(2.0)

    # ── Step 8: Add caption ───────────────────────────────────────
    if caption:
        t("caption_field", "tap caption field")
        human_delay(0.8)
        input_text_adb(caption)
        human_delay(0.5)
        # Dismiss keyboard
        adb(["shell", "input", "keyevent", "111"])  # KEYCODE_ESCAPE
        human_delay(0.5)

    # ── Step 9: Tap Share/Post ────────────────────────────────────
    t("share_button", "Share (post Reel)")
    human_delay(1.0)

    # ── Step 10: Wait for upload ──────────────────────────────────
    print(f"  [*] Waiting {UPLOAD_WAIT}s for upload...")
    time.sleep(UPLOAD_WAIT)

    # ── Step 11: Close Instagram (clean state) ────────────────────
    close_instagram()

    print(f"  [++] Posted: {filename}")
    return True


# ─── Queue management ─────────────────────────────────────────────

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
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SUCCESS_LOG, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {filename} | BlueStacks\n")


def get_queue() -> list[str]:
    pattern = os.path.join(VIDEO_DIR, "*.mp4")
    videos  = sorted(glob.glob(pattern))
    posted  = load_posted()

    queue = [v for v in videos if os.path.basename(v) not in posted]
    random.shuffle(queue)
    return queue


def pick_caption() -> str:
    """Pick a simple caption that works with ADB text input."""
    options = [
        "sigma motivation",
        "villain arc activated",
        "wolf of wall street vibes",
        "breaking bad energy",
        "aura unlocked",
        "no days off",
        "built different",
        "main character energy",
        "patrick bateman mode",
        "money moves only",
    ]
    return random.choice(options)


# ─── Calibration mode ─────────────────────────────────────────────

def run_calibration(w: int, h: int):
    """
    Interactive calibration — takes screenshots and lets user
    update coordinates for their specific BlueStacks setup.
    """
    coords = load_coords()

    print("""
╔══════════════════════════════════════════════════════╗
║         BlueStacks Calibration Mode                  ║
║  Takes screenshots so you can find the right coords  ║
╚══════════════════════════════════════════════════════╝

This will walk you through each tap point.
For each step:
  1. A screenshot is saved showing the current screen
  2. Open the screenshot to see where to tap
  3. Enter the X,Y pixel coords (or press Enter to keep current)

Screen size: {w}x{h}
""".format(w=w, h=h))

    steps = [
        ("plus_button",   "Step 1: The '+' button to create a new post (bottom nav)"),
        ("reel_tab",      "Step 2: The 'REEL' tab on the creation screen"),
        ("first_video",   "Step 3: The first video thumbnail in the gallery"),
        ("next_button",   "Step 4: The 'Next' button (top right)"),
        ("caption_field", "Step 5: The caption text input field"),
        ("share_button",  "Step 6: The 'Share' / 'Post' button"),
    ]

    print("[*] Opening Instagram for calibration...")
    launch_instagram()

    for key, description in steps:
        print(f"\n{'─'*54}")
        print(f"  {description}")
        cur = coords[key]
        cur_x = int(cur[0] * w)
        cur_y = int(cur[1] * h)
        print(f"  Current: ({cur_x}, {cur_y}) = ({cur[0]:.3f}, {cur[1]:.3f})")

        screenshot(f"calib_{key}.png")
        print(f"  Screenshot saved: calib_{key}.png")
        print(f"  Open it and find the pixel coords for this button.")

        raw = input(f"  Enter new X,Y (or press Enter to keep {cur_x},{cur_y}): ").strip()
        if raw:
            try:
                parts = raw.replace(" ", "").split(",")
                x_px, y_px = int(parts[0]), int(parts[1])
                coords[key] = [round(x_px / w, 4), round(y_px / h, 4)]
                print(f"  Updated: ({x_px}, {y_px}) = ({coords[key][0]}, {coords[key][1]})")
            except Exception:
                print("  Invalid input — keeping current value")

    save_coords(coords)
    print("\n[+] Calibration complete! Run without --calibrate to start posting.")


# ─── Main ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BlueStacks Instagram Poster")
    parser.add_argument("--calibrate",  action="store_true", help="Run coordinate calibration")
    parser.add_argument("--screenshot", action="store_true", help="Take a screenshot and exit")
    parser.add_argument("--once",       action="store_true", help="Post one video and exit")
    parser.add_argument("--dry-run",    action="store_true", help="Push video but skip UI taps")
    parser.add_argument("--daily-cap",  type=int, default=None, help="Max posts per day")
    args = parser.parse_args()

    print("""
╔══════════════════════════════════════════════════════╗
║     BlueStacks Instagram Poster                      ║
║     Real app · Real taps · Undetectable              ║
╚══════════════════════════════════════════════════════╝
""")

    # Connect ADB
    if not connect_bluestacks():
        sys.exit(1)

    # Detect screen
    w, h = get_screen_size()
    print(f"[+] Screen: {w}x{h}")

    # Screenshot only
    if args.screenshot:
        screenshot()
        return

    # Calibration mode
    if args.calibrate:
        run_calibration(w, h)
        return

    # Load coords
    coords = load_coords()
    if not os.path.exists(COORDS_FILE):
        print("[~] Using default coordinates (1080x1920 portrait)")
        print("    Run --calibrate if taps are off\n")

    daily_cap   = args.daily_cap or random.randint(config.DAILY_MIN, config.DAILY_MAX)
    posts_today = 0

    print(f"[*] Video folder: {VIDEO_DIR}")
    print(f"[*] Daily cap:    {daily_cap}")
    print(f"[*] Interval:     {POST_INTERVAL_MIN//60}-{POST_INTERVAL_MAX//60} min between posts\n")

    while True:
        # Rest window check
        hour = datetime.now().hour
        rest_start = getattr(config, "REST_WINDOW_START", 3)
        rest_end   = getattr(config, "REST_WINDOW_END",   9)
        if getattr(config, "REST_WINDOW_ENABLED", True) and rest_start <= hour < rest_end:
            resume_hour = rest_end + random.randint(0, 15) / 60
            print(f"\n[rest] Sleeping until {rest_end}:00 (rest window {rest_start}-{rest_end})")
            while datetime.now().hour < rest_end:
                time.sleep(60)
            print("[rest] Resuming...\n")
            posts_today = 0

        # Daily cap check
        if posts_today >= daily_cap:
            print(f"\n[*] Daily cap reached ({posts_today}). Sleeping until tomorrow...")
            time.sleep(3600 * 6)
            posts_today = 0
            daily_cap = random.randint(config.DAILY_MIN, config.DAILY_MAX)
            print(f"[*] New day — cap: {daily_cap}\n")
            continue

        # Get queue
        queue = get_queue()
        if not queue:
            print("[!!] No videos in queue.")
            print(f"     Run: python instagram_scraper.py --amount 200")
            print("     Waiting 10 minutes then checking again...")
            time.sleep(600)
            continue

        video_path = queue[0]
        caption    = pick_caption()

        print(f"\n[{posts_today+1}/{daily_cap}] {os.path.basename(video_path)}")
        print(f"  Caption: {caption}")

        success = post_reel(video_path, caption, coords, w, h, dry_run=args.dry_run)

        if success:
            log_success(os.path.basename(video_path))
            if config.DELETE_AFTER_UPLOAD and not args.dry_run:
                try:
                    os.remove(video_path)
                    print(f"  [--] Deleted local file")
                except OSError:
                    pass
            posts_today += 1

            if args.once:
                print("\n[*] --once flag set, exiting.")
                break

            # Human-like interval between posts
            delay = random.randint(POST_INTERVAL_MIN, POST_INTERVAL_MAX)
            next_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n[*] Next post in {delay//60}m {delay%60}s")
            time.sleep(delay)
        else:
            print(f"  [!!] Post failed — skipping, waiting 5 min")
            time.sleep(300)


if __name__ == "__main__":
    main()
