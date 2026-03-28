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
VIDEO_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", os.getenv("NICHE", "motion"))

# ─── Posting Limits ────────────────────────────────────────────────
DAILY_MIN = 96         # ~2-3 per 30 min over 24h
DAILY_MAX = 144        # ~3 per 30 min over 24h
BATCH_SIZE = 3         # videos per mini-batch (2-3 posts per batch)

# ─── Caption ──────────────────────────────────────────────────────
# Proven algorithm captions — these are what grab the IG algorithm.
# The Japan/Titanic ones are tested and work. Motion ones add brand.
# You'll paste the new one from the reel when you have it.
VIRAL_CAPTIONS = [
    (
        "🇳🇱 Netherlands is transforming its cities into climate-resilient hubs!\n"
        "In Rotterdam, innovative \"water plazas\" are being built to tackle flooding "
        "while doubling as public spaces. These smart urban designs store excess rainwater "
        "during storms and release it slowly—reducing pressure on drainage systems. "
        "Beyond flood control, green rooftops and urban gardens help cool the city, "
        "improve air quality, and boost biodiversity. A powerful example of how cities "
        "can adapt to climate change while enhancing everyday life 🌍💧🌿\n"
        "#Netherlands #Rotterdam #ClimateAction #GreenCity #Sustainability "
        "UrbanDesign EcoFuture SmartCity ClimateChange GreenLiving"
    ),
]
USE_SAME_CAPTION = True

# ─── Watermark ───────────────────────────────────────────────────
# Overlay text on each video before uploading
WATERMARK_ENABLED = False
WATERMARK_TEXT = "$MOTION"
WATERMARK_FONTSIZE = 42
WATERMARK_OPACITY = 0.85
WATERMARK_POSITION = "bottom_right"   # top_left, top_right, bottom_left, bottom_right, center
WATERMARK_COLOR = "white"
WATERMARK_FONT = ""                   # leave empty for default, or path to .ttf file

# ─── Pinned Comment ──────────────────────────────────────────────
# Auto-comment and pin after each upload
PIN_COMMENT_ENABLED = False
PIN_COMMENTS = [
    "Like and follow for motion 🔥💰",
    "Follow for more motion 🐺",
    "Motion never stops 💸 Follow for more",
    "Like + Follow = Motion 🏆",
    "This is motion. Follow for more 🔥",
]

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
USE_FFMPEG_THUMBNAIL = True
FFMPEG_PATH = "ffmpeg"

# ─── Video Duration Filter ───────────────────────────────────────────
# Auto-delete videos longer than this (seconds). 0 = no limit.
MAX_VIDEO_DURATION = 30

# ─── Logging ────────────────────────────────────────────────────────
SUCCESS_LOG = os.path.join(os.path.dirname(__file__), "success.txt")
DELETE_AFTER_UPLOAD = True
