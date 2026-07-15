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
    # ── 50% — Hello Kitty / Sanrio, MEME-FIRST ─────────────────────────
    # Nunu 2026-07-15: the page must be FUNNY / meme-adjacent to surface on
    # reels. DROP lifestyle/haul/GRWM/skincare/decor (that's the "tough"
    # off-brand content). Keep only meme + meme-adjacent formats. The old
    # lifestyle keywords are already marked done in hellokitty_progress.txt
    # so they won't re-scrape; these NEW meme keywords are what get pulled.
    "hellokitty": [
        # direct meme terms
        "hello kitty meme", "hello kitty memes", "hello kitty funny meme",
        "sanrio meme", "sanrio memes", "sanrio funny", "kuromi meme",
        "kuromi funny", "my melody meme", "my melody funny", "cinnamoroll meme",
        "cinnamoroll funny", "pompompurin meme", "keroppi meme",
        # relatable / mood / pov / be-like meme formats
        "hello kitty relatable", "hello kitty mood", "kuromi mood",
        "hello kitty pov", "kuromi pov", "hello kitty be like", "sanrio be like",
        "hello kitty me when", "kuromi me when", "hello kitty when",
        "hello kitty reaction", "kuromi reaction",
        # humor / cursed / slander meme culture
        "cursed hello kitty", "hello kitty cursed", "hello kitty shitpost",
        "hello kitty slander", "kuromi slander", "sanrio slander",
        "hello kitty derp", "hello kitty rage", "hello kitty crying meme",
        # funny edits / trends / audios
        "hello kitty capcut", "hello kitty funny edit", "hello kitty trend funny",
        "hello kitty cat meme", "hello kitty cat funny", "hello kitty comic",
        "hello kitty joke", "hello kitty humor", "sanrio comic",
        # core catch-alls (broad viral surface, already partly scraped)
        "hello kitty cute funny", "hello kitty viral", "hello kitty funny",
        # round 2 meme angles (2026-07-15) for post-wipe extension
        "sanrio pov", "my melody pov", "cinnamoroll pov", "sanrio reaction",
        "kuromi crashout", "hello kitty crashout", "kuromi vs my melody",
        "hello kitty text meme", "kuromi text", "sanrio characters funny",
        "hello kitty animation funny", "kuromi edit funny", "hello kitty gets",
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
    # ── 15% — Funny / meme cats (Nunu's core model: short funny cat clips) ─
    "catsother": [
        "cute cat meme", "funny cat", "silly cat", "cat vibing", "cat jam",
        "maxwell cat", "oiia cat", "spinning cat", "banana cat",
        "chipi chipi chapa chapa cat", "happy happy happy cat",
        "michi cat", "nyan cat", "bingus cat", "cute cat", "kitten",
        "cat compilation",
        # ── meme-format expansion 2026-07-15 (short funny clips w/ trending
        #    sounds + funny captions — the reference-page model) ──
        "cat meme", "cat memes", "funny cats", "funny cat videos",
        "silly cats", "derp cat", "grumpy cat", "cat fail", "cat reaction",
        "cat pov", "cat be like", "relatable cat", "cat mood", "cursed cat",
        "screaming cat", "cat scream", "talking cat", "cat zoomies",
        "polite cat", "huh cat", "coughing cat", "smiling cat cat",
        "standing cat", "shocked cat", "confused cat", "cat drama",
        "menace cat", "smudge cat", "keyboard cat", "cat trending sound",
        "cat yelling", "cat staring meme", "uh oh cat", "cat crashout",
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
