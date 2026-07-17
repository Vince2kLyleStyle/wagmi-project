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
VIDEO_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", os.getenv("NICHE", "hellokitty"))

# ─── Posting Limits ────────────────────────────────────────────────
# topcats (Nunu 2026-07-16): "I only truly need 50 ish a day, we can take
# hour breaks here and there." So: 3-post batches roughly hourly, with a
# jittered ~50/day ceiling. 18 active hours of hourly batches is ~54
# potential posts, so the cap lands first and the day ends with a natural
# break rather than a hard cut mid-stream. ~50/day also stretches the
# 348-clip bank to ~7 days instead of ~3.
DAILY_MIN = 48
DAILY_MAX = 52
BATCH_SIZE = 3         # 3 posts per batch, one batch every ~hour

# ─── Caption ──────────────────────────────────────────────────────
# ⚠️ TEMPORARY PLACEHOLDER — Nunu has NOT finalized the cats voice yet.
# Brand = WHOLESOME, targeting a WOMEN audience. These are safe, on-brand
# hashtag captions so nothing off-brand posts by accident. Replace once the
# voice/caption strategy is decided.
CAPTIONS_ENABLED = True

VIRAL_CAPTIONS = [
    "🐾🥺 #cat #cats #catsofinstagram #kitten #cute #catlover #meow #kitty #wholesome #hellokitty",
    "the cutest thing you'll see today 🥰 #cats #kitten #catsofinstagram #cute #catlover #wholesome #kitty #meow",
    "🥹💕 #cat #catsofinstagram #kittensofinstagram #cute #catlover #wholesome #hellokitty #meow #kitty",
]
USE_SAME_CAPTION = True  # picks one randomly per post — add more as you find trending ones

# ─── Emoji Overlay ───────────────────────────────────────────────
# Renders 🥀🥀😭😂 at middle-right of every video before uploading.
# Requires NotoColorEmoji font (sudo apt install fonts-noto-color-emoji)
EMOJI_OVERLAY_ENABLED = False
EMOJI_FONTSIZE = 75          # semi-small on a 1080p frame

# ─── Watermark ───────────────────────────────────────────────────
# Overlay text on each video before uploading
WATERMARK_ENABLED = False
WATERMARK_TEXT = "@juice.ysaladtoppers"
WATERMARK_FONTSIZE = 36
WATERMARK_OPACITY = 0.45          # subtle — visible but not distracting
WATERMARK_POSITION = "bottom_right"
WATERMARK_COLOR = "white"
WATERMARK_FONT = ""

# ─── Rest Window ─────────────────────────────────────────────────
# No posting during these hours (24h format). Bot sleeps and resumes after.
REST_WINDOW_ENABLED = True         # overnight break 2am-8am to stretch content + look human
REST_WINDOW_START = 2
REST_WINDOW_END = 8

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

# ─── Auto-Prune / Surge — PERMANENTLY DISABLED ───────────────────────
# DO NOT RE-ENABLE. instagrapi view counts return 0 even on viral posts.
# Auto-prune deleted a 4M view post and 2 days of content. Never again.
# The check_and_prune() function is now a permanent no-op in fader_reels.py.
PRUNE_INTERVAL_BATCHES = 4

# ─── Timing (seconds) ──────────────────────────────────────────────
# Between videos in a batch — quick stutter: 20-60s between the 3 posts.
INTRA_BATCH_MIN = 20
INTRA_BATCH_MAX = 60

# Between batches — ~60 min with jitter (55-65 min).
# topcats pace: 3 posts quickly, then wait ~an hour, repeat. Wide jitter
# (50-70 min) so the gaps look human rather than metronomic — Nunu is fine
# with breaks landing here and there.
INTER_BATCH_CENTER = 3600    # 60 min center
INTER_BATCH_SPREAD = 300     # jitter: ±5 min std-dev
INTER_BATCH_FLOOR  = 3000    # never less than 50 min
INTER_BATCH_CEIL   = 4200    # never more than 70 min

# ─── Throttle / Error Handling ─────────────────────────────────────
THROTTLE_SLEEP_MIN = 1800    # 30 min
THROTTLE_SLEEP_MAX = 7200    # 120 min

# ─── Thumbnail ─────────────────────────────────────────────────────
USE_FFMPEG_THUMBNAIL = True
FFMPEG_PATH = "ffmpeg"

# ─── Video Duration Filter ───────────────────────────────────────────
# Auto-delete videos longer than this (seconds). 0 = no limit.
MAX_VIDEO_DURATION = 15                # short clips rewatch more = explore push

# ─── Video Quality Filter ────────────────────────────────────────────
# Auto-delete videos below this resolution (height in pixels). 0 = no limit.
MIN_VIDEO_HEIGHT = 0

# ─── Logging ────────────────────────────────────────────────────────
SUCCESS_LOG = os.path.join(os.path.dirname(__file__), "success.txt")
# Keep the local file after posting. get_queue() already dedupes against
# SUCCESS_LOG, so deletion was never needed to avoid reposting — it only
# destroyed the bank irreversibly. Nothing is ever re-posted (Nunu 2026-07-16:
# "we cannot afford to post a recycled clip at all"), so the kept files are
# purely an audit trail of what went out.
DELETE_AFTER_UPLOAD = False
