"""
Simple Reel Poster — minimal, proven flow.
Posts ONE reel using the exact sequence that was manually verified.

Flow:
1. Push video to BlueStacks
2. Launch Instagram, wait for full load
3. Send ShareHandlerActivity intent
4. Tap OK on popup
5. Pause video, tap Next via uiautomator
6. On caption screen: type caption, tap Share via uiautomator
7. Wait for upload
"""

import glob
import os
import random
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import config

VIDEO_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")
SUCCESS_LOG = config.SUCCESS_LOG
ADB_SERIAL = None


def adb(cmd, timeout=30):
    prefix = ["adb"]
    if ADB_SERIAL:
        prefix = ["adb", "-s", ADB_SERIAL]
    env = os.environ.copy()
    env["MSYS_NO_PATHCONV"] = "1"
    try:
        result = subprocess.run(prefix + cmd, capture_output=True,
                                timeout=timeout, env=env)
        return result.stdout.decode("utf-8", errors="replace").strip()
    except Exception as e:
        print(f"  [adb] error: {e}")
        return ""


def screenshot(name):
    prefix = ["adb"]
    if ADB_SERIAL:
        prefix = ["adb", "-s", ADB_SERIAL]
    env = os.environ.copy()
    env["MSYS_NO_PATHCONV"] = "1"
    with open(name, "wb") as f:
        subprocess.run(prefix + ["exec-out", "screencap", "-p"],
                       stdout=f, timeout=10, env=env)
    print(f"  [screenshot] {name}")


def find_element(text=None, content_desc=None):
    """Find UI element via uiautomator. Returns (x, y) or None."""
    adb(["shell", "uiautomator dump /sdcard/uidump.xml"], timeout=10)
    time.sleep(0.5)
    out = adb(["shell", "cat /sdcard/uidump.xml"], timeout=10)
    adb(["shell", "rm /sdcard/uidump.xml"], timeout=5)

    if not out or '<?xml' not in out:
        return None

    try:
        idx = out.index('<?xml')
        tree = ET.fromstring(out[idx:])
        for node in tree.iter("node"):
            match = False
            if text and node.get("text", "").lower() == text.lower():
                match = True
            if content_desc and content_desc.lower() in node.get("content-desc", "").lower():
                match = True
            if match:
                bounds = node.get("bounds", "")
                nums = re.findall(r"\d+", bounds)
                if len(nums) == 4:
                    cx = (int(nums[0]) + int(nums[2])) // 2
                    cy = (int(nums[1]) + int(nums[3])) // 2
                    return cx, cy
    except Exception:
        pass
    return None


def tap(x, y, label=""):
    if label:
        print(f"  [tap] {label} ({x}, {y})")
    adb(["shell", "input", "tap", str(x), str(y)])


def connect():
    global ADB_SERIAL
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10)
    for line in result.stdout.splitlines():
        if "\tdevice" in line:
            serial = line.split("\t")[0]
            if serial.startswith("127.0.0.1"):
                ADB_SERIAL = serial
                return True
    return False


def get_content_id(filename):
    out = adb(["shell",
               f'content query --uri content://media/external/video/media '
               f'--projection _id --where "_data LIKE \'%{filename}\'"'])
    for line in out.splitlines():
        if "_id=" in line:
            return line.split("_id=")[1].strip().split(",")[0]
    return None


def post_one(video_path, caption):
    filename = os.path.basename(video_path)
    print(f"\n{'='*50}")
    print(f"  Posting: {filename}")
    print(f"{'='*50}")

    # Step 1: Push video
    print("  [1] Pushing video...")
    tmp = f"/data/local/tmp/{filename}"
    remote = f"/sdcard/DCIM/Camera/{filename}"
    adb(["shell", "mkdir", "-p", "/sdcard/DCIM/Camera"])
    adb(["push", video_path, tmp], timeout=120)
    adb(["shell", f"cp {tmp} {remote}"])
    adb(["shell", f"rm {tmp}"])
    adb(["shell", "am", "broadcast",
         "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
         "-d", f"file://{remote}"])
    # Force media scan via MediaScannerConnection-style insert
    adb(["shell",
         f'content insert --uri content://media/external/video/media '
         f'--bind _data:s:{remote} '
         f'--bind mime_type:s:video/mp4'])
    time.sleep(3)

    # Step 2: Get content ID
    print("  [2] Getting content ID...")
    media_id = get_content_id(filename)
    if not media_id:
        # Retry: force insert into media store directly
        print("  [2] Retrying with direct insert...")
        time.sleep(3)
        adb(["shell",
             f'content insert --uri content://media/external/video/media '
             f'--bind _data:s:{remote} '
             f'--bind mime_type:s:video/mp4'])
        time.sleep(3)
        media_id = get_content_id(filename)
    if not media_id:
        print("  [!!] Could not get content ID")
        return False
    print(f"  [2] Content ID: {media_id}")

    # Step 3: Launch Instagram and wait for FULL load
    print("  [3] Launching Instagram...")
    adb(["shell", "am", "force-stop", "com.instagram.android"])
    time.sleep(3)
    adb(["shell", "am", "start", "-n",
         "com.instagram.android/com.instagram.android.activity.MainTabActivity"])
    # Wait until home feed is actually loaded (not splash screen)
    print("  [3] Waiting for home feed to load...")
    for i in range(10):
        time.sleep(3)
        home = find_element(content_desc="Home")
        if home:
            print(f"  [3] Home feed loaded after {(i+1)*3}s")
            break
    else:
        print("  [3] Home feed not detected, waiting 15s extra...")
        time.sleep(15)

    # Step 4: Send share intent
    print("  [4] Sending share intent...")
    adb(["shell", "am", "start",
         "-a", "android.intent.action.SEND",
         "-t", "video/mp4",
         "-n", "com.instagram.android/com.instagram.share.handleractivity.ShareHandlerActivity",
         "--eu", "android.intent.extra.STREAM",
         f"content://media/external/video/media/{media_id}"])
    time.sleep(12)
    screenshot("sp_01_intent.png")

    # Step 5: Handle popup IF present
    print("  [5] Checking for reels popup...")
    reels_popup = find_element(text="Video posts are now shared as reels")
    if reels_popup:
        ok_pos = find_element(text="OK")
        if ok_pos:
            tap(ok_pos[0], ok_pos[1], "OK (popup)")
        else:
            tap(540, 1716, "OK (fallback)")
        time.sleep(10)
    else:
        # No popup — might already be on edit screen, or still loading
        print("  [5] No popup detected, waiting for edit screen...")
        time.sleep(5)
    screenshot("sp_02_after_ok.png")

    # Step 6: Find and tap Next on edit screen
    # CRITICAL: Must pause the video first so uiautomator works.
    # Try multiple times with different pause tap locations.
    print("  [6] Finding Next on edit screen...")
    next_pos = None

    # KEY FIX: Pause video and tap Next in ONE shell command.
    # If there's any delay between pause and Next tap, the video resumes
    # and the Next tap hits the nav bar instead. Combining them in one
    # shell command ensures zero delay.
    print("  [6] Pause + Next in one command...")
    adb(["shell", "input tap 540 960 && sleep 1 && input tap 982 1876"])
    time.sleep(10)

    screenshot("sp_03_after_next.png")

    # Step 6b: Check if we landed in the full video editor
    # (has Edit/Add clips/Audio/Text at bottom). If so, tap → top-right.
    editor_check = find_element(text="Add clips")
    if not editor_check:
        editor_check = find_element(text="Audio")
    if editor_check:
        print("  [6b] In full video editor — tapping → arrow top-right...")
        arrow_pos = find_element(content_desc="Next")
        if arrow_pos:
            tap(arrow_pos[0], arrow_pos[1], "→ arrow (uiautomator)")
        else:
            # Arrow is always in top-right corner
            tap(756, 44, "→ arrow (fallback)")
        time.sleep(6)

    # Step 7: Verify we're on caption/share screen
    # uiautomator can fail due to encoding issues, so try multiple checks
    print("  [7] Checking for caption screen...")
    on_caption_screen = False

    for check in range(3):
        caption_field = find_element(text="Write a caption and add hashtags")
        if not caption_field:
            caption_field = find_element(text="Write a caption")
        share_btn = find_element(content_desc="Share")
        save_draft = find_element(content_desc="Save draft")
        edit_cover = find_element(text="Edit cover")

        on_caption_screen = caption_field or share_btn or save_draft or edit_cover
        if on_caption_screen:
            break
        print(f"  [7] Check {check+1}/3 — not detected yet, waiting 3s...")
        time.sleep(3)

    if not on_caption_screen:
        print("  [!!] Not on caption screen! Aborting.")
        screenshot("sp_04_wrong_screen.png")
        adb(["shell", "am", "force-stop", "com.instagram.android"])
        return False

    print("  [7] On caption/share screen!")

    # Step 8: Type caption
    if caption:
        print("  [8] Typing caption...")
        if caption_field:
            tap(caption_field[0], caption_field[1], "caption field")
        else:
            tap(540, 829, "caption field (fallback)")
        time.sleep(0.5)

        # Type word by word
        safe_caption = ""
        for ch in caption:
            if ord(ch) < 128 and ch not in ('\\', "'", '"', '`', '&', '|', ';', '>', '<'):
                safe_caption += ch
        safe_caption = " ".join(safe_caption.split())[:200]  # trim

        words = safe_caption.split(" ")
        for i, word in enumerate(words):
            if i > 0:
                adb(["shell", "input", "keyevent", "62"])
                time.sleep(0.05)
            if word:
                adb(["shell", "input", "text", word])
                time.sleep(0.05)

        adb(["shell", "input", "keyevent", "111"])  # dismiss keyboard
        time.sleep(1)

    # Step 9: Wait for video to finish processing
    # Share button is GRAYED OUT while "Loading..." spinner is visible.
    # uiautomator can't detect the Loading overlay, so wait a fixed time.
    # Typical processing: 15-45 seconds depending on video size.
    print("  [9] Waiting 60s for video to finish processing...")
    time.sleep(60)

    # Step 10: Tap Share
    print("  [10] Tapping Share...")
    share_pos = find_element(content_desc="Share")
    if share_pos and share_pos[0] > 400:
        tap(share_pos[0], share_pos[1], "Share (uiautomator)")
    else:
        share_pos = find_element(text="Share")
        if share_pos and share_pos[0] > 400:
            tap(share_pos[0], share_pos[1], "Share (text)")
        else:
            tap(802, 1836, "Share (fallback)")

    time.sleep(5)
    screenshot("sp_05_after_share.png")

    # Step 11: Verify we're no longer on caption screen (Share was tapped)
    still_on_caption = find_element(text="Write a caption")
    if not still_on_caption:
        still_on_caption = find_element(content_desc="Save draft")
    if still_on_caption:
        print("  [!!] Still on caption screen — Share didn't work! Retrying...")
        # Try tapping Share again at known position
        tap(802, 1836, "Share retry")
        time.sleep(5)
        still_on_caption = find_element(content_desc="Save draft")
        if still_on_caption:
            print("  [!!] Share failed twice — aborting")
            screenshot("sp_06_share_failed.png")
            adb(["shell", "am", "force-stop", "com.instagram.android"])
            return False

    # Step 12: Wait for upload
    print("  [12] Waiting for upload...")
    time.sleep(45)
    screenshot("sp_06_verify.png")

    # Verify: check for "Keep Instagram open" or home feed
    upload_msg = find_element(text="Keep Instagram open to finish posting")
    home_feed = find_element(content_desc="Home")
    if upload_msg or home_feed:
        print("  [++] Post confirmed uploading!")
    else:
        print("  [~] Could not verify upload, but continuing")

    # Clean up remote file
    adb(["shell", f"rm {remote}"])
    adb(["shell", "am", "force-stop", "com.instagram.android"])

    print(f"  [++] Posted: {filename}")
    return True


def log_success(filename):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SUCCESS_LOG, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {filename} | BlueStacks\n")


def main():
    if not connect():
        print("[!!] No BlueStacks device found")
        sys.exit(1)

    print(f"[+] Device: {ADB_SERIAL}")

    videos = sorted(glob.glob(os.path.join(VIDEO_DIR, "*.mp4")))
    if not videos:
        print("[!!] No videos in queue")
        sys.exit(1)

    print(f"[*] {len(videos)} videos in queue")

    for video_path in videos:
        caption = random.choice(config.VIRAL_CAPTIONS) if config.VIRAL_CAPTIONS else "motion"
        success = post_one(video_path, caption)
        if success:
            log_success(os.path.basename(video_path))
            try:
                os.remove(video_path)
                print(f"  [--] Deleted local file")
            except OSError:
                pass
        else:
            print(f"  [!!] Post failed")

        # Wait between posts
        delay = random.randint(1680, 1920)
        print(f"\n[*] Next post in {delay//60}m")
        time.sleep(delay)


if __name__ == "__main__":
    main()
