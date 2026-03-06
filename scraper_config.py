"""
TikTok Scraper — Configuration
All tunables in one place.
"""

import os

# ─── TikTok Search ────────────────────────────────────────────────────
KEYWORDS = [                           # Default keywords (used when no niche specified)
    "trading memes", "forex memes", "stock market funny",
    "crypto memes", "gambling wins compilation",
    "hustle motivation", "sigma edit",
    "funny memes compilation", "viral memes today",
]

# ─── Niche Presets ────────────────────────────────────────────────────
# Each niche = a keyword group that maps to its own download folder
# and ultimately to its own Instagram account.
#
# STRATEGY: Focus on SHORT, VIRAL, MEME-WORTHY content that performs
# well on Instagram Explore. Avoid generic/long-form content.
# Keywords target compilations, edits, and meme formats.
NICHES = {
    "trading": [
        # Meme / viral formats
        "trading memes", "forex memes", "stock market memes",
        "crypto memes", "trader humor",
        # Viral edits
        "trading edit", "forex edit", "trading sigma",
        "stock market edit", "crypto edit",
        # Wins / losses (high engagement)
        "trading wins compilation", "trading fails",
        "forex gains", "crypto wins",
        # Lifestyle / aspirational (short-form)
        "trader lifestyle edit", "wolf of wall street edit",
        "day trader motivation", "TJR",
    ],
    "gambling": [
        # Viral wins
        "gambling wins compilation", "casino big win",
        "slot machine jackpot", "poker bluff",
        # Meme / humor
        "gambling memes", "casino memes", "sports betting memes",
        # Short clips
        "blackjack compilation", "roulette wins",
        "gambling edit", "casino edit",
        "sports betting wins",
    ],
    "hustle": [
        # Sigma / edit format (very viral on IG)
        "sigma male edit", "sigma edit", "grindset edit",
        "hustle edit", "motivation edit",
        # Meme / humor
        "hustle memes", "entrepreneur memes", "money memes",
        # Short motivational
        "millionaire mindset", "rich lifestyle edit",
        "success motivation short", "money motivation edit",
    ],
    "memes": [
        # Pure meme content (explore page gold)
        "funny memes compilation", "viral memes today",
        "tiktok memes compilation", "relatable memes",
        "gen z memes", "meme edit",
        "caught in 4k", "unexpected memes",
        "no context memes", "random memes compilation",
        "brainrot memes", "memes that hit different",
        "send this to your friend",
    ],
    "fitness": [
        # Gym memes and edits
        "gym memes", "gym edit", "gym motivation edit",
        "workout fails", "gym fails compilation",
        "bodybuilding edit", "fitness memes",
        "PR compilation", "gym transformation edit",
        "arm day edit", "chest day edit",
    ],
}

# ─── Content Quality Filters ─────────────────────────────────────────
MAX_VIDEOS_PER_KEYWORD = 30            # Lower than before — quality > quantity
MIN_VIEWS = 100_000                    # Only grab content with 100K+ views
MIN_LIKES = 0                          # Minimum like count (0 = no filter)
SCROLL_COUNT = 8                       # Times to scroll for more results
HEADLESS = True                        # Run browser without GUI

# ─── Video Duration Filter ───────────────────────────────────────────
# Instagram Reels sweet spot: 15-60 seconds
# Longer content gets less engagement on Reels
MAX_VIDEO_DURATION = 90                # Skip videos longer than 90 seconds
PREFER_SHORT = True                    # Prioritize <60s content in results

# ─── Telegram ─────────────────────────────────────────────────────────
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_BOT_USERNAME = "OFMTikTokBot"
TELEGRAM_SESSION_DIR = os.path.join(os.path.dirname(__file__), "sessions")
TELEGRAM_SESSION_NAME = "tiktok_scraper"
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE", "")  # Your phone number for first-time auth
TELEGRAM_SEND_DELAY_MIN = 3           # Seconds between messages
TELEGRAM_SEND_DELAY_MAX = 6

# ─── Telegram Notifications ──────────────────────────────────────────
# Send status updates to yourself or a group chat
TELEGRAM_NOTIFY_CHAT = os.getenv("TELEGRAM_NOTIFY_CHAT", "")  # Chat ID or @username for notifications
TELEGRAM_NOTIFY_ENABLED = bool(TELEGRAM_NOTIFY_CHAT)

# ─── Output ───────────────────────────────────────────────────────────
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "scraped_urls.txt")
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos")
TELEGRAM_DOWNLOAD_TIMEOUT = 120        # Seconds to wait for bot to reply with video
