"""
Fader v2 — Configuration
All tunables in one place.

IMPORTANT: Daily limits are now managed by safety.py's progressive ramp-up
system. The values here are FALLBACK MAXIMUMS only. The safety module will
enforce lower limits for newer accounts automatically.
"""

import os

# ─── Account ────────────────────────────────────────────────────────
USERNAME = os.getenv("IG_USERNAME", "")
PASSWORD = os.getenv("IG_PASSWORD", "")
SESSION_DIR = os.path.join(os.path.dirname(__file__), "sessions")
SESSION_FILE = os.path.join(SESSION_DIR, f"{USERNAME}_session.json") if USERNAME else ""

# ─── Video Source ───────────────────────────────────────────────────
VIDEO_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "trading")

# ─── Niche (set by pipeline or manually) ────────────────────────────
CURRENT_NICHE = os.getenv("IG_NICHE", "")

# ─── Posting Limits ────────────────────────────────────────────────
# These are FALLBACK values. The safety module calculates the real
# daily limit based on account automation age.
# Old values (70-85/day) were WAY too aggressive and triggered bans.
DAILY_MIN = 8              # safe minimum for established accounts
DAILY_MAX = 20             # hard cap (safety module may set lower)
BATCH_SIZE = 1             # 1 video per batch — safer than 2

# ─── Caption ──────────────────────────────────────────────────────
# USE_SAME_CAPTION = False → uses niche_config.py's per-niche captions
# USE_SAME_CAPTION = True → uses VIRAL_CAPTIONS below (legacy mode)
USE_SAME_CAPTION = False

VIRAL_CAPTIONS = [
    # Legacy captions — only used if USE_SAME_CAPTION = True
    # Prefer niche_config.py captions instead
]

# ─── Timing (seconds) ──────────────────────────────────────────────
# These are FALLBACK values. The safety module provides dynamic gaps
# based on account age.
# Between videos in a batch (when BATCH_SIZE > 1)
INTRA_BATCH_MIN = 60
INTRA_BATCH_MAX = 180

# Between batches — now driven by safety.get_post_gap()
# These fallbacks are only used if safety module is unavailable
INTER_BATCH_CENTER = 2400    # 40 min center (was 25 — too fast)
INTER_BATCH_SPREAD = 600     # +/- 10 min std-dev
INTER_BATCH_FLOOR = 1200     # never less than 20 min
INTER_BATCH_CEIL = 3600      # never more than 60 min

# ─── Warm-up ──────────────────────────────────────────────────────
# Intensity: "light", "normal", "full"
# New/recently-flagged accounts should use "full"
WARMUP_INTENSITY = "normal"

# ─── Throttle / Error Handling ─────────────────────────────────────
# Now managed by safety.py's cooldown system
THROTTLE_SLEEP_MIN = 3600    # 60 min (was 30 — too aggressive)
THROTTLE_SLEEP_MAX = 10800   # 3 hours (was 2 hours)

# ─── Thumbnail ─────────────────────────────────────────────────────
USE_FFMPEG_THUMBNAIL = False
FFMPEG_PATH = "ffmpeg"

# ─── Logging ────────────────────────────────────────────────────────
SUCCESS_LOG = os.path.join(os.path.dirname(__file__), "success.txt")
DELETE_AFTER_UPLOAD = True
