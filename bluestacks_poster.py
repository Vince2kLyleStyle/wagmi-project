"""
BlueStacks Instagram Poster
============================
Posts Reels directly through the Instagram app inside BlueStacks
using ADB tap/swipe commands. No API calls whatsoever.
Instagram sees a real Android device doing normal human taps.

Flow per post:
  1. Push video to BlueStacks via adb (two-step: /data/local/tmp then cp)
  2. Trigger media scanner so Instagram gallery sees it
  3. Launch Instagram
  4. Navigate: + → REEL tab → select video → Next → dismiss popups → caption → Share
  5. Wait for upload confirmation
  6. Log success, delete local file
  7. Wait human-like delay, repeat

Requirements:
  - BlueStacks 5 open, Instagram logged into bot account
  - ADB enabled: BlueStacks Settings > Advanced > Android Debug Bridge > ON
  - adb.exe on Windows PATH (C:\\platform-tools\\)

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
import re
import subprocess
import sys
import time
from datetime import datetime

import captions as caption_gen
import config
from video_processor import process_video

# ─── Paths ────────────────────────────────────────────────────────
VIDEO_DIR    = config.VIDEO_DIR
SUCCESS_LOG  = config.SUCCESS_LOG
COORDS_FILE  = os.path.join(os.path.dirname(__file__), "bluestacks_coords.json")

# ─── Timing ───────────────────────────────────────────────────────
AFTER_PUSH_SLEEP     = 3      # seconds after adb push before opening IG
AFTER_LAUNCH_SLEEP   = 4      # seconds after opening Instagram
AFTER_TAP_SLEEP      = 1.5   # default between taps
UPLOAD_WAIT          = 60     # seconds to wait for upload to complete (re-encoded files need more time)
POST_INTERVAL_MIN    = 1680   # 28 min — slight jitter floor
POST_INTERVAL_MAX    = 1920   # 32 min — slight jitter ceiling

# ─── Default coordinates (BlueStacks 5, 1080x1920 portrait) ───────
# Calibrated via uiautomator dump on 2026-04-04.
# All values are absolute pixel coords for 1080x1920 screen.
DEFAULT_COORDS = {
    # "+" button — top-left of home screen (content-desc="Create a reel")
    "plus_button":         [48, 113],
    # "REEL" tab on the creation screen (POST/STORY/REEL/LIVE bottom tabs)
    "reel_tab":            [539, 1860],
    # First video thumbnail in gallery grid (center of second cell, after Camera)
    "first_video":         [540, 648],
    # "Next" button — edit screen (bottom-right purple button)
    "next_button_edit":    [982, 1876],
    # "Share" button — caption/share screen (bottom-right blue button)
    # NOTE: "Save draft" is at ~(210, 1890) — DO NOT hit that!
    "next_button_share":   [610, 1890],
    # Caption text field ("Write a caption and add hashtags...")
    "caption_field":       [540, 605],
    # "OK" on any confirmation dialog (popups like "New ways to reuse")
    "ok_button":           [540, 1701],
}


# ─── ADB helpers ──────────────────────────────────────────────────

ADB_SERIAL = None  # Set after connect_bluestacks() picks a device
_adb_consecutive_timeouts = 0  # Track consecutive ADB failures

def adb(cmd: list, timeout: int = 30) -> str:
    """Run an adb command. Returns stdout. Exits on connection failure."""
    global _adb_consecutive_timeouts
    try:
        prefix = ["adb"]
        if ADB_SERIAL:
            prefix = ["adb", "-s", ADB_SERIAL]
        # MSYS_NO_PATHCONV prevents Git Bash from mangling /sdcard/ paths
        env = os.environ.copy()
        env["MSYS_NO_PATHCONV"] = "1"
        result = subprocess.run(
            prefix + cmd,
            capture_output=True, text=True, timeout=timeout,
            env=env,
        )
        _adb_consecutive_timeouts = 0  # Reset on success
        return result.stdout.strip()
    except FileNotFoundError:
        print("[!!] adb not found -- add C:\\platform-tools\\ to Windows PATH")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        _adb_consecutive_timeouts += 1
        print(f"[!!] ADB command timed out ({_adb_consecutive_timeouts}x): {' '.join(cmd)}")
        return ""
    except Exception as e:
        print(f"[!!] ADB error: {e}")


def adb_is_healthy() -> bool:
    """Check if ADB is responsive. Returns False after 3+ consecutive timeouts."""
    if _adb_consecutive_timeouts >= 3:
        return False
    return True


def connect_bluestacks() -> bool:
    """Auto-connect to BlueStacks on common ports. Sets ADB_SERIAL."""
    global ADB_SERIAL

    # Check already-connected devices first
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10)
    lines = [l for l in result.stdout.splitlines() if "\tdevice" in l]

    # Prefer 127.0.0.1:PORT (BlueStacks), fall back to emulator-*
    for line in lines:
        serial = line.split("\t")[0]
        if serial.startswith("127.0.0.1"):
            ADB_SERIAL = serial
            print(f"[+] Using device: {ADB_SERIAL}")
            return True

    for line in lines:
        serial = line.split("\t")[0]
        if serial.startswith("emulator"):
            ADB_SERIAL = serial
            print(f"[+] Using device: {ADB_SERIAL}")
            return True

    # Try connecting on common BlueStacks ports
    print("[*] Connecting to BlueStacks...")
    for port in [5555, 5556, 5565, 5575]:
        out = subprocess.run(
            ["adb", "connect", f"127.0.0.1:{port}"],
            capture_output=True, text=True, timeout=10
        ).stdout
        if "connected" in out.lower():
            ADB_SERIAL = f"127.0.0.1:{port}"
            print(f"[+] Connected on port {port}")
            time.sleep(2)
            return True

    print("[!!] Could not connect to BlueStacks.")
    print("     Make sure BlueStacks is open and ADB is enabled.")
    print("     BlueStacks Settings > Advanced > Android Debug Bridge > ON")
    return False


def get_screen_size() -> tuple[int, int]:
    """Get BlueStacks screen dimensions (prefers override size)."""
    out = adb(["shell", "wm", "size"])
    # Output may have both "Physical size: 1920x1080" and "Override size: 1080x1920"
    # Prefer override (our portrait setting) over physical
    try:
        for line in reversed(out.splitlines()):
            if ":" in line:
                size_str = line.split(":")[-1].strip()
                w, h = size_str.split("x")
                return int(w), int(h)
    except Exception:
        pass
    print("[~] Could not detect screen size, defaulting to 1080x1920")
    return 1080, 1920


def ensure_portrait():
    """Set BlueStacks to portrait mode (1080x1920) if it isn't already."""
    w, h = get_screen_size()
    if w > h:
        print(f"[*] Screen is landscape ({w}x{h}), switching to portrait...")
        adb(["shell", "settings", "put", "system", "user_rotation", "0"])
        adb(["shell", "settings", "put", "system", "accelerometer_rotation", "0"])
        adb(["shell", "wm", "size", "1080x1920"])
        time.sleep(3)
        w, h = get_screen_size()
        print(f"[+] Screen now: {w}x{h}")
    return w, h


def tap(x_pct: float, y_pct: float, w: int, h: int, label: str = ""):
    """Tap at fractional screen coordinates."""
    x = int(w * x_pct)
    y = int(h * y_pct)
    if label:
        print(f"  [tap] {label} ({x}, {y})")
    adb(["shell", "input", "tap", str(x), str(y)])


def tap_absolute(x: int, y: int, label: str = ""):
    """Tap at absolute Android coordinates."""
    if label:
        print(f"  [tap] {label} ({x}, {y})")
    adb(["shell", "input", "tap", str(x), str(y)])


def find_element(text: str = None, resource_id: str = None,
                 content_desc: str = None) -> tuple[int, int] | None:
    """
    Use uiautomator dump to find a UI element by text, resource-id, or
    content-desc. Returns the center (x, y) in Android coordinates, or None.

    This is more reliable than fixed coordinates — works regardless of
    screen size, window position, or DPI scaling.
    """
    import re
    import xml.etree.ElementTree as ET

    # Dump current UI hierarchy to sdcard with a short timeout — dumps
    # can hang indefinitely if Android is in a weird state, which would
    # wedge the entire poster loop. 15s is plenty for a real dump.
    adb(["shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"], timeout=15)
    time.sleep(0.5)
    adb(["pull", "/sdcard/ui_dump.xml", "ui_dump.xml"], timeout=10)
    adb(["shell", "rm", "/sdcard/ui_dump.xml"], timeout=5)

    if not os.path.exists("ui_dump.xml"):
        return None

    try:
        tree = ET.parse("ui_dump.xml")
        root = tree.getroot()

        for node in root.iter("node"):
            match = False
            if text and node.get("text", "").lower() == text.lower():
                match = True
            if resource_id and resource_id in node.get("resource-id", ""):
                match = True
            if content_desc and content_desc.lower() in node.get("content-desc", "").lower():
                match = True

            if match:
                bounds = node.get("bounds", "")
                # bounds format: [left,top][right,bottom]
                nums = re.findall(r"\d+", bounds)
                if len(nums) == 4:
                    cx = (int(nums[0]) + int(nums[2])) // 2
                    cy = (int(nums[1]) + int(nums[3])) // 2
                    return cx, cy
    except Exception as e:
        print(f"  [ui] uiautomator parse error: {e}")
    finally:
        try:
            os.remove("ui_dump.xml")
        except OSError:
            pass

    return None


def tap_element(text: str = None, resource_id: str = None,
                content_desc: str = None,
                fallback_pct: list = None, w: int = 1080, h: int = 1920,
                label: str = "") -> bool:
    """
    Tap a UI element found via uiautomator, with percentage fallback.
    Returns True if tapped, False if not found and no fallback.
    """
    pos = find_element(text=text, resource_id=resource_id, content_desc=content_desc)
    if pos:
        tap_absolute(pos[0], pos[1], label or text or resource_id or "element")
        return True
    if fallback_pct:
        print(f"  [ui] element not found, using fallback coords for {label or text}")
        tap(fallback_pct[0], fallback_pct[1], w, h, label or text or "fallback")
        return True
    print(f"  [!!] Could not find element: text={text} id={resource_id}")
    return False


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


def paste_unicode_text(text: str) -> bool:
    """Paste Unicode text into the focused field via Windows clipboard + ADB PASTE.

    Works with emojis and any Unicode. BlueStacks auto-syncs the Windows
    clipboard to the Android clipboard, so Set-Clipboard on the host side
    makes the text available to the device. `adb shell input keyevent 279`
    (KEYCODE_PASTE) pastes at the current cursor position without needing
    PowerShell SendKeys (which would steal BlueStacks focus and pause
    the renderer). Caller must ensure the caption field is focused first.

    Retries once if the first paste leaves the caption field empty.
    Returns True if paste appeared successful, False otherwise.
    """
    if not text:
        return False
    caption_file = os.path.join(os.path.dirname(__file__), "_caption_tmp.txt")
    try:
        # Write caption bytes-for-bytes as UTF-8 with BOM so PowerShell
        # reads it unambiguously even on older systems that default to
        # ASCII/cp1252.
        with open(caption_file, "wb") as f:
            f.write(b"\xef\xbb\xbf" + text.encode("utf-8"))
        # `Get-Content -Raw -Encoding UTF8` handles newlines, emojis, all
        # Unicode correctly. BOM tells PowerShell to use UTF8.
        ps_cmd = (
            f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            f"$t = [IO.File]::ReadAllText('{caption_file}', "
            f"[System.Text.Encoding]::UTF8); "
            f"if ($t.Length -gt 0 -and $t[0] -eq [char]0xFEFF) {{ $t = $t.Substring(1) }}; "
            f"Set-Clipboard -Value $t"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, timeout=10
        )
    except Exception as e:
        print(f"  [!!] Could not set clipboard: {e}")
        return False
    finally:
        try:
            os.remove(caption_file)
        except OSError:
            pass

    # BlueStacks syncs Windows → Android clipboard on a polling cycle.
    # 0.5s is sometimes too fast; 1.5s is reliable.
    time.sleep(1.5)

    # KEYCODE_PASTE = 279 — pastes clipboard into focused field.
    adb(["shell", "input", "keyevent", "279"], timeout=5)
    time.sleep(1.5)

    # Verify: dump UI and check the caption field actually contains text.
    # IG shows the placeholder "Write a caption and add hashtags…" when
    # the field is empty. If we still see that, the paste didn't land.
    placeholder_still_there = find_element(text="Write a caption and add hashtags\u2026") is not None
    if placeholder_still_there:
        print(f"  [caption] Empty after paste — retrying in 2s")
        time.sleep(2)
        adb(["shell", "input", "keyevent", "279"], timeout=5)
        time.sleep(1.5)
        placeholder_still_there = find_element(text="Write a caption and add hashtags\u2026") is not None
        if placeholder_still_there:
            print(f"  [!!] Paste retry failed — caption still empty")
            return False
    print(f"  [caption] Pasted via clipboard ({len(text)} chars)")
    return True


def input_text_adb(text: str):
    """
    Paste text into the focused field via ADB clipboard broadcast.

    The old approach (adb shell input text) can only handle ASCII.
    This approach sets the Android clipboard via am broadcast and then
    pastes with Ctrl+V (KEYCODE_PASTE). Works with Japanese, emojis,
    and all Unicode.
    """
    if not text:
        return

    # Replace newlines with literal \n for the broadcast extra
    # (Android clipboard supports newlines)
    escaped = text.replace("'", "'\\''")  # escape single quotes for shell

    # Set clipboard via ADB broadcast using clipper-style approach
    # Write text to a temp file on device, then use am broadcast
    # to set clipboard content.
    import tempfile
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False,
                                       encoding='utf-8', dir='.')
    try:
        tmp.write(text)
        tmp.close()
        # Push text file to device
        adb(["push", tmp.name, "/data/local/tmp/caption.txt"], timeout=10)
        # Use input via clipboard: set clipboard and paste
        # Method: use 'am broadcast' with ADB_INPUT_TEXT or service call
        # Simplest reliable method: use 'input text' for ASCII parts,
        # and for non-ASCII, use PowerShell to set Windows clipboard
        # (BlueStacks shares clipboard with Windows host)
    finally:
        try:
            os.remove(tmp.name)
        except OSError:
            pass

    # Set Windows clipboard (shared with BlueStacks)
    try:
        import subprocess as _sp
        # Write caption to a temp file for PowerShell to read
        caption_file = os.path.join(os.path.dirname(__file__), "_caption_tmp.txt")
        with open(caption_file, "w", encoding="utf-8") as f:
            f.write(text)
        _sp.run(
            ["powershell", "-NoProfile", "-Command",
             f"Get-Content -Path '{caption_file}' -Raw | Set-Clipboard"],
            capture_output=True, timeout=10
        )
        os.remove(caption_file)
    except Exception as e:
        print(f"  [!!] Could not set clipboard: {e}")
        return

    time.sleep(0.5)

    # Paste via Windows SendKeys — the ONLY method that preserves
    # Japanese/Unicode in BlueStacks. Sequence: Ctrl+A (select all)
    # → Delete → Ctrl+V (paste). This ensures a clean field.
    ps_cmd = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; "
        "public class W { [DllImport(\"user32.dll\")] public static extern bool "
        "SetForegroundWindow(IntPtr hWnd); }'; "
        "$p = Get-Process HD-Player -ErrorAction SilentlyContinue; "
        "if ($p) { [W]::SetForegroundWindow($p.MainWindowHandle); "
        "Start-Sleep -Milliseconds 300; "
        "[System.Windows.Forms.SendKeys]::SendWait('^a'); "
        "Start-Sleep -Milliseconds 200; "
        "[System.Windows.Forms.SendKeys]::SendWait('{DELETE}'); "
        "Start-Sleep -Milliseconds 200; "
        "[System.Windows.Forms.SendKeys]::SendWait('^v') }"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_cmd],
        capture_output=True, timeout=10
    )
    time.sleep(1.0)
    print(f"  [caption] Pasted via SendKeys ({len(text)} chars)")


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
    Push video file to BlueStacks DCIM/Camera so Instagram gallery sees it.
    Uses two-step push (tmp → cp) because BlueStacks 5 fchown fails on
    direct adb push to /sdcard/.
    Returns the remote path on the Android filesystem.
    """
    filename = os.path.basename(local_path)
    tmp_path = f"/data/local/tmp/{filename}"
    remote   = f"/sdcard/DCIM/Camera/{filename}"

    # Ensure the folder exists
    adb(["shell", "mkdir", "-p", "/sdcard/DCIM/Camera"])

    print(f"  [push] {filename} -> BlueStacks...")

    # Step 1: push to /data/local/tmp (always writable)
    out = adb(["push", local_path, tmp_path], timeout=120)
    if "error" in out.lower() and "fchown" not in out.lower():
        print(f"  [!!] Push failed: {out}")
        return ""

    # Step 2: copy from tmp to sdcard gallery
    adb(["shell", "cp", tmp_path, remote])
    adb(["shell", "rm", tmp_path])

    # Verify the file landed. If ADB went offline mid-push, ls returns
    # garbage or empty — attempt to recover the connection before giving up.
    verify = adb(["shell", "ls", "-la", remote])
    if filename not in verify:
        # Check if ADB itself is healthy — a device-offline state
        # turns every subsequent adb call into a silent failure.
        dev_check = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, timeout=10
        ).stdout
        if "offline" in dev_check or "127.0.0.1:5555\tdevice" not in dev_check:
            print(f"  [!!] ADB device offline/missing — reconnecting...")
            subprocess.run(["adb", "disconnect", "127.0.0.1:5555"],
                           capture_output=True, timeout=10)
            time.sleep(1)
            subprocess.run(["adb", "connect", "127.0.0.1:5555"],
                           capture_output=True, timeout=10)
            time.sleep(3)
            # Retry the push from scratch.
            adb(["shell", "mkdir", "-p", "/sdcard/DCIM/Camera"])
            adb(["push", local_path, tmp_path], timeout=120)
            adb(["shell", "cp", tmp_path, remote])
            adb(["shell", "rm", tmp_path])
            verify = adb(["shell", "ls", "-la", remote])
            if filename not in verify:
                print(f"  [!!] File still not found after ADB reconnect")
                return ""
            print(f"  [push] Recovered after ADB reconnect")
        else:
            print(f"  [!!] File not found after push: {remote}")
            return ""

    # Trigger media scanner so Instagram gallery sees the video immediately.
    # Use both broadcast + cmd content scan (cmd works on more API levels).
    adb(["shell", "am", "broadcast",
         "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
         "-d", f"file://{remote}"])
    adb(["shell", "cmd", "media", "rescan", remote])
    time.sleep(AFTER_PUSH_SLEEP)
    print(f"  [push] Done")
    return remote


def ensure_thumbnail_on_device():
    """Push thumbnail.jpg to BlueStacks gallery if not already there."""
    thumb_local = os.path.join(os.path.dirname(__file__), "thumbnail.jpg")
    if not os.path.exists(thumb_local):
        return
    # Check if already on device
    check = adb(["shell", "ls", "/sdcard/DCIM/Camera/thumbnail.jpg"])
    if "thumbnail.jpg" in check:
        return
    # Push via two-step
    adb(["push", thumb_local, "/data/local/tmp/thumbnail.jpg"], timeout=30)
    adb(["shell", "cp", "/data/local/tmp/thumbnail.jpg", "/sdcard/DCIM/Camera/thumbnail.jpg"])
    adb(["shell", "rm", "/data/local/tmp/thumbnail.jpg"])
    adb(["shell", "am", "broadcast",
         "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
         "-d", "file:///sdcard/DCIM/Camera/thumbnail.jpg"])
    time.sleep(2)
    print("  [cover] Thumbnail pushed to BlueStacks gallery")


def focus_bluestacks_window():
    """Force the BlueStacks host window to the foreground.

    BlueStacks pauses its renderer when the host window loses focus —
    Android keeps running but the display freezes/goes black, which
    makes IG's share UI silently fail (taps land but nothing draws).

    Uses WScript.Shell's AppActivate in addition to SetForegroundWindow
    because Windows' focus-stealing-prevention blocks the Win32 API from
    non-foreground processes, but AppActivate isn't subject to that
    restriction. Calls SW_RESTORE first to un-minimize."""
    try:
        ps_cmd = (
            "Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; "
            "public class W { [DllImport(\"user32.dll\")] public static extern bool "
            "SetForegroundWindow(IntPtr h); "
            "[DllImport(\"user32.dll\")] public static extern bool ShowWindow(IntPtr h, int n); "
            "[DllImport(\"user32.dll\")] public static extern bool BringWindowToTop(IntPtr h); }'; "
            "$p = Get-Process HD-Player -ErrorAction SilentlyContinue; "
            "if ($p) { "
            "  [W]::ShowWindow($p.MainWindowHandle, 9); "
            "  [W]::BringWindowToTop($p.MainWindowHandle); "
            "  [W]::SetForegroundWindow($p.MainWindowHandle); "
            "  $w = New-Object -ComObject WScript.Shell; "
            "  $w.AppActivate('BlueStacks App Player') | Out-Null; "
            "}"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, timeout=10
        )
        time.sleep(1.5)
    except Exception as e:
        print(f"  [focus] could not foreground BlueStacks: {e}")


def is_screen_rendering() -> bool:
    """Check if BlueStacks' display is actually rendering (not paused).

    When the renderer is paused, screencap returns a pure-black frame
    even though Android says mAwake=true. Samples a screenshot and
    returns False if average brightness is below 3/255.
    """
    try:
        adb(["shell", "screencap", "-p", "/sdcard/_bright_check.png"], timeout=10)
        adb(["pull", "/sdcard/_bright_check.png", "_bright_check.png"], timeout=10)
        adb(["shell", "rm", "/sdcard/_bright_check.png"], timeout=5)
        from PIL import Image
        im = Image.open("_bright_check.png")
        w, h = im.size
        # Sample a 20x20 grid — much faster than full scan.
        total = 0
        count = 0
        for y in range(0, h, max(1, h // 20)):
            for x in range(0, w, max(1, w // 20)):
                px = im.getpixel((x, y))
                total += sum(px[:3])
                count += 3
        im.close()
        try:
            os.remove("_bright_check.png")
        except OSError:
            pass
        avg = total / count if count else 0
        return avg > 3
    except Exception as e:
        print(f"  [screen] check failed: {e}")
        return True  # assume OK on error — don't block the flow


def ensure_screen_rendering(max_attempts: int = 3) -> bool:
    """Re-focus BlueStacks until the screen stops being black.

    If three focus attempts don't revive rendering, restart HD-Player
    entirely. Returns True if screen is rendering by the time we return.
    """
    for attempt in range(max_attempts):
        if is_screen_rendering():
            return True
        print(f"  [screen] BLACK (attempt {attempt+1}/{max_attempts}) — refocusing")
        focus_bluestacks_window()
        time.sleep(2)
    # Last resort: restart HD-Player
    if not is_screen_rendering():
        print("  [screen] still black — restarting HD-Player")
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Stop-Process -Name HD-Player -Force -ErrorAction SilentlyContinue"],
                capture_output=True, timeout=10
            )
            time.sleep(3)
            subprocess.Popen(
                ["C:/Program Files/BlueStacks_nxt/HD-Player.exe", "--instance", "Pie64"],
                creationflags=0x00000008  # DETACHED_PROCESS
            )
            # Wait for boot
            for _ in range(40):
                time.sleep(3)
                out = adb(["shell", "getprop", "sys.boot_completed"], timeout=5)
                if "1" in out:
                    break
            time.sleep(5)
            connect_bluestacks()
            return is_screen_rendering()
        except Exception as e:
            print(f"  [screen] HD-Player restart failed: {e}")
            return False
    return True


def wake_screen():
    """Wake the BlueStacks display + dismiss any lockscreen.
    BlueStacks sometimes blanks the display after the inter-batch wait,
    which makes every subsequent ShareHandlerActivity intent fail. The
    real fix is force-foregrounding the host window (renderer pauses
    when unfocused), but we still send wake/menu keyevents and re-assert
    the never-sleep settings as belt-and-suspenders. All adb calls use
    a short timeout so a stuck ADB session doesn't burn 2 minutes here."""
    focus_bluestacks_window()
    adb(["shell", "input", "keyevent", "224"], timeout=5)
    time.sleep(0.3)
    adb(["shell", "input", "keyevent", "82"], timeout=5)
    time.sleep(0.3)
    adb(["shell", "settings", "put", "system", "screen_off_timeout", "2147483647"], timeout=5)
    adb(["shell", "svc", "power", "stayon", "true"], timeout=5)


def launch_instagram():
    """Launch Instagram to home screen."""
    wake_screen()
    print("  [app] Launching Instagram...")
    adb(["shell", "am", "start",
         "-n", "com.instagram.android/com.instagram.android.activity.MainTabActivity"])
    time.sleep(AFTER_LAUNCH_SLEEP)


def close_instagram():
    """Force-close Instagram (clean state for next post)."""
    adb(["shell", "am", "force-stop", "com.instagram.android"])
    time.sleep(1)


def dismiss_all_popups():
    """
    Keep tapping dismiss buttons until no more popups remain.
    Handles all known Instagram popups:
      - "New ways to reuse" -> OK
      - "Get App" (Edits promo) -> back button
      - "You're also sharing on Facebook" -> Got it
      - "Trial reels" -> Close
      - "Update on your original audio" -> Turn off and share / Share
    """
    for attempt in range(5):  # max 5 popup dismissals
        pos = find_element(text="Got it")
        if pos:
            tap_absolute(pos[0], pos[1], "dismiss popup (Got it)")
            human_delay(1.5)
            continue

        pos = find_element(text="Close")
        if pos:
            tap_absolute(pos[0], pos[1], "dismiss popup (Close)")
            human_delay(1.5)
            continue

        pos = find_element(text="Turn off and share")
        if pos:
            tap_absolute(pos[0], pos[1], "Turn off and share")
            human_delay(1.5)
            return  # this one actually posts — we're done

        pos = find_element(text="Get App")
        if pos:
            adb(["shell", "input", "keyevent", "4"])  # back button
            print("  [ui] dismissed Edits promo")
            human_delay(1.5)
            continue

        # "Rate Instagram" popup — tap "No, thanks"
        pos = find_element(text="No, thanks")
        if pos:
            tap_absolute(pos[0], pos[1], "dismiss popup (No, thanks)")
            human_delay(1.5)
            continue

        pos = find_element(text="Remind me later")
        if pos:
            tap_absolute(pos[0], pos[1], "dismiss popup (Remind me later)")
            human_delay(1.5)
            continue

        # "New ways to reuse" has OK button, but only dismiss if that
        # popup text is actually on screen (not the OK from other screens)
        pos = find_element(text="OK")
        if pos:
            reuse = find_element(text="New ways to reuse")
            if reuse:
                tap_absolute(pos[0], pos[1], "dismiss popup (OK)")
                human_delay(1.5)
                continue

        # No more popups found
        break


def action_blocked() -> bool:
    """True if Instagram is currently showing a rate-limit / block notice.

    The deleter has had this since the wipe; the poster never did, so a
    throttled account would just keep getting hammered. At ~6 posts/hr that
    is the difference between a temporary block and a dead account.
    """
    try:
        adb(["shell", "uiautomator", "dump", "/sdcard/block_dump.xml"], timeout=15)
        adb(["pull", "/sdcard/block_dump.xml", "block_dump.xml"], timeout=10)
        adb(["shell", "rm", "/sdcard/block_dump.xml"], timeout=10)
        with open("block_dump.xml", "r", encoding="utf-8", errors="replace") as f:
            low = f.read().lower()
    except Exception:
        return False
    finally:
        try:
            os.remove("block_dump.xml")
        except OSError:
            pass
    return any(s in low for s in (
        "action blocked", "try again later", "we restrict",
        "temporarily blocked", "we limit how often",
        "couldn't post", "couldn't share",
    ))


def read_active_handle(max_attempts: int = 3) -> str | None:
    """Navigate to the profile tab and read the handle from the action bar.
    Returns the handle, or None if it couldn't be read after retries.
    """
    import xml.etree.ElementTree as _ET
    for attempt in range(max_attempts):
        close_instagram()
        time.sleep(1)
        launch_instagram()
        time.sleep(6)
        tap_absolute(972, 1876, "profile tab")
        time.sleep(5)
        adb(["shell", "uiautomator", "dump", "/sdcard/handle_dump.xml"])
        time.sleep(0.5)
        adb(["pull", "/sdcard/handle_dump.xml", "handle_dump.xml"])
        adb(["shell", "rm", "/sdcard/handle_dump.xml"])
        try:
            tree = _ET.parse("handle_dump.xml")
            for node in tree.getroot().iter("node"):
                if node.get("resource-id", "").endswith("action_bar_title"):
                    handle = (node.get("text") or "").strip()
                    if handle:
                        return handle
        except Exception:
            pass
        finally:
            try:
                os.remove("handle_dump.xml")
            except OSError:
                pass
        print(f"  [guard] handle unreadable (attempt {attempt+1}/{max_attempts})")
    return None


def verify_account(expect_handle: str):
    """Abort unless the account active in BlueStacks is the expected one.

    Several IG accounts are logged into this emulator, including a personal
    one. Posting is irreversible and public, so an unreadable handle is
    treated as a failure, never as permission to proceed.
    """
    handle = read_active_handle()
    if handle is None:
        print(f"[ABORT] Could not read the active account handle. "
              f"Refusing to post blind.")
        sys.exit(1)
    if handle.lower() != expect_handle.lower():
        print(f"[ABORT] Active account is '{handle}', expected "
              f"'{expect_handle}'. Refusing to post to the wrong account.")
        sys.exit(1)
    print(f"[guard] Active account verified: {handle}")


def get_profile_post_count() -> int | None:
    """Navigate to the profile tab, read the post count, go back to home.
    Returns the integer count, or None if it couldn't be read.

    Always launches Instagram first — without this, the function would
    tap (972, 1876) on whatever app happens to be foregrounded (often
    Google Play after `close_instagram()` between posts).
    """
    import re as _re
    # Force-launch IG to a known state. close_instagram + launch ensures
    # the home feed is loaded so the bottom nav coords are valid.
    close_instagram()
    time.sleep(1)
    launch_instagram()
    time.sleep(6)
    # Tap profile tab — center of [864,1832][1080,1920] = (972, 1876).
    tap_absolute(972, 1876, "profile tab")
    time.sleep(5)
    # Tiny pull-to-refresh to force IG to re-query the server count.
    # IG caches the post count on the profile screen — without a refresh,
    # consecutive reads after posts return the stale count. Using a short
    # swipe (300px) so we don't scroll the count header off-screen.
    adb(["shell", "input", "swipe", "540", "400", "540", "700", "400"], timeout=5)
    time.sleep(4)
    # Dump UI and look for the posts count
    pos_data = find_element(text="posts")
    # The count is in a parent container with content-desc like "395posts"
    adb(["shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"])
    time.sleep(0.5)
    adb(["pull", "/sdcard/ui_dump.xml", "ui_dump.xml"])
    adb(["shell", "rm", "/sdcard/ui_dump.xml"])
    count = None
    try:
        import xml.etree.ElementTree as _ET
        tree = _ET.parse("ui_dump.xml")
        for node in tree.getroot().iter("node"):
            cd = node.get("content-desc", "")
            m = _re.match(r"(\d+)\s*posts?", cd)
            if m:
                count = int(m.group(1))
                break
            # Also try reading standalone number above "posts" text
            txt = node.get("text", "").strip()
            if txt.isdigit():
                # Check if next sibling or nearby node says "posts"
                # Heuristic: if y < 400 and x ~ 240-300, it's the posts count
                bounds = node.get("bounds", "")
                nums = _re.findall(r"\d+", bounds)
                if len(nums) == 4 and int(nums[1]) < 400 and int(nums[0]) < 350:
                    count = int(txt)
                    break
    except Exception:
        pass
    finally:
        try:
            os.remove("ui_dump.xml")
        except OSError:
            pass
    # Go back to home tab — center of [0,1832][216,1920] = (108, 1876)
    tap_absolute(108, 1876, "home tab")
    time.sleep(2)
    return count


def get_media_content_id(filename: str) -> str:
    """
    Query the Android media store for the content:// ID of a file in
    /sdcard/DCIM/Camera/ by filename.  Returns the ID string or "".
    """
    full_path = f"/sdcard/DCIM/Camera/{filename}"
    # Try exact path match first (most reliable), then LIKE fallback.
    queries = [
        f"content query --uri content://media/external/video/media "
        f"--projection _id --where \"_data='{full_path}'\"",
        f"content query --uri content://media/external/video/media "
        f"--projection _id --where \"_data LIKE '%{filename}'\"",
    ]
    for q in queries:
        out = adb(["shell", q])
        for line in out.splitlines():
            if "_id=" in line:
                try:
                    return line.split("_id=")[1].strip()
                except IndexError:
                    pass
    return ""


def wait_for_media_id(filename: str, max_wait: int = 20) -> str:
    """Poll for the content URI, re-triggering the media scanner each round.
    The scanner is async; freshly pushed files often need 5-10s to be indexed."""
    full_path = f"/sdcard/DCIM/Camera/{filename}"
    deadline = time.time() + max_wait
    attempt = 0
    while time.time() < deadline:
        media_id = get_media_content_id(filename)
        if media_id:
            return media_id
        attempt += 1
        # Re-trigger scan each iteration.
        adb(["shell", "am", "broadcast",
             "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
             "-d", f"file://{full_path}"])
        adb(["shell", "cmd", "media", "rescan", full_path])
        time.sleep(2)
    return ""


def post_reel(
    video_path: str,
    caption: str,
    coords: dict,
    w: int,
    h: int,
    dry_run: bool = False,
) -> bool:
    """
    Post one Reel via BlueStacks — STREAMLINED version.

    Uses timed taps at known coordinates instead of uiautomator for
    the main flow. uiautomator dumps are slow and hang, crashing the
    process. The only uiautomator usage is Share-enabled polling.

    Coordinates (1080x1920, calibrated 2026-04-10):
      Next (editor):    (982, 1876)
      Caption field:    (540, 829)
      OK (caption):     (1018, 111)
      Share:            (802, 1836)
    """
    import re as _re

    filename = os.path.basename(video_path)
    print(f"\n{'='*54}")
    print(f"  Posting: {filename}")
    print(f"{'='*54}")

    # ── Ensure BlueStacks is actually rendering ────────────────────
    # The host window can lose focus during inter-batch waits, which
    # puts BlueStacks into a paused state where the framebuffer is
    # pure black. ADB taps still register but nothing draws → IG
    # never shows the editor/share UI → every post fails silently.
    if not ensure_screen_rendering():
        print("  [!!] Screen is black, could not revive — aborting post")
        return False

    # ── Reject audio-only / unreadable files before doing anything ─
    # Some files in the memes source are MP3 wrapped in .mp4 containers.
    # They push fine but index as audio in the media store, so
    # content://media/external/video/media queries return no id and the
    # share intent can't find the file. Cheaper to quarantine now than
    # burn 30+ seconds on ffmpeg + share-intent timeouts.
    try:
        import video_processor as _vp
        if _vp._get_video_resolution(video_path) is None:
            print("  [reject] No video stream — moving to rejects/")
            reject_dir = os.path.join(os.path.dirname(VIDEO_DIR), "rejects")
            os.makedirs(reject_dir, exist_ok=True)
            try:
                os.rename(video_path, os.path.join(reject_dir, filename))
            except OSError:
                pass
            return False
    except Exception as e:
        print(f"  [~] Could not pre-check video ({e}) — continuing")

    # ── Process video: burn emoji overlay on top-center ───────────
    # Only run when overlays are enabled in config — otherwise post the raw file.
    if getattr(config, "EMOJI_OVERLAY_ENABLED", False) or getattr(config, "WATERMARK_ENABLED", False):
        print("  [proc] Burning emoji overlay...")
        proc_ok = process_video(video_path, video_path)
        if not proc_ok:
            print("  [~] Overlay failed — posting original")
    else:
        print("  [proc] Overlays disabled — posting raw video")

    # ── Clean device gallery (prevents stale media store entries
    # from making IG's Share button stay disabled) ─────────────────
    adb(["shell", "rm", "-f", "/sdcard/DCIM/Camera/*.mp4"])
    time.sleep(1)

    # ── Push video ────────────────────────────────────────────────
    remote = push_video_to_bluestacks(video_path)
    if not remote:
        return False

    if dry_run:
        print("  [dry-run] Skipping UI taps")
        return True

    # ── Get content URI (poll up to 20s, re-scanning each round) ──
    media_id = wait_for_media_id(filename, max_wait=20)
    if not media_id:
        print("  [!!] No content URI after 20s — aborting")
        return False

    content_uri = f"content://media/external/video/media/{media_id}"
    print(f"  [media] {content_uri}")

    # ── Launch IG ─────────────────────────────────────────────────
    close_instagram()
    time.sleep(1)
    launch_instagram()
    time.sleep(10)  # wait for IG to fully load

    # ── Send share intent ─────────────────────────────────────────
    print("  [app] Sending share intent...")
    adb([
        "shell", "am", "start",
        "-a", "android.intent.action.SEND",
        "-t", "video/mp4",
        "-n", "com.instagram.android/com.instagram.share.handleractivity.ShareHandlerActivity",
        "--eu", "android.intent.extra.STREAM", content_uri,
    ])
    time.sleep(12)  # wait for editor to load

    # ── Tap Next on editor ────────────────────────────────────────
    print("  [tap] Next (982, 1876)")
    tap_absolute(982, 1876, "Next")
    time.sleep(8)  # wait for share/caption screen

    # ── Paste caption via Windows clipboard + ADB PASTE ───────────
    # Unicode-safe (emojis work) and focus-safe (no SendKeys steal).
    # BlueStacks auto-syncs Windows clipboard → Android clipboard.
    if caption:
        print("  [caption] Tap caption field (540, 829)")
        tap_absolute(540, 829, "caption field")
        time.sleep(2.5)
        paste_unicode_text(caption)
        time.sleep(0.5)
        # Tap OK / done to dismiss the caption editor and return to share
        # screen. The OK button is in the top-right of the caption editor.
        tap_absolute(1018, 111, "caption OK")
        time.sleep(4)

    # ── Wait then tap Share ──────────────────────────────────────
    # 12s lets IG finish committing the caption + re-enable Share. The
    # first post after a cold IG launch was failing with 6s — Share stayed
    # disabled. 12s is enough even for slow starts.
    print("  [step10] Waiting 12s then tapping Share...")
    time.sleep(12)

    # On cold/new accounts Share stays disabled for a while after upload
    # (IG rate-limits new-account reel submissions). Poll the UI for
    # enabled state before tapping — tapping a disabled Share does nothing.
    def _share_enabled() -> bool:
        try:
            adb(["shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"], timeout=15)
            adb(["pull", "/sdcard/ui_dump.xml", "ui_dump.xml"], timeout=10)
            with open("ui_dump.xml", "r", encoding="utf-8") as _f:
                _xml = _f.read()
            import re as _re_share
            m = _re_share.search(r'content-desc="Share"[^/>]*enabled="(true|false)"', _xml)
            if m:
                return m.group(1) == "true"
        except Exception:
            pass
        return True  # unknown → assume enabled, avoid false stall
    waited = 0
    while waited < 90:
        if _share_enabled():
            break
        print(f"  [~] Share disabled — waiting 5s ({waited}s elapsed)")
        time.sleep(5)
        waited += 5

    tap_absolute(802, 1836, "Share")
    print("  [share] Tapped Share — waiting for upload...")
    time.sleep(UPLOAD_WAIT)

    # On brand-new / cold accounts IG shows an "About Reels" modal when you
    # tap Share; on those accounts (802, 1836) lands in Cancel (bottom) and
    # the real Share is the purple button at (540, 1748). Dismiss by
    # tapping the modal's Share when we detect it.
    if find_element(text="About Reels") is not None:
        print("  [~] About Reels modal present — tapping its Share button")
        tap_absolute(540, 1748, "Share (About Reels)")
        time.sleep(UPLOAD_WAIT)

    # ── Verify share landed (no longer on share screen) ──────────
    # After a successful share, IG navigates back to the home feed.
    # If Share was disabled or the upload failed, we'd still be on
    # the share screen with "Save draft" visible. If we catch that
    # state, retry the Share tap once — Share was probably briefly
    # disabled when we tapped, and is enabled by now.
    still_on_share = find_element(text="Save draft") is not None
    if still_on_share:
        print("  [~] Still on share screen — retrying Share tap")
        tap_absolute(802, 1836, "Share (retry)")
        time.sleep(UPLOAD_WAIT)
        if find_element(text="About Reels") is not None:
            print("  [~] About Reels modal on retry — tapping its Share")
            tap_absolute(540, 1748, "Share (About Reels retry)")
            time.sleep(UPLOAD_WAIT)
        still_on_share = find_element(text="Save draft") is not None
        if still_on_share:
            print("  [!!] Share retry also failed")
            return False
    print("  [verify] Left share screen (post submitted)")

    # ── Clean up remote video file ──────────────────────
    adb(["shell", "rm", remote])

    # Deliberately NOT calling close_instagram() here — the background
    # upload continues even after the share screen disappears, and killing
    # IG mid-upload drops the post silently. The next post's close+launch
    # at the start of its own post_reel call will reset state.

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
    """Build the post queue enforcing the topcats content MIX:
        50% hellokitty / 35% popgak (popcat+gak) / 15% catsother.

    Reads the three tier folders under tiktok_videos/, drops already-posted
    files, and weighted-interleaves so the posting stream holds the ratio
    (a tier that is behind its target share is picked next). Ratios overridable
    via env MIX_HELLOKITTY / MIX_POPGAK / MIX_CATSOTHER.
    """
    posted = load_posted()
    base = os.path.dirname(VIDEO_DIR)  # tiktok_videos/

    tiers = [
        ("hellokitty", float(os.getenv("MIX_HELLOKITTY", "0.50"))),
        ("popgak",     float(os.getenv("MIX_POPGAK",     "0.35"))),
        ("catsother",  float(os.getenv("MIX_CATSOTHER",  "0.15"))),
    ]

    pools, weights = {}, {}
    for name, w in tiers:
        d = os.path.join(base, name)
        vids = [v for v in sorted(glob.glob(os.path.join(d, "*.mp4")))
                if os.path.basename(v) not in posted]
        random.shuffle(vids)
        pools[name] = vids
        weights[name] = max(w, 1e-6)

    emitted = {name: 0 for name, _ in tiers}
    queue, total = [], sum(len(v) for v in pools.values())
    for _ in range(total):
        avail = [name for name, _ in tiers if pools[name]]
        if not avail:
            break
        # pick the tier most 'behind' its target share
        pick = min(avail, key=lambda n: emitted[n] / weights[n])
        queue.append(pools[pick].pop())
        emitted[pick] += 1
    return queue


def pick_caption() -> str:
    """topcats online caption strategy (Nunu 2026-07-15): each post caption is
    a LONG CAT FACT led by the fact, followed by #kitty + a rotating mix of
    cat/reach hashtags. Delegates to captions.generate_caption(), which never
    repeats an identical caption (large fact pool + randomized hashtags).
    Avoids posting the same fact back-to-back via a tiny state file. Falls back
    to config.VIRAL_CAPTIONS only if the generator is unavailable.
    """
    last_file = os.path.join(os.path.dirname(__file__), ".caption_last")
    try:
        last = ""
        if os.path.exists(last_file):
            with open(last_file, "r", encoding="utf-8") as f:
                last = f.read().strip()
        caption = caption_gen.generate_caption()
        # re-roll once if the fact (first line) repeats the previous post
        if caption.split("\n", 1)[0] == last:
            caption = caption_gen.generate_caption()
        with open(last_file, "w", encoding="utf-8") as f:
            f.write(caption.split("\n", 1)[0])
        return caption
    except Exception:  # noqa: BLE001 — never let caption gen crash a post
        pool = getattr(config, "VIRAL_CAPTIONS", None)
        return pool[0] if pool else "#kitty #cat #cats #catsofinstagram #reels #fyp"


def _OBSOLETE_pick_caption() -> str:
    """Return the fixed caption used for all posts."""
    return (
        "#\U0001f1f8\U0001f1ea \u30ad\u30eb\u30ca\uff08\u7279\u96c6\u7b2c2\u5f3e\uff09"
        "\u304c\u300c\u5317\u6975\u570f\u30bd\u30fc\u30e9\u30fc\u84c4\u96fb"
        "\u30a2\u30a4\u30b9\u30ea\u30f3\u30af\u300d\u3092\u5c0e\u5165\u3057\u307e\u3057\u305f\uff01\n"
        "\u3053\u308c\u306f1MW\u306e\u592a\u967d\u5149\u767a\u96fb\u30a2\u30ec\u30a4\u3068"
        "2MWh\u306e\u30d0\u30c3\u30c6\u30ea\u30fc\u30b7\u30b9\u30c6\u30e0\u3092\u5229\u7528"
        "\u3057\u3066\u3001\u30ad\u30eb\u30ca\u306b\u3042\u308b\u4e16\u754c\u6700\u5927\u306e"
        "\u30a2\u30a4\u30b9\u30ea\u30f3\u30af\u8907\u5408\u65bd\u8a2d\u306b\u96fb\u529b\u3092"
        "\u4f9b\u7d66\u3059\u308b\u3082\u306e\u3067\u3059\u3002\u590f\u306b\u84c4\u3048\u305f"
        "\u592a\u967d\u30a8\u30cd\u30eb\u30ae\u30fc\u3092\u4f7f\u3063\u3066\u6975\u591c\u306e"
        "\u671f\u9593\u306b\u6c37\u3092\u51cd\u3089\u305b\u308b\u3053\u3068\u3067\u3001"
        "\u30b9\u30a6\u30a7\u30fc\u30c7\u30f3\u6700\u5317\u306e\u90fd\u5e02\u304c\u4e16\u754c"
        "\u521d\u306e\u592a\u967d\u5149\u767a\u96fb\u306b\u3088\u308b\u30a6\u30a3\u30f3\u30bf\u30fc"
        "\u30b9\u30dd\u30fc\u30c4\u306e\u62e0\u70b9\u3068\u306a\u308a\u307e\u3057\u305f\uff01"
        "\u2600\ufe0f\U0001f50b\u26f8\ufe0f\u2744\ufe0f\u26a1\ufe0f\n"
        "\u3053\u306e\u5b63\u7bc0\u9593\u306e\u30a8\u30cd\u30eb\u30ae\u30fc\u8caf\u8535"
        "\u30bd\u30ea\u30e5\u30fc\u30b7\u30e7\u30f3\u306b\u3088\u308a\u3001\u6c37\u306e"
        "\u30e1\u30f3\u30c6\u30ca\u30f3\u30b9\u304b\u3089\u30c7\u30a3\u30fc\u30bc\u30eb"
        "\u71c3\u6599\u306e\u4f7f\u7528\u304c\u5b8c\u5168\u306b\u6392\u9664\u3055\u308c"
        "\u307e\u3057\u305f\u3002\n"
        "\u30ad\u30eb\u30ca\u306f\u5317\u6975\u570f\u306e\u767d\u591c\u306e\u592a\u967d"
        "\u5149\u3092\u30a2\u30a4\u30b9\u30ea\u30f3\u30af\u306e\u30a8\u30cd\u30eb\u30ae\u30fc"
        "\u3068\u3057\u3066\u84c4\u3048\u3001\u30b9\u30a6\u30a7\u30fc\u30c7\u30f3\u6700\u5317"
        "\u306e\u8857\u306e\u30a2\u30a4\u30b9\u30db\u30c3\u30b1\u30fc\u5834\u3092\u6975\u591c"
        "\u306e\u4e2d\u3067\u3082\u30af\u30ea\u30b9\u30bf\u30eb\u306e\u3088\u3046\u306b"
        "\u7f8e\u3057\u304f\u8f1d\u304b\u305b\u3066\u3044\u307e\u3059\u3002\U0001f1f8\U0001f1ea\n"
        "\u590f\u306e\u592a\u967d\u304c\u51ac\u306e\u6c37\u3092\u51cd\u3089\u305b\u308b"
        " \u2014 \u30ad\u30eb\u30ca\u306f\u3001\u5b63\u7bc0\u9593\u306e\u84c4\u96fb"
        "\u30bd\u30ea\u30e5\u30fc\u30b7\u30e7\u30f3\u304c\u5317\u6975\u570f\u306e"
        "\u30a6\u30a3\u30f3\u30bf\u30fc\u30b9\u30dd\u30fc\u30c4\u306e\u52d5\u529b\u6e90"
        "\u306b\u306a\u308a\u5f97\u308b\u3053\u3068\u3092\u8a3c\u660e\u3057\u3066\u3044"
        "\u307e\u3059\uff01 \u26f8\ufe0f\U0001f49a\n"
        "#Kiruna #Sweden #SolarStorage #IceRink ArcticEnergy WinterSports SeasonalBattery"
    )


# ─── Calibration mode ─────────────────────────────────────────────

def run_calibration(w: int, h: int):
    """
    Interactive calibration — takes screenshots and lets user
    update coordinates for their specific BlueStacks setup.
    """
    coords = load_coords()

    print()
    print("=" * 54)
    print("  BlueStacks Calibration Mode")
    print("  Takes screenshots so you can find the right coords")
    print("=" * 54)
    print()
    print("This will walk you through each tap point.")
    print("For each step:")
    print("  1. A screenshot is saved showing the current screen")
    print("  2. Open the screenshot to see where to tap")
    print("  3. Enter the X,Y pixel coords (or press Enter to keep current)")
    print()
    print(f"Screen size: {w}x{h}")
    print()

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
    parser.add_argument("--test",       action="store_true", help="Test ADB connection + screenshot, then exit")
    parser.add_argument("--once",       action="store_true", help="Post one video and exit")
    parser.add_argument("--dry-run",    action="store_true", help="Push video but skip UI taps")
    parser.add_argument("--daily-cap",  type=int, default=None, help="Max posts per day")
    parser.add_argument("--expect-handle", default="topcats.online",
                        help="Abort unless this IG account is active in BlueStacks")
    args = parser.parse_args()

    print()
    print("=" * 54)
    print("  BlueStacks Instagram Poster")
    print("  Real app - Real taps - Undetectable")
    print("=" * 54)
    print()

    # Connect ADB
    if not connect_bluestacks():
        sys.exit(1)

    # Ensure portrait mode and detect screen size
    w, h = ensure_portrait()
    print(f"[+] Screen: {w}x{h}")

    # Test mode — verify ADB is working, take screenshot, dump UI, exit
    if args.test or args.screenshot:
        print("[*] Testing ADB connection...")
        print(f"[+] Screen size: {w}x{h}")
        screenshot("bluestacks_screen.png")
        print("[*] Dumping UI elements...")
        pos = find_element(text="Next")
        if pos:
            print(f"[+] Found 'Next' button at {pos} -- uiautomator working")
        else:
            print("[~] 'Next' not visible (expected if not on that screen)")
        packages = adb(["shell", "pm", "list", "packages", "com.instagram"])
        if "com.instagram.android" in packages:
            print("[+] Instagram is installed")
        else:
            print("[!!] Instagram not found -- install it inside BlueStacks")
        print("\n[+] Test complete. Check bluestacks_screen.png to see current screen.")
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
    _ibf = getattr(config, "INTER_BATCH_FLOOR", 1680)
    _ibc = getattr(config, "INTER_BATCH_CEIL",  1920)
    print(f"[*] Batch size:   {getattr(config, 'BATCH_SIZE', 3)}")
    print(f"[*] Interval:     {_ibf//60}-{_ibc//60} min between batches\n")

    # Confirm we're driving the right account before anything gets published.
    verify_account(args.expect_handle)

    consecutive_blocks = 0

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

        # Post a batch of videos (3 per batch, ~30 min between batches)
        batch_size = getattr(config, "BATCH_SIZE", 3)
        intra_min  = getattr(config, "INTRA_BATCH_MIN", 20)
        intra_max  = getattr(config, "INTRA_BATCH_MAX", 60)
        inter_center = getattr(config, "INTER_BATCH_CENTER", 1800)
        inter_floor  = getattr(config, "INTER_BATCH_FLOOR", 1680)
        inter_ceil   = getattr(config, "INTER_BATCH_CEIL", 1920)

        # Read profile post count BEFORE the batch so we can verify
        # that IG actually shows N more posts after we're done.
        pre_count = get_profile_post_count()
        if pre_count is not None:
            print(f"\n[verify] Profile shows {pre_count} posts before batch")
        else:
            print("\n[verify] Could not read pre-batch post count (will skip delta check)")

        batch_posted = 0
        for i in range(batch_size):
            queue = get_queue()
            if not queue:
                print("[!!] No videos in queue.")
                print(f"     Run: python bluestacks_scraper.py --amount 50")
                break

            if posts_today >= daily_cap:
                break

            video_path = queue[0]
            caption    = pick_caption() if getattr(config, "CAPTIONS_ENABLED", True) else ""

            print(f"\n[{posts_today+1}/{daily_cap}] ({i+1}/{batch_size}) {os.path.basename(video_path)}")
            if caption:
                print(f"  Caption: {caption.encode('ascii', errors='replace').decode('ascii')[:80]}...")
            else:
                print(f"  Caption: (none)")

            success = post_reel(video_path, caption, coords, w, h, dry_run=args.dry_run)

            if not success and not args.dry_run and action_blocked():
                consecutive_blocks += 1
                backoff = min(3600 * consecutive_blocks, 6 * 3600)
                print(f"\n[BLOCK] Instagram is rate-limiting us "
                      f"(strike {consecutive_blocks}). Backing off "
                      f"{backoff//60} min instead of retrying.")
                if consecutive_blocks >= 3:
                    print("[BLOCK] 3 consecutive blocks — stopping. "
                          "Posting more now risks the account.")
                    sys.exit(1)
                time.sleep(backoff)
                break

            if success:
                consecutive_blocks = 0
                # A dry-run returns True without publishing anything. Logging
                # it would mark the video posted forever and silently drop it
                # from the bank, so only record real posts.
                if not args.dry_run:
                    log_success(os.path.basename(video_path))
                if config.DELETE_AFTER_UPLOAD and not args.dry_run:
                    try:
                        os.remove(video_path)
                        print(f"  [--] Deleted local file")
                    except OSError:
                        pass
                posts_today += 1
                batch_posted += 1

                if args.once:
                    print("\n[*] --once flag set, exiting.")
                    break

                # Short delay between posts in same batch
                if i < batch_size - 1:
                    intra_delay = random.randint(intra_min, intra_max)
                    print(f"  [batch] Next in batch in {intra_delay}s")
                    time.sleep(intra_delay)
            else:
                print(f"  [!!] Post failed -- recovering")
                close_instagram()
                # If ADB was timing out, try to reconnect
                if not adb_is_healthy():
                    print("  [!!] ADB unresponsive — reconnecting...")
                    global _adb_consecutive_timeouts
                    _adb_consecutive_timeouts = 0
                    connect_bluestacks()
                    time.sleep(10)
                else:
                    time.sleep(60)

        if args.once:
            break

        if not queue:
            print("     Waiting 10 minutes then checking again...")
            time.sleep(600)
            continue

        # Verify via profile post count delta — the truth source.
        post_count = get_profile_post_count()
        if pre_count is not None and post_count is not None:
            delta = post_count - pre_count
            mark = "OK" if delta >= batch_posted else "MISMATCH"
            print(f"[verify] Profile now shows {post_count} posts ({delta:+d}) — claimed {batch_posted} — {mark}")
            if delta < batch_posted:
                print(f"[!!] {batch_posted - delta} post(s) failed to appear on profile despite success log")
        elif post_count is not None:
            print(f"[verify] Profile shows {post_count} posts (no pre-baseline)")

        # Wait between batches (~30 min with jitter)
        inter_delay = random.randint(inter_floor, inter_ceil)
        next_time = (datetime.now() + __import__('datetime').timedelta(seconds=inter_delay)).strftime("%H:%M:%S")
        print(f"\n[*] Batch done ({batch_posted} posted). Next batch at ~{next_time} ({inter_delay//60}m)")
        time.sleep(inter_delay)


if __name__ == "__main__":
    main()
