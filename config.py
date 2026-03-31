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

# ─── Emoji Overlay ───────────────────────────────────────────────
# Renders 🥀🥀😢😂 at middle-right of every video before uploading.
# Requires NotoColorEmoji font (sudo apt install fonts-noto-color-emoji)
EMOJI_OVERLAY_ENABLED = True
EMOJI_FONTSIZE = 75          # semi-small on a 1080p frame

# ─── Watermark ───────────────────────────────────────────────────
# Overlay text on each video before uploading
WATERMARK_ENABLED = True
WATERMARK_TEXT = "$MOTION"
WATERMARK_FONTSIZE = 36
WATERMARK_OPACITY = 0.45          # subtle — visible but not distracting
WATERMARK_POSITION = "bottom_right"
WATERMARK_COLOR = "white"
WATERMARK_FONT = ""

# ─── Rest Window ─────────────────────────────────────────────────
# No posting during these hours (24h format). Bot sleeps and resumes after.
REST_WINDOW_ENABLED = True
REST_WINDOW_START = 3              # 3am
REST_WINDOW_END = 9                # 9am — 6 hour rest covering the true dead zone

# ─── Active Window ───────────────────────────────────────────────
# Only post during these hours — peak engagement time.
# Outside this window the bot pauses until the window opens.
ACTIVE_WINDOW_ENABLED = False      # not needed — rest window handles dead hours

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

# ─── Auto-Prune Dead Posts ───────────────────────────────────────────
# After every N batches, fetch recent posts and delete any with < MIN_VIEWS
# that are older than GRACE_MINUTES (to let new posts warm up first).
PRUNE_ENABLED = False    # DISABLED — instagrapi view counts unreliable
PRUNE_INTERVAL_BATCHES = 4     # run prune every 4 batches (~2 hrs)
PRUNE_MIN_VIEWS = 10           # delete posts with fewer than this many views
PRUNE_GRACE_MINUTES = 180      # 3 hours — gives slow cookers time to pop

# ─── Surge Mode ──────────────────────────────────────────────────────
# When any recent post crosses SURGE_THRESHOLD views, cut inter-batch delay
# in half to flood the algorithm while we already have momentum.
# Surge stays active until the next check cycle finds no viral posts.
SURGE_ENABLED = False    # DISABLED — depends on same unreliable view counts
SURGE_THRESHOLD = 10_000       # views needed to trigger surge
SURGE_INTER_BATCH_CENTER = 900  # 15 min between batches (vs normal 30)
SURGE_INTER_BATCH_FLOOR = 750   # never less than 12.5 min
SURGE_INTER_BATCH_CEIL = 1050   # never more than 17.5 min

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
MAX_VIDEO_DURATION = 30                # short clips rewatch better = more explore push

# ─── Video Quality Filter ────────────────────────────────────────────
# Auto-delete videos below this resolution (height in pixels). 0 = no limit.
MIN_VIDEO_HEIGHT = 0

# ─── Logging ────────────────────────────────────────────────────────
SUCCESS_LOG = os.path.join(os.path.dirname(__file__), "success.txt")
DELETE_AFTER_UPLOAD = True
