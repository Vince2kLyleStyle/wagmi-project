#!/usr/bin/env python3
"""
Motion Bot — Pre-flight Check
==============================
Run this before starting the bot to verify everything is ready.
Prints [OK] or [!!] for each item and exits 0 if all clear, 1 if not.

Usage:
    python check.py
"""

import importlib
import json
import os
import shutil
import subprocess
import sys

PASS  = "[OK]"
FAIL  = "[!!]"
WARN  = "[~] "

ok    = True
warns = []

def check(label, passed, fix=None, warning=False):
    global ok
    if passed:
        print(f"  {PASS}  {label}")
    elif warning:
        print(f"  {WARN} {label}")
        if fix:
            print(f"         {fix}")
        warns.append(label)
    else:
        print(f"  {FAIL}  {label}")
        if fix:
            print(f"         FIX: {fix}")
        ok = False


print()
print("=" * 56)
print("  Motion Bot — Pre-flight Check")
print("=" * 56)
print()

# ── Python version ────────────────────────────────────────────────
print("  [ Python ]")
major, minor = sys.version_info[:2]
check(
    f"Python {major}.{minor} (need 3.10+)",
    major == 3 and minor >= 10,
    fix="Install Python 3.10 or newer from python.org"
)
print()

# ── Required packages ─────────────────────────────────────────────
print("  [ Packages ]")
packages = {
    "instagrapi":   "instagrapi",
    "PIL":          "Pillow",
    "dotenv":       "python-dotenv",
    "requests":     "requests",
    "telethon":     "telethon",
}
for import_name, pip_name in packages.items():
    try:
        importlib.import_module(import_name)
        check(f"{pip_name}", True)
    except ImportError:
        check(f"{pip_name}", False, fix=f"pip install {pip_name}")
print()

# ── ffmpeg ────────────────────────────────────────────────────────
print("  [ Tools ]")
ffmpeg_path = shutil.which("ffmpeg")
check(
    "ffmpeg on PATH",
    ffmpeg_path is not None,
    fix="Download from ffmpeg.org and add to PATH (or install via choco/winget)"
)
ffprobe_path = shutil.which("ffprobe")
check(
    "ffprobe on PATH",
    ffprobe_path is not None,
    fix="Comes with ffmpeg — make sure both are in the same folder on PATH"
)
adb_path = shutil.which("adb")
check(
    "adb on PATH (for BlueStacks)",
    adb_path is not None,
    fix="Optional: download Android Platform Tools from developer.android.com/tools",
    warning=True
)
print()

# ── Instagram credentials ─────────────────────────────────────────
print("  [ Instagram ]")

# Load .env if exists
env_file = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_file):
    from dotenv import load_dotenv
    load_dotenv(env_file)

ig_user = os.getenv("IG_USERNAME", "dumbmoneyonsolana")
ig_pass = os.getenv("IG_PASSWORD", "")

check(
    f"IG_USERNAME set (@{ig_user})",
    bool(ig_user),
    fix="Set IG_USERNAME in .env file"
)
check(
    "IG_PASSWORD set",
    bool(ig_pass) and ig_pass != "InstagramPassword1",
    fix='Add IG_PASSWORD=yourpassword to your .env file'
)

session_dir  = os.path.join(os.path.dirname(__file__), "sessions")
session_file = os.path.join(session_dir, f"{ig_user}_session.json")
check(
    "Instagram session saved (faster login)",
    os.path.exists(session_file),
    fix="Will be created automatically on first run — no action needed",
    warning=True
)
print()

# ── Telegram ──────────────────────────────────────────────────────
print("  [ Telegram ]")
tg_api_id   = os.getenv("TELEGRAM_API_ID", "")
tg_api_hash = os.getenv("TELEGRAM_API_HASH", "")

check(
    "TELEGRAM_API_ID set",
    bool(tg_api_id),
    fix="Get free API ID from my.telegram.org/apps → add to .env"
)
check(
    "TELEGRAM_API_HASH set",
    bool(tg_api_hash),
    fix="Get free API hash from my.telegram.org/apps → add to .env"
)

session_path = os.path.join(
    os.path.dirname(__file__), "sessions", "tiktok_scraper.session"
)
check(
    "Telegram session saved (login done)",
    os.path.exists(session_path),
    fix="Run setup_once.bat to log in to Telegram (one time only)"
)
print()

# ── BlueStacks token ──────────────────────────────────────────────
print("  [ BlueStacks (optional — better uploads) ]")
token_file = os.path.join(os.path.dirname(__file__), "bluestacks_token.json")
if os.path.exists(token_file):
    try:
        tok = json.load(open(token_file))
        has_session = bool(tok.get("sessionid"))
        has_user    = bool(tok.get("ds_user_id"))
        check(
            f"BlueStacks token loaded (user_id: {tok.get('ds_user_id','?')[:6]}***)",
            has_session and has_user,
            fix="Re-run extract_token.py with BlueStacks open"
        )
    except Exception:
        check("BlueStacks token readable", False,
              fix="Re-run extract_token.py")
else:
    check(
        "BlueStacks token (not set up yet)",
        False,
        fix="Install BlueStacks, log into Instagram, run extract_token.py",
        warning=True
    )
print()

# ── Video folder ──────────────────────────────────────────────────
print("  [ Content ]")
video_dir = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")
os.makedirs(video_dir, exist_ok=True)
videos = [f for f in os.listdir(video_dir) if f.endswith(".mp4")] if os.path.exists(video_dir) else []
check(
    f"Video folder exists ({video_dir})",
    True
)
check(
    f"Videos ready to post ({len(videos)} mp4s in queue)",
    len(videos) > 0,
    fix="Run: python instagram_scraper.py --amount 200",
    warning=len(videos) == 0
)
print()

# ── Summary ───────────────────────────────────────────────────────
print("=" * 56)
if ok and not warns:
    print("  READY — everything checks out. Run run.bat to start.")
elif ok:
    print(f"  READY (with {len(warns)} warning(s) — see above)")
    print("  Warnings won't stop the bot but should be fixed soon.")
else:
    print("  NOT READY — fix the [!!] items above, then re-run check.py")
print("=" * 56)
print()

sys.exit(0 if ok else 1)
