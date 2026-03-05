"""
TikTok Scraper — Configuration
All tunables in one place.
"""

import os

# ─── TikTok Search ────────────────────────────────────────────────────
KEYWORDS = [                           # Niche keywords to search
    "trading", "trading lifestyle", "trader motivation",
    "forex", "forex lifestyle", "forex gains",
    "stocks", "stock market", "stock trading",
    "crypto trading", "crypto gains", "bitcoin trading",
    "day trading", "day trader lifestyle",
    "gambling", "gambling wins", "casino wins",
    "wolf of wall street", "hustle motivation",
    "hustle", "TJR", "money motivation",
    "luxury lifestyle", "rich lifestyle",
]
MAX_VIDEOS_PER_KEYWORD = 50            # Videos to collect per keyword
MIN_VIEWS = 0                          # Minimum view count (0 = no filter)
MIN_LIKES = 0                          # Minimum like count (0 = no filter)
SCROLL_COUNT = 10                      # Times to scroll for more results
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
