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
# Captions — randomly picked for each upload
VIRAL_CAPTIONS = [
    "this is what motion looks like 🔥 #motion #sigma #grindset",
    "motion never stops 💰 #motion #money #hustle",
    "built different. #motion #mindset #success",
    "the grind is silent, the results are loud 🐺 #motion #wolfofwallstreet",
    "money talks, motion walks 💸 #motion #lifestyle",
    "no days off. #motion #grind #entrepreneur",
    "motion is a lifestyle, not a moment 🏆 #motion #winning",
    "they sleep, we grind 🌙 #motion #hustle #sigma",
    "this edit goes crazy 🔥 #motion #edit #viral",
    "cold. calculated. motion. ❄️ #motion #sigma #mindset",
]
USE_SAME_CAPTION = True

# ─── Watermark ───────────────────────────────────────────────────
# Overlay text on each video before uploading
WATERMARK_ENABLED = True
WATERMARK_TEXT = "$MOTION"
WATERMARK_FONTSIZE = 42
WATERMARK_OPACITY = 0.85
WATERMARK_POSITION = "bottom_right"   # top_left, top_right, bottom_left, bottom_right, center
WATERMARK_COLOR = "white"
WATERMARK_FONT = ""                   # leave empty for default, or path to .ttf file

# ─── Pinned Comment ──────────────────────────────────────────────
# Auto-comment and pin after each upload
PIN_COMMENT_ENABLED = True
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
USE_FFMPEG_THUMBNAIL = False
FFMPEG_PATH = "ffmpeg"

# ─── Logging ────────────────────────────────────────────────────────
SUCCESS_LOG = os.path.join(os.path.dirname(__file__), "success.txt")
DELETE_AFTER_UPLOAD = True
