"""
Debug Post — step-by-step posting with screenshots at every stage.
Run this to see exactly where the posting flow breaks.
"""
import glob
import os
import random
import subprocess
import sys
import time

import config

ADB_SERIAL = None

def adb(cmd, timeout=30):
    try:
        prefix = ["adb"]
        if ADB_SERIAL:
            prefix = ["adb", "-s", ADB_SERIAL]
        env = os.environ.copy()
        env["MSYS_NO_PATHCONV"] = "1"
        result = subprocess.run(prefix + cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return result.stdout.strip()
    except Exception as e:
        print(f"[!!] ADB error: {e}")
        return ""

def screenshot(name):
    adb(["exec-out", "screencap", "-p"], timeout=10)
    # Use exec-out to pull screenshot
    prefix = ["adb"]
    if ADB_SERIAL:
        prefix = ["adb", "-s", ADB_SERIAL]
    env = os.environ.copy()
    env["MSYS_NO_PATHCONV"] = "1"
    with open(name, "wb") as f:
        result = subprocess.run(prefix + ["exec-out", "screencap", "-p"], stdout=f, timeout=10, env=env)
    print(f"  [screenshot] {name}")

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
                print(f"[+] Using: {ADB_SERIAL}")
                return True
    print("[!!] No device found")
    return False

def main():
    if not connect():
        sys.exit(1)

    # Find a video to post
    VIDEO_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")
    videos = sorted(glob.glob(os.path.join(VIDEO_DIR, "*.mp4")))
    if not videos:
        print("[!!] No videos in queue")
        sys.exit(1)

    video_path = videos[0]
    filename = os.path.basename(video_path)
    print(f"\n[*] Debug posting: {filename}")
    print(f"[*] Taking screenshots at every step\n")

    # Step 0: Push video
    print("=" * 50)
    print("STEP 0: Push video to BlueStacks")
    print("=" * 50)
    tmp_path = f"/data/local/tmp/{filename}"
    remote = f"/sdcard/DCIM/Camera/{filename}"
    adb(["shell", "mkdir", "-p", "/sdcard/DCIM/Camera"])
    adb(["push", video_path, tmp_path], timeout=120)
    adb(["shell", "cp", tmp_path, remote])
    adb(["shell", "rm", tmp_path])
    adb(["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote}"])
    time.sleep(3)
    print(f"  Pushed: {remote}")

    # Step 1: Force-close and launch Instagram
    print("\n" + "=" * 50)
    print("STEP 1: Launch Instagram")
    print("=" * 50)
    adb(["shell", "am", "force-stop", "com.instagram.android"])
    time.sleep(2)
    adb(["shell", "am", "start", "-n", "com.instagram.android/com.instagram.android.activity.MainTabActivity"])
    time.sleep(5)
    screenshot("debug_01_home.png")

    input("\n>>> Check debug_01_home.png — are we on IG home? Press Enter to continue...")

    # Step 2: Tap + button
    print("\n" + "=" * 50)
    print("STEP 2: Tap + (create new post)")
    print("=" * 50)
    tap(48, 104, "+ button (top-left)")
    time.sleep(4)
    screenshot("debug_02_create.png")

    input("\n>>> Check debug_02_create.png — did the creation screen open? Press Enter...")

    # Step 3: Tap REEL tab
    print("\n" + "=" * 50)
    print("STEP 3: Tap REEL tab")
    print("=" * 50)
    tap(800, 1860, "REEL tab")
    time.sleep(2)
    screenshot("debug_03_reel_tab.png")

    input("\n>>> Check debug_03_reel_tab.png — is REEL selected? Press Enter...")

    # Step 4: Select video thumbnail
    print("\n" + "=" * 50)
    print("STEP 4: Tap video thumbnail")
    print("=" * 50)
    tap(540, 200, "first video thumbnail")
    time.sleep(3)
    screenshot("debug_04_video_selected.png")

    input("\n>>> Check debug_04_video_selected.png — was video selected? Press Enter...")

    # Step 5: Tap Next (edit screen)
    print("\n" + "=" * 50)
    print("STEP 5: Tap Next (edit screen)")
    print("=" * 50)
    tap(982, 1876, "Next (bottom-right)")
    time.sleep(4)
    screenshot("debug_05_after_next_edit.png")

    input("\n>>> Check debug_05_after_next_edit.png — are we on caption screen? Press Enter...")

    # Step 6: Type caption
    print("\n" + "=" * 50)
    print("STEP 6: Tap caption field and type")
    print("=" * 50)
    tap(540, 829, "caption field")
    time.sleep(1)
    adb(["shell", "input", "text", "motion"])
    time.sleep(1)
    adb(["shell", "input", "keyevent", "111"])  # dismiss keyboard
    time.sleep(1)
    screenshot("debug_06_caption.png")

    input("\n>>> Check debug_06_caption.png — was caption entered? Press Enter...")

    # Step 7: Scroll down and tap Share/Next
    print("\n" + "=" * 50)
    print("STEP 7: Scroll down + tap Share")
    print("=" * 50)
    adb(["shell", "input", "swipe", "540", "1400", "540", "400", "400"])
    time.sleep(2)
    screenshot("debug_07_before_share.png")

    input("\n>>> Check debug_07_before_share.png — can you see Share button? Press Enter...")

    tap(802, 1836, "Share/Next button")
    time.sleep(3)
    screenshot("debug_08_after_share.png")

    input("\n>>> Check debug_08_after_share.png — was Share tapped? Press Enter...")

    # Step 8: Wait for upload
    print("\n" + "=" * 50)
    print("STEP 8: Waiting 45s for upload...")
    print("=" * 50)
    time.sleep(45)
    screenshot("debug_09_upload_done.png")

    print("\n>>> Check debug_09_upload_done.png — did the post upload?")
    print(f"\n[*] Debug complete. Check all debug_*.png files.")

    # Cleanup remote
    adb(["shell", "rm", remote])


if __name__ == "__main__":
    main()
