"""
Fader v2 — Configuration
All tunables in one place.

Strategy: 3-reel bursts every ~30 minutes with the same niche caption.
Aggressive posting to hit FYP fast. Safety module only kicks in for
actual Instagram errors (rate limits, challenges) — not for cadence.
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
# Burst strategy: 3 reels per burst, every ~30 min
# ~3 per 30min × 18hrs = ~108/day potential, but cap to keep sane
DAILY_MIN = 70             # minimum posts per day
DAILY_MAX = 90             # hard cap per day
BATCH_SIZE = 3             # 3 reels per burst

# ─── Caption ──────────────────────────────────────────────────────
# USE_SAME_CAPTION = False → uses niche_config.py's per-niche captions
# Set to True + fill VIRAL_CAPTIONS to force one specific caption
USE_SAME_CAPTION = False

VIRAL_CAPTIONS = [
    # Only used if USE_SAME_CAPTION = True
    # Otherwise captions come from niche_config.py per niche
]

# ─── Timing (seconds) ──────────────────────────────────────────────
# Burst pattern: 3 reels with short gaps, then ~30 min wait
# Between videos WITHIN a burst (keep it quick but not instant)
INTRA_BATCH_MIN = 30         # 30s between reels in a burst
INTRA_BATCH_MAX = 90         # 90s max

# Between bursts (~30 min with jitter)
INTER_BATCH_CENTER = 1800    # 30 min center
INTER_BATCH_SPREAD = 300     # +/- 5 min std-dev
INTER_BATCH_FLOOR = 1500     # never less than 25 min
INTER_BATCH_CEIL = 2400      # never more than 40 min

# ─── Warm-up ──────────────────────────────────────────────────────
# Intensity: "light", "normal", "full"
# New/recently-flagged accounts should use "full"
WARMUP_INTENSITY = "normal"

# ─── Throttle / Error Handling ─────────────────────────────────────
# Only kicks in when IG actually rate-limits or challenges
THROTTLE_SLEEP_MIN = 1800    # 30 min
THROTTLE_SLEEP_MAX = 3600    # 60 min

# ─── Thumbnail ─────────────────────────────────────────────────────
USE_FFMPEG_THUMBNAIL = False
FFMPEG_PATH = "ffmpeg"

# ─── Logging ────────────────────────────────────────────────────────
SUCCESS_LOG = os.path.join(os.path.dirname(__file__), "success.txt")
DELETE_AFTER_UPLOAD = True
