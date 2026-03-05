"""
TikTok Scraper — Configuration
All tunables in one place.
"""

import os

# ─── TikTok Search ────────────────────────────────────────────────────
KEYWORDS = [                           # Niche keywords to search
    "trading", "gambling", "wolf of wall street",
    "forex", "stocks", "crypto trading", "day trading",
    "hustle", "TJR",
]
MAX_VIDEOS_PER_KEYWORD = 20            # Videos to collect per keyword
MIN_VIEWS = 100_000                    # Minimum view count (0 = no filter)
MIN_LIKES = 5_000                      # Minimum like count (0 = no filter)
SCROLL_COUNT = 5                       # Times to scroll for more results
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
