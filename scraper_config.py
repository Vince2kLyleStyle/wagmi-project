"""
TikTok Scraper — Configuration
All tunables in one place.
"""

import os
from dotenv import load_dotenv
load_dotenv()

# ─── TikTok Search ────────────────────────────────────────────────────
KEYWORDS = [                           # Default keywords (used when no niche specified)
    "TJR", "TJR edit", "wolf of wall street meme",
    "sigma grindset", "hustle meme", "crypto meme",
]

# ─── Niche Presets ────────────────────────────────────────────────────
# Each niche = a keyword group that maps to its own download folder
# and ultimately to its own Instagram account.
# Add new niches here — the pipeline and scraper will auto-detect them.
NICHES = {
    "memes": [
        # Proven performers — your best content
        "TJR", "wolf of wall street edit",
        # Broad discovery — let engagement ratio do the filtering
        "funny meme compilation", "meme that made me cry laughing",
        "try not to laugh", "funniest video ever",
        "perfectly cut screams", "unexpected ending",
    ],
}

# ─── Viral Caption Search ────────────────────────────────────────────
# Search TikTok for videos using this exact viral caption.
# Videos with the same caption are pre-filtered quality content.
VIRAL_CAPTION_SEARCH = (
    "Japan is turning footsteps into electricity "
    "Using piezoelectric tiles every step you take generates a small amount of energy"
)
# How much of the caption must match to count (0.0-1.0)
CAPTION_MATCH_THRESHOLD = 0.35

# ─── Bulk Mode: Multiple Viral Captions ──────────────────────────────
# Accounts that use these captions post the type of content we want.
# Phase 1: Search captions → discover accounts
# Phase 2: Scrape each account's full profile → get ALL their videos
# Add more captions here to discover more accounts and get more content.
VIRAL_CAPTIONS = [
    # Japan piezoelectric tiles
    "Japan is turning footsteps into electricity "
    "Using piezoelectric tiles every step you take generates a small amount of energy",

    # Titanic Korean caption
    "1997년 개봉한 영화 Titanic은 잭과 로즈의 운명적인 사랑을 통해 비극 속에서도 오래 남는 감정의 깊이를 보여주는 작품입니다",
]

# Max videos to grab per discovered account
MAX_VIDEOS_PER_ACCOUNT = 30
MAX_VIDEOS_PER_KEYWORD = 200            # Videos to collect per keyword
MIN_VIEWS = 100_000                    # Minimum view count (lowered to catch more caption copies)
MIN_LIKES = 0                          # Minimum like count (0 = no filter)
MIN_ENGAGEMENT_RATIO = 0.05            # Min likes/views ratio (5% = genuinely good)
SCROLL_COUNT = 25                      # Times to scroll for more results
HEADLESS = True                        # Run browser without GUI

# ─── Telegram ─────────────────────────────────────────────────────────
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_BOT_USERNAME = "OFMTikTokBot"
TELEGRAM_SESSION_DIR = os.path.join(os.path.dirname(__file__), "sessions")
TELEGRAM_SESSION_NAME = "tiktok_scraper"
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE", "")  # Your phone number for first-time auth
TELEGRAM_SEND_DELAY_MIN = 3           # Seconds between messages
TELEGRAM_SEND_DELAY_MAX = 6

# ─── Output ───────────────────────────────────────────────────────────
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "scraped_urls.txt")
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos")
TELEGRAM_DOWNLOAD_TIMEOUT = 120        # Seconds to wait for bot to reply with video
