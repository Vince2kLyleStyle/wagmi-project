"""
Fader v2 — Configuration
All tunables in one place.
"""

import os
from dotenv import load_dotenv
load_dotenv()

# ─── Account ────────────────────────────────────────────────────────
USERNAME = os.getenv("IG_USERNAME", "dumbmoneyonsolana")
PASSWORD = os.getenv("IG_PASSWORD", "InstagramPassword1")
SESSION_DIR = os.path.join(os.path.dirname(__file__), "sessions")
SESSION_FILE = os.path.join(SESSION_DIR, f"{USERNAME}_session.json")

# ─── Proxy ─────────────────────────────────────────────────────────
# Set via env var or directly here. Supports http/https/socks5.
# Examples:
#   http://user:pass@host:port
#   socks5://user:pass@host:port
PROXY = os.getenv("IG_PROXY", "")

# ─── Video Source ───────────────────────────────────────────────────
VIDEO_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "memes")

# ─── Posting Limits ────────────────────────────────────────────────
DAILY_MIN = 96         # ~2-3 per 30 min over 24h
DAILY_MAX = 144        # ~3 per 30 min over 24h
BATCH_SIZE = 3         # videos per mini-batch (2-3 posts per batch)

# ─── Caption ──────────────────────────────────────────────────────
# Exact caption — used for every upload
VIRAL_CAPTIONS = [
    (
        "#🇯🇵Japan is turning footsteps into electricity! "
        "Using piezoelectric tiles, every step you take generates a small amount of energy. "
        "Millions of steps together can power LED lights and displays in busy places like "
        "Shibuya Station. A brilliant way to create a sustainable and smart city • turning m"
    ),
]
USE_SAME_CAPTION = True

# ─── Timing (seconds) ──────────────────────────────────────────────
# Between videos in a batch
INTRA_BATCH_MIN = 20
INTRA_BATCH_MAX = 60

# Between batches (~30 min with jitter → 2-3 posts per 30 min)
INTER_BATCH_CENTER = 1800    # 30 min center
INTER_BATCH_SPREAD = 180     # +/- 3 min std-dev
INTER_BATCH_FLOOR = 1500     # never less than 25 min
INTER_BATCH_CEIL = 2100      # never more than 35 min

# ─── Throttle / Error Handling ─────────────────────────────────────
THROTTLE_SLEEP_MIN = 1800    # 30 min
THROTTLE_SLEEP_MAX = 7200    # 120 min

# ─── Thumbnail ─────────────────────────────────────────────────────
USE_FFMPEG_THUMBNAIL = False
FFMPEG_PATH = "ffmpeg"

# ─── Logging ────────────────────────────────────────────────────────
SUCCESS_LOG = os.path.join(os.path.dirname(__file__), "success.txt")
DELETE_AFTER_UPLOAD = True
