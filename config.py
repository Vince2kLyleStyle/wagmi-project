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
DAILY_MIN = 96         # 3 posts per 30 min × 16 active hours
DAILY_MAX = 96         # fixed — exactly 3 every 30 min
BATCH_SIZE = 3         # 3 videos per batch

# ─── Caption ──────────────────────────────────────────────────────
# These are VIRAL TRENDING TOPIC captions — not niche-specific.
# The trick: broad trending topics push posts to explore, regardless of video content.
# Rotate these so each post looks unique. Add new trending ones as you find them.
# Pro tip: grab captions from @memeyahu @twinkpotato @womenconsumer posts that went viral.
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
        "#UrbanDesign #EcoFuture #SmartCity #ClimateChange #GreenLiving"
    ),
    (
        "🇯🇵 Japan's work culture is unlike anything in the world.\n"
        "From 'Inemuri' — the practice of sleeping at work as a sign of dedication — "
        "to employees who haven't taken a day off in years. "
        "Japan ranks among the most productive nations on earth, yet burnout is at an all-time high. "
        "Is extreme dedication admirable or dangerous? 🤔\n"
        "#Japan #WorkCulture #Productivity #JapanLife #Tokyo #Hustle "
        "#WorkEthic #JapaneseLifestyle #Dedication #Mindset"
    ),
    (
        "🚢 The Titanic had a second ship — and almost nobody talks about it.\n"
        "The RMS Olympic was the Titanic's sister ship, nearly identical in every way. "
        "It sailed for 24 years without major incident. "
        "Some historians believe the ships were secretly swapped for insurance fraud. "
        "The Olympic was quietly scrapped in 1935. The mystery was never solved. 🧊\n"
        "#Titanic #History #Conspiracy #RMSOlympic #HistoryFacts "
        "#MindBlown #DidYouKnow #HistoryLovers #Mystery #Facts"
    ),
    (
        "🧠 Your brain makes 35,000 decisions every single day.\n"
        "Most of them happen without you even realizing it. "
        "The food you choose, the route you take, the words you say — "
        "almost all of it runs on autopilot. "
        "The people who master their habits master their life. "
        "Build the right systems and your brain does the rest. 💡\n"
        "#Psychology #Mindset #Brain #Habits #SelfImprovement "
        "#MentalHealth #Motivation #PersonalDevelopment #Success #GrowthMindset"
    ),
    (
        "🏛️ Rome wasn't built in a day — but it was burned in one.\n"
        "In 64 AD, a fire swept through Rome for six days, destroying 10 of its 14 districts. "
        "Emperor Nero reportedly played the lyre while watching the flames. "
        "Whether he started it or not, he used the disaster to build his golden palace. "
        "History's most powerful lesson: chaos always creates opportunity. 🔥\n"
        "#History #Rome #AncientRome #DidYouKnow #HistoryFacts "
        "#Nero #RomanEmpire #Facts #HistoryLovers #MindBlown"
    ),
]
USE_SAME_CAPTION = True  # picks one randomly per post — add more as you find trending ones

# ─── Emoji Overlay ───────────────────────────────────────────────
# Renders 🥀🥀😭😂 at middle-right of every video before uploading.
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

# ─── Auto-Prune / Surge — PERMANENTLY DISABLED ───────────────────────
# DO NOT RE-ENABLE. instagrapi view counts return 0 even on viral posts.
# Auto-prune deleted a 4M view post and 2 days of content. Never again.
# The check_and_prune() function is now a permanent no-op in fader_reels.py.
PRUNE_INTERVAL_BATCHES = 4

# ─── Timing (seconds) ──────────────────────────────────────────────
# Between videos in a batch
INTRA_BATCH_MIN = 20
INTRA_BATCH_MAX = 60

# Between batches — 3 posts every 30 min with slight jitter
INTER_BATCH_CENTER = 1800    # 30 min center
INTER_BATCH_SPREAD = 90      # slight jitter: ±1.5 min std-dev
INTER_BATCH_FLOOR = 1680     # never less than 28 min
INTER_BATCH_CEIL  = 1920     # never more than 32 min

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
