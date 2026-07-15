"""
TikTok Scraper — Configuration
All tunables in one place.
"""

import os
from dotenv import load_dotenv
load_dotenv()

# ─── TikTok Search ────────────────────────────────────────────────────
KEYWORDS = [                           # Default keywords (used when no niche specified)
    "hello kitty", "cute cat meme", "popcat",
]

# ─── Niche Presets ────────────────────────────────────────────────────
# Each niche = a keyword group that maps to its own download folder.
# CATS FOREVER — "topcats online". Brand = WHOLESOME, targeting women + teens/
# young adults. Content MIX enforced by the poster: 50% hellokitty / 35% popgak
# (popcat + gak) / 15% catsother.  (see PRIORITY tiers in bluestacks_poster.py)
# Volume is biased toward hellokitty because it's consumed fastest at 50%.
NICHES = {
    # ── 50% — Hello Kitty / Sanrio (the star; needs the most volume) ─
    "hellokitty": [
        "hello kitty", "hello kitty edit", "hello kitty funny",
        "hello kitty aesthetic", "hello kitty cute", "hello kitty cosplay",
        "hello kitty makeup", "hello kitty room", "hello kitty outfit",
        "hello kitty nails", "hello kitty haul", "hello kitty plush",
        "hello kitty asmr", "hello kitty diy", "sanrio", "sanrio aesthetic",
        "kuromi", "my melody", "cinnamoroll",
        # breadth expansion (wholesome, women-targeted) — added to lift volume
        "hello kitty coquette", "hello kitty pink", "hello kitty decor",
        "hello kitty cake", "hello kitty birthday", "hello kitty art",
        "hello kitty drawing", "hello kitty wallpaper", "hello kitty collection",
        "hello kitty grwm", "hello kitty fit", "hello kitty unboxing",
        "hello kitty car", "hello kitty transformation", "sanrio haul",
        "sanrio collection", "kuromi cute", "my melody cute", "cinnamoroll cute",
        # fresh angles added 2026-07-15 (first 38 kw exhausted at 175 vids) —
        # wider Sanrio roster + lifestyle niches, all wholesome/women-teen targeted
        "pompompurin", "keroppi", "pochacco", "badtz maru", "hangyodon",
        "tuxedo sam", "sanrio characters", "sanrio blind box", "sanrio plushie",
        "hello kitty cafe", "sanrio cafe", "hello kitty boba", "hello kitty bakery",
        "hello kitty bento", "hello kitty crochet", "hello kitty amigurumi",
        "hello kitty phone case", "hello kitty skincare", "hello kitty perfume",
        "hello kitty desk setup", "sanrio room tour", "hello kitty island adventure",
        "hello kitty cat", "kuromi aesthetic",
        # ── BLITZ expansion 2026-07-15 (Nunu: hundreds on hundreds of HK shorts) ──
        # full Sanrio character roster
        "chococat", "little twin stars", "gudetama", "aggretsuko", "hello mimmy",
        "hangyodon cute", "pompompurin cute", "keroppi cute", "pochacco cute",
        # merch / haul / unboxing
        "sanrio surprise", "sanrio unboxing", "hello kitty shopping", "sanrio store",
        "hello kitty temu", "hello kitty shein", "hello kitty amazon finds",
        "hello kitty squishmallow", "hello kitty build a bear", "hello kitty keychain",
        # lifestyle / routines / setup
        "hello kitty morning routine", "hello kitty night routine",
        "hello kitty gaming setup", "hello kitty pc", "hello kitty keyboard",
        "hello kitty stationary", "hello kitty journal", "hello kitty sticker",
        # food
        "hello kitty cookies", "hello kitty lunch", "hello kitty starbucks",
        "hello kitty drink", "hello kitty mcdonalds", "hello kitty happy meal",
        # beauty
        "hello kitty press on", "hello kitty lip gloss", "hello kitty makeup collection",
        # fashion
        "hello kitty ootd", "hello kitty fit check", "hello kitty crocs",
        "hello kitty shoes", "hello kitty jewelry", "hello kitty bag",
        "hello kitty purse", "hello kitty accessories",
        # decor / room / car
        "hello kitty room makeover", "hello kitty bedroom", "hello kitty apartment",
        "hello kitty car accessories", "hello kitty jeep",
        # diy / craft
        "hello kitty painting", "hello kitty perler", "hello kitty clay",
        "hello kitty custom", "hello kitty tattoo",
        # aesthetic / seasonal / cosplay
        "hello kitty core", "sanrio core", "hello kitty pfp", "hello kitty halloween",
        "hello kitty christmas", "hello kitty valentine", "hello kitty 50th",
        "kuromi cosplay", "my melody cosplay", "sanrio cosplay",
    ],
    # ── 35% — Popcat + Gak (crypto meme-cats, kept cute not degen) ──
    "popgak": [
        "popcat", "pop cat meme", "popcat meme", "popcat edit",
        "popcat trend", "popcat funny", "popcat cute",
        "popcat song", "popcat original", "pop cat", "popcat cat",
        "gakster", "gak cat", "gakstercat", "gak meme", "gakster cat",
        "gakster funny", "gak cat meme",
        # ── fresh angles added 2026-07-15 (original 18 kw exhausted at 64 vids;
        #    progress tracker only scrapes NEW keywords, so these top up 64→150) ──
        "popcat mic", "popcat asmr", "popcat button", "popcat click",
        "popcat dance", "popcat compilation", "popcat plush", "popcat loud",
        "popcat reaction", "wide cat popcat", "popcat animation", "popcat game",
        "gakster edit", "gakster trend", "gakster dance", "gak cat funny",
        "gakster compilation", "gakster plush", "gak cat cute", "gakster meme",
        # round 2 (2026-07-15) — push 106→150
        "popcat toy", "popcat remix", "popcat cover", "popcat sticker",
        "popcat cat cute", "gak cat edit", "gakster cute", "gak cat asmr",
    ],
    # ── 15% — Other wholesome viral cats / characters ───────────────
    "catsother": [
        "cute cat meme", "funny cat", "silly cat", "cat vibing", "cat jam",
        "maxwell cat", "oiia cat", "spinning cat", "banana cat",
        "chipi chipi chapa chapa cat", "happy happy happy cat",
        "michi cat", "nyan cat", "bingus cat", "cute cat", "kitten",
        "cat compilation",
    ],
}
MAX_VIDEOS_PER_KEYWORD = 50            # Videos to collect per keyword
MIN_VIEWS = 50_000                     # lowered from 100k: hello kitty niche content is plentiful but lower-view; still a real quality floor (+ engagement-ratio filter)
MIN_LIKES = 0                          # Minimum like count (0 = no filter)
MIN_ENGAGEMENT_RATIO = 0.03            # Min likes/views ratio (3% = people actually cared)
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
