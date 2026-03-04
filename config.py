"""
Fader v2 — Configuration
All tunables in one place. Adjust to taste.
"""

import os

# ─── Account ────────────────────────────────────────────────────────
USERNAME = os.getenv("IG_USERNAME", "your_username")
PASSWORD = os.getenv("IG_PASSWORD", "your_password")
SESSION_DIR = os.path.join(os.path.dirname(__file__), "sessions")
SESSION_FILE = os.path.join(SESSION_DIR, f"{USERNAME}_session.json")

# ─── Video Source ───────────────────────────────────────────────────
VIDEO_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos")

# ─── Posting Limits ────────────────────────────────────────────────
DAILY_MIN = 8          # minimum posts per day
DAILY_MAX = 15         # hard cap per day
BATCH_SIZE = 3         # videos per mini-batch (like old Fader)

# ─── Timing (seconds) ──────────────────────────────────────────────
# Intra-batch delay (between videos inside one batch)
INTRA_BATCH_MIN = 40
INTRA_BATCH_MAX = 90

# Inter-batch delay (between batches) — Gaussian center + jitter
INTER_BATCH_CENTER = 3600    # 60 min center
INTER_BATCH_SPREAD = 1200    # ±20 min std-dev
INTER_BATCH_FLOOR = 2700     # never less than 45 min
INTER_BATCH_CEIL = 10800     # never more than 3 hours

# ─── Session Refresh ───────────────────────────────────────────────
REFRESH_EVERY_N_POSTS = 25   # re-login every N uploads

# ─── Warm-up Phase (start of each session) ─────────────────────────
WARMUP_MIN_SEC = 1800        # 30 min minimum warm-up
WARMUP_MAX_SEC = 3600        # 60 min maximum warm-up
WARMUP_STORIES_MIN = 5
WARMUP_STORIES_MAX = 15
WARMUP_LIKES_MIN = 3
WARMUP_LIKES_MAX = 8

# ─── Pre-upload Human Actions ──────────────────────────────────────
PRE_STORIES_MIN = 3
PRE_STORIES_MAX = 10
PRE_LIKES_MIN = 1
PRE_LIKES_MAX = 5

# ─── Post-upload Human Actions ─────────────────────────────────────
POST_LIKES_MIN = 0
POST_LIKES_MAX = 3

# ─── Throttle / Error Handling ─────────────────────────────────────
THROTTLE_SLEEP_MIN = 1800    # 30 min
THROTTLE_SLEEP_MAX = 7200    # 120 min
MAX_RETRIES = 1              # retry once after throttle

# ─── Thumbnail ─────────────────────────────────────────────────────
# Set to True if ffmpeg is installed — extracts random frame as thumbnail
USE_FFMPEG_THUMBNAIL = True
FFMPEG_PATH = "ffmpeg"       # or full path like r"C:\ffmpeg\bin\ffmpeg.exe"

# ─── Logging ────────────────────────────────────────────────────────
SUCCESS_LOG = os.path.join(os.path.dirname(__file__), "success.txt")
DELETE_AFTER_UPLOAD = True    # delete .mp4 after successful upload
