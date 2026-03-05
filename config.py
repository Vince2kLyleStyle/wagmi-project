"""
Fader v2 — Configuration
All tunables in one place.
"""

import os

# ─── Account ────────────────────────────────────────────────────────
USERNAME = os.getenv("IG_USERNAME", "dumbmoneyonsolana")
PASSWORD = os.getenv("IG_PASSWORD", "InstagramPassword1")
SESSION_DIR = os.path.join(os.path.dirname(__file__), "sessions")
SESSION_FILE = os.path.join(SESSION_DIR, f"{USERNAME}_session.json")

# ─── Video Source ───────────────────────────────────────────────────
VIDEO_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "trading")

# ─── Posting Limits ────────────────────────────────────────────────
DAILY_MIN = 30         # minimum posts per day
DAILY_MAX = 40         # hard cap per day (~2 per 20min × 12hrs = 72 max, stay under)
BATCH_SIZE = 2         # videos per mini-batch

# ─── Caption ──────────────────────────────────────────────────────
# 3 captions — one is randomly picked for each upload
VIRAL_CAPTIONS = [
    (
        "Follow for more 🔥💯\n"
        ".\n.\n.\n"
        "#viral #fyp #foryou #explore #trending #reels #reelsinstagram"
    ),
    (
        "You need to see this 👀🤯\n"
        ".\n.\n.\n"
        "#viral #fyp #foryou #explore #trending #reels #instareels"
    ),
    (
        "Save this for later 🚀💎\n"
        ".\n.\n.\n"
        "#viral #fyp #foryou #explore #trending #reels #viralreels"
    ),
]
USE_SAME_CAPTION = True

# ─── Timing (seconds) ──────────────────────────────────────────────
# Between videos in a batch
INTRA_BATCH_MIN = 30
INTRA_BATCH_MAX = 90

# Between batches (~20 min with jitter)
INTER_BATCH_CENTER = 1200    # 20 min center
INTER_BATCH_SPREAD = 300     # +/- 5 min std-dev (more natural)
INTER_BATCH_FLOOR = 720      # never less than 12 min
INTER_BATCH_CEIL = 1800      # never more than 30 min

# ─── Throttle / Error Handling ─────────────────────────────────────
THROTTLE_SLEEP_MIN = 1800    # 30 min
THROTTLE_SLEEP_MAX = 7200    # 120 min

# ─── Thumbnail ─────────────────────────────────────────────────────
USE_FFMPEG_THUMBNAIL = False
FFMPEG_PATH = "ffmpeg"

# ─── Logging ────────────────────────────────────────────────────────
SUCCESS_LOG = os.path.join(os.path.dirname(__file__), "success.txt")
DELETE_AFTER_UPLOAD = True
