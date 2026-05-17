#!/usr/bin/env python3
"""
BlueStacks Mass Scraper (yt-dlp edition)
=========================================
Drives IG's Reels tab inside BlueStacks to grab reel URLs via
Share -> Copy link -> Windows clipboard, then downloads each via yt-dlp.

Per reel:
  1. Tap Share button
  2. Wait for share sheet
  3. Tap Copy link
  4. Read Windows clipboard (BlueStacks syncs Android -> Windows)
  5. Download via yt-dlp (parallel-ish)
  6. Swipe to dismiss sheet, swipe up to next reel

Usage:
    python mass_scrape.py 200      # scrape up to 200 fresh reels

Stops when target reached OR too many consecutive duplicates/failures.
"""

import os
import re
import subprocess
import sys
import time

ADB = ["adb", "-s", "127.0.0.1:5555"]
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")
SEEN_FILE = os.path.join(os.path.dirname(__file__), "ig_scraped.txt")
LOG_FILE = os.path.join(os.path.dirname(__file__), "mass_scrape.log")


def log(msg: str):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    # Strip non-ASCII for Windows cp1252 console
    safe = line.encode("ascii", errors="replace").decode("ascii")
    print(safe, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def adb_cmd(args: list, timeout: int = 10) -> str:
    env = os.environ.copy()
    env["MSYS_NO_PATHCONV"] = "1"
    try:
        r = subprocess.run(ADB + args, capture_output=True, text=True,
                           timeout=timeout, env=env)
        return r.stdout
    except subprocess.TimeoutExpired:
        return ""


def tap(x: int, y: int):
    adb_cmd(["shell", "input", "tap", str(x), str(y)])


def swipe(x1: int, y1: int, x2: int, y2: int, dur: int = 400):
    adb_cmd(["shell", "input", "swipe", str(x1), str(y1),
             str(x2), str(y2), str(dur)])


def keyevent(code: int):
    adb_cmd(["shell", "input", "keyevent", str(code)])


def set_clipboard(text: str):
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"Set-Clipboard -Value '{text}'"],
        capture_output=True, timeout=10
    )


def read_clipboard() -> str:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
        capture_output=True, text=True, timeout=10
    )
    return r.stdout.strip()


def open_reels_tab():
    """Navigate to the vertical Reels feed (between Home and Messages)."""
    adb_cmd(["shell", "am", "force-stop", "com.instagram.android"], timeout=10)
    time.sleep(2)
    adb_cmd(["shell", "am", "start", "-n",
             "com.instagram.android/com.instagram.android.activity.MainTabActivity"])
    time.sleep(6)
    tap(324, 1876)  # Reels tab (center of bottom nav slot 2)
    time.sleep(6)


def open_explore_feed():
    """Navigate to Explore tab (right before Profile) and tap the first
    video tile to enter the vertical explore-reel feed. After that, the
    same grab_url + swipe-up loop works."""
    adb_cmd(["shell", "am", "force-stop", "com.instagram.android"], timeout=10)
    time.sleep(2)
    adb_cmd(["shell", "am", "start", "-n",
             "com.instagram.android/com.instagram.android.activity.MainTabActivity"])
    time.sleep(6)
    tap(756, 1876)  # Explore / Search tab (slot 4)
    time.sleep(6)
    # Tap the first content tile in the explore grid.
    # Grid tiles are in a 3-col layout; first tile is approx (180, 430).
    tap(180, 430)
    time.sleep(6)


def _find_element_by_desc(desc: str, min_x: int = 0) -> tuple[int, int] | None:
    """Dump UI and find center of an element by content-desc (exact match).
    `min_x` restricts to elements whose center X exceeds that value —
    useful when there are multiple elements sharing a desc (e.g., the
    Share action-bar icon vs the Share button inside a sheet)."""
    import xml.etree.ElementTree as ET
    adb_cmd(["shell", "uiautomator", "dump", "/sdcard/_d.xml"], timeout=15)
    adb_cmd(["pull", "/sdcard/_d.xml", "_d.xml"], timeout=10)
    adb_cmd(["shell", "rm", "/sdcard/_d.xml"], timeout=5)
    try:
        tree = ET.parse("_d.xml")
    except Exception:
        return None
    for node in tree.getroot().iter("node"):
        if node.get("content-desc", "") != desc:
            continue
        bounds = node.get("bounds", "")
        nums = re.findall(r"\d+", bounds)
        if len(nums) != 4:
            continue
        cx = (int(nums[0]) + int(nums[2])) // 2
        cy = (int(nums[1]) + int(nums[3])) // 2
        if cx < min_x:
            continue
        try:
            os.remove("_d.xml")
        except OSError:
            pass
        return cx, cy
    try:
        os.remove("_d.xml")
    except OSError:
        pass
    return None


def grab_url() -> str | None:
    """Dump UI to find Share/Copy link coords (they shift when a reel
    has the Repost icon), tap, and read the Windows clipboard."""
    sentinel = f"SENTINEL_{int(time.time() * 1000)}"
    set_clipboard(sentinel)

    # Find the Share button dynamically. Action-bar Share lives on the
    # right side (x > 900); inside the share sheet there's another
    # "Share" element that sits closer to center, so restrict by min_x.
    share = _find_element_by_desc("Share", min_x=900)
    if not share:
        return None
    tap(share[0], share[1])
    time.sleep(2.0)

    copy = _find_element_by_desc("Copy link", min_x=0)
    if not copy:
        return None
    tap(copy[0], copy[1])
    time.sleep(2.5)

    clip = read_clipboard()
    if clip == sentinel or not clip:
        return None
    m = re.search(
        r"https://www\.instagram\.com/(?:reel|p)/([A-Za-z0-9_-]+)",
        clip
    )
    return f"https://www.instagram.com/reel/{m.group(1)}/" if m else None


def dismiss_share_sheet():
    # Back key reliably closes the share sheet without affecting the
    # Reels feed. Swipe-dismiss sometimes scrolled the contact carousel
    # inside the sheet instead of closing the sheet.
    keyevent(4)
    time.sleep(1.0)


def next_reel():
    swipe(540, 1400, 540, 500, 400)
    time.sleep(4.5)


def is_on_reels() -> bool:
    """Quick check: is the Reels action bar (Share button) visible?"""
    xml = adb_cmd(["shell", "uiautomator", "dump", "/sdcard/_r.xml"], timeout=10)
    if "dumped" not in xml.lower():
        return False
    data = adb_cmd(["shell", "cat", "/sdcard/_r.xml"], timeout=10)
    adb_cmd(["shell", "rm", "/sdcard/_r.xml"], timeout=5)
    return 'content-desc="Share"' in data and 'content-desc="Reel by' in data


def load_seen() -> set:
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def mark_seen(shortcode: str):
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        f.write(shortcode + "\n")


def download(url: str) -> bool:
    shortcode = url.rstrip("/").split("/")[-1]
    out = os.path.join(DOWNLOAD_DIR, f"ig_{shortcode}.mp4")
    if os.path.exists(out):
        return True
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    r = subprocess.run(
        ["python", "-m", "yt_dlp",
         "-f", "mp4/best",
         "--merge-output-format", "mp4",
         "-o", out,
         "--no-progress", "--quiet",
         url],
        capture_output=True, text=True, timeout=180,
    )
    return r.returncode == 0 and os.path.exists(out)


def filter_video(path: str) -> tuple[bool, str]:
    """Return (keep, reason_if_rejected)."""
    try:
        # Get duration + width/height
        r = subprocess.run(
            ["ffprobe", "-v", "error",
             "-select_streams", "v:0",
             "-show_entries", "stream=width,height,duration",
             "-of", "csv=p=0",
             path],
            capture_output=True, text=True, timeout=10
        )
        parts = r.stdout.strip().split(",")
        if len(parts) < 3:
            return False, "no video stream"
        w, h, d = int(parts[0]), int(parts[1]), float(parts[2])
    except Exception as e:
        return False, f"ffprobe err: {e}"

    if d < 3 or d > 30:
        return False, f"duration {d:.1f}s"
    if h < w:
        return False, f"not vertical ({w}x{h})"
    size = os.path.getsize(path)
    if size < 200_000:
        return False, f"size too small {size}"
    return True, ""


def scrape(target: int, mode: str = "mixed"):
    """mode: 'reels' | 'explore' | 'mixed' (alternates every 25 collected)"""
    seen = load_seen()
    collected = 0
    duplicates = 0
    grabs_failed = 0
    downloads_failed = 0
    rejects = 0
    attempts = 0
    current_source = "reels"  # start with Reels tab

    log(f"Starting. Target: {target} new reels. Mode: {mode}. Seen: {len(seen)}")
    if mode == "explore":
        current_source = "explore"
        open_explore_feed()
    else:
        open_reels_tab()

    max_attempts = target * 4
    rejects_dir = os.path.join(os.path.dirname(DOWNLOAD_DIR), "rejects",
                               "autofiltered")
    os.makedirs(rejects_dir, exist_ok=True)

    while collected < target and attempts < max_attempts:
        attempts += 1
        url = grab_url()

        if not url:
            grabs_failed += 1
            log(f"  [{attempts}] grab failed (total fails: {grabs_failed})")
            if grabs_failed % 5 == 0:
                # Try relaunching Reels tab if many consecutive fails
                log("  [!] many grab fails - reopening Reels tab")
                open_reels_tab()
                grabs_failed = 0
                continue
            dismiss_share_sheet()
            next_reel()
            continue
        grabs_failed = 0

        shortcode = url.rstrip("/").split("/")[-1]
        if shortcode in seen:
            duplicates += 1
            if duplicates % 10 == 0:
                log(f"  [{attempts}] dup ({duplicates} total)")
            dismiss_share_sheet()
            next_reel()
            continue
        seen.add(shortcode)
        mark_seen(shortcode)

        # Download
        ok = download(url)
        out_path = os.path.join(DOWNLOAD_DIR, f"ig_{shortcode}.mp4")

        if not ok or not os.path.exists(out_path):
            downloads_failed += 1
            log(f"  [!] dl failed: {shortcode}")
            dismiss_share_sheet()
            next_reel()
            continue

        # Filter
        keep, reason = filter_video(out_path)
        if not keep:
            try:
                os.rename(out_path, os.path.join(rejects_dir, os.path.basename(out_path)))
            except OSError:
                try:
                    os.remove(out_path)
                except OSError:
                    pass
            rejects += 1
            log(f"  [reject] {shortcode}: {reason}")
            dismiss_share_sheet()
            next_reel()
            continue

        collected += 1
        size_kb = os.path.getsize(out_path) // 1024
        log(f"  [{collected}/{target}] KEEP {shortcode} ({size_kb} KB) [{current_source}]")

        dismiss_share_sheet()
        next_reel()

        # In mixed mode, alternate sources every 25 videos so the queue
        # has content from both the Reels feed and Explore feed.
        if mode == "mixed" and collected % 25 == 0:
            if current_source == "reels":
                current_source = "explore"
                log(f"  [switch] -> explore feed after {collected} kept")
                open_explore_feed()
            else:
                current_source = "reels"
                log(f"  [switch] -> reels feed after {collected} kept")
                open_reels_tab()

    log("")
    log(f"Done: {collected}/{target} kept | "
        f"{duplicates} dups | {rejects} rejects | "
        f"{downloads_failed} dl fails | {attempts} attempts")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    mode = sys.argv[2] if len(sys.argv) > 2 else "mixed"
    scrape(count, mode)
