"""
TikTok Scraper — Configuration
All tunables in one place.
"""

import os
from dotenv import load_dotenv
load_dotenv()

# ─── TikTok Search ────────────────────────────────────────────────────
KEYWORDS = [                           # Default keywords (used when no niche specified)
    "shitpost", "brainrot", "low quality meme",
    "deep fried meme", "cursed video", "unhinged meme",
    "perfectly cut screams", "meme that goes hard",
    "earrape meme", "dank meme compilation",
]

# ─── Niche Presets ────────────────────────────────────────────────────
# Each niche = a keyword group that maps to its own download folder
# and ultimately to its own Instagram account.
# Add new niches here — the pipeline and scraper will auto-detect them.
NICHES = {
    "memes": [
        "shitpost", "brainrot",
        "low quality meme", "deep fried meme",
        "cursed video", "unhinged meme",
        "perfectly cut screams", "meme that goes hard",
        "earrape meme", "dank meme compilation",
    ],
    "ai_brainrot": [
        # Core AI food / fruit terms
        "ai generated fruit", "ai fruit", "ai fruits",
        "ai food", "ai generated food", "ai cooking",
        "ai cake", "ai candy", "ai chocolate",
        "ai fruit cutting", "ai fruit satisfying",
        "ai satisfying food", "ai food asmr",
        "ai dessert", "ai ice cream", "ai sushi",
        "ai pizza", "ai burger",
        # AI brainrot general
        "ai brainrot", "ai generated brainrot",
        "ai cursed", "ai cursed video",
        "ai satisfying", "ai oddly satisfying",
        "ai satisfying video", "ai asmr",
        # Specific viral formats
        "ai watermelon", "ai mango", "ai strawberry",
        "ai grape", "ai orange fruit",
        "ai jelly fruit", "ai gummy fruit",
        "ai fruit jelly", "ai rainbow food",
        "ai miniature food", "ai tiny food",
        "ai giant fruit", "ai realistic fruit",
        # Engagement bait formats
        "ai food tiktok", "ai fruit tiktok",
        "ai generated satisfying", "ai art food",
        "ai food compilation", "ai fruit compilation",
        "this ai fruit looks real", "ai food that looks real",
        # Adjacent trending
        "ai slime food", "ai soap cutting",
        "ai kinetic sand food", "ai candy factory",
        "ai chocolate factory", "ai fruit factory",
    ],
    "facts_brainrot": [
        # AI narrated facts / did you know style
        "ai facts", "ai did you know", "ai narrated facts",
        "ai voice facts", "ai fun facts", "ai history facts",
        "ai science facts", "ai country facts", "ai japan facts",
        "ai world facts", "ai mind blowing facts",
        # Specific viral formats
        "japan turning footsteps into electricity",
        "piezoelectric tiles", "ai technology facts",
        "ai inventions", "ai future technology",
        "countries doing insane things", "japan innovation",
        "things you didn't know existed",
        "ai generated documentary", "ai narrated",
        # Korean/multilingual AI caption style
        "ai voiceover facts", "robot voice facts",
        "text to speech facts", "tts brainrot facts",
        "ai slideshow facts", "ai facts compilation",
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

    # AI fruit / food viral captions
    "This fruit doesn't exist it was made by AI",
    "AI generated food that looks more real than real food",
    "POV AI makes your favorite fruit",
    "AI fruit is taking over tiktok",
    "Would you eat this AI generated food",
    "This AI fruit is so satisfying to watch",
    "AI made this and it looks delicious",
    "Can you tell this food was made by AI",
    "AI is getting too good at making food",
    "The most satisfying AI food video you'll ever see",
]

# Max videos to grab per discovered account
MAX_VIDEOS_PER_ACCOUNT = 30
MAX_VIDEOS_PER_KEYWORD = 200            # Videos to collect per keyword
MIN_VIEWS = 10_000                     # Lowered for AI content (newer = fewer views)
MIN_LIKES = 0                          # Minimum like count (0 = no filter)
MIN_ENGAGEMENT_RATIO = 0.02            # Min likes/views ratio (2% = cast widest net)
MIN_INTERACTIONS = 10_000              # Minimum total interactions (likes + comments + shares)
SCROLL_COUNT = 40                      # More scrolling = more videos found
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
