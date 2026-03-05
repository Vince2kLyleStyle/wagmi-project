"""
Fader v2 — Configuration
All tunables in one place.
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
BATCH_SIZE = 3         # videos per mini-batch

# ─── Caption ──────────────────────────────────────────────────────
VIRAL_CAPTION = (
    "Follow for more 🔥💯\n"
    ".\n.\n.\n"
    "#viral #fyp #foryou #explore #trending #reels #reelsinstagram"
)
USE_SAME_CAPTION = True

# ─── Timing (seconds) ──────────────────────────────────────────────
# Between videos in a batch
INTRA_BATCH_MIN = 20
INTRA_BATCH_MAX = 60

# Between batches (~20 min with jitter)
INTER_BATCH_CENTER = 1200    # 20 min center
INTER_BATCH_SPREAD = 180     # +/- 3 min std-dev
INTER_BATCH_FLOOR = 900      # never less than 15 min
INTER_BATCH_CEIL = 1500      # never more than 25 min

# ─── Throttle / Error Handling ─────────────────────────────────────
THROTTLE_SLEEP_MIN = 1800    # 30 min
THROTTLE_SLEEP_MAX = 7200    # 120 min

# ─── Thumbnail ─────────────────────────────────────────────────────
USE_FFMPEG_THUMBNAIL = True
FFMPEG_PATH = "ffmpeg"

# ─── Logging ────────────────────────────────────────────────────────
SUCCESS_LOG = os.path.join(os.path.dirname(__file__), "success.txt")
DELETE_AFTER_UPLOAD = True
