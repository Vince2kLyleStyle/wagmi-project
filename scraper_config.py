"""
TikTok Scraper — Configuration
All tunables in one place.
"""

import os
from dotenv import load_dotenv
load_dotenv()

# ─── TikTok Search ────────────────────────────────────────────────────
KEYWORDS = [                           # Default keywords (used when no niche specified)
    "funny tiktok", "funny reels", "trending meme",
    "meme compilation", "try not to laugh",
    "perfectly cut screams", "funny skit",
    "shitpost", "brainrot", "dank meme",
]

# ─── Niche Presets ────────────────────────────────────────────────────
# Each niche = a keyword group that maps to its own download folder
# and ultimately to its own Instagram account.
# Add new niches here — the pipeline and scraper will auto-detect them.
NICHES = {
    "memes": [
        # Core funny / trending
        "funny tiktok", "funny reels", "funny meme",
        "trending meme", "viral meme", "meme compilation",
        "funny video compilation", "try not to laugh",
        "meme that goes hard", "funniest tiktoks",
        # Specific viral formats
        "perfectly cut screams", "unexpected ending",
        "wait for it funny", "caught in 4k",
        "bro what", "nah this is crazy",
        "real life npc", "skit comedy",
        "funny skit", "comedy tiktok",
        # Brainrot / shitpost (still gold)
        "shitpost", "brainrot", "unhinged meme",
        "cursed video", "dank meme",
        "low quality meme", "deep fried meme",
        # Relatable / trending humor
        "relatable meme", "gen z humor",
        "when you realize", "pov funny",
        "bro really said", "this guy is a legend",
        "hood memes", "funny fails",
        "instant regret", "karma funny",
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
    "minecraft_parkour": [
        # Core format
        "minecraft parkour", "minecraft parkour storytime",
        "parkour storytime", "minecraft story time",
        "minecraft parkour story", "storytime minecraft",
        "minecraft storytelling", "storytime parkour",
        # Variations
        "minecraft parkour asmr", "minecraft parkour satisfying",
        "minecraft storytime tiktok", "reddit stories minecraft",
        "reddit storytime minecraft", "scary story minecraft parkour",
        "confession minecraft parkour", "aita minecraft parkour",
        "minecraft background storytime", "subway surfers storytime",
        "subway surfers parkour", "satisfying gameplay storytime",
        # Related gameplay background formats
        "storytime gameplay", "reddit story gameplay",
        "tiktok storytime gameplay", "viral storytime minecraft",
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
    "motion": [
        # ── FUNNY movie edits (these are your bangers) ──
        "wolf of wall street funny", "wolf of wall street meme",
        "scarface funny", "scarface meme", "tony montana funny",
        "american psycho funny", "patrick bateman meme", "patrick bateman funny",
        "peaky blinders funny", "thomas shelby funny", "thomas shelby meme",
        "breaking bad funny", "walter white meme", "walter white funny",
        "heisenberg meme", "heisenberg funny",
        "godfather funny", "godfather meme",
        "goodfellas funny", "goodfellas meme",
        "fight club funny", "tyler durden meme", "tyler durden funny",
        "joker funny", "joker meme", "joker funny scene",
        "batman funny", "batman meme",
        "john wick funny", "john wick meme",
        "suits funny", "harvey specter funny", "harvey specter meme",
        "money heist funny", "professor funny",
        "narcos funny", "narcos meme",
        "django funny", "pulp fiction funny",
        "taxi driver meme", "nightcrawler meme",
        "ozark funny", "power funny",
        "top boy funny", "top boy meme",
        "succession funny", "logan roy meme",

        # ── Sigma / grindset MEMES (funny ones, not serious) ──
        "sigma meme", "sigma male meme", "sigma funny",
        "sigma rule funny", "sigma male funny",
        "gigachad meme", "gigachad funny",
        "sigma edit funny", "sigma brainrot",
        "villain arc meme", "villain arc funny",
        "lone wolf meme",

        # ── Money MEMES (funny, not motivational speeches) ──
        "money meme", "money meme funny", "money meme edit",
        "counting money meme", "money flex funny",
        "rich people funny", "rich meme",
        "hood money meme", "hood funny money",
        "gangster meme", "gangster funny",
        "mafia meme", "mafia funny",
        "bag secured meme", "money printer meme",
        "grindset meme", "hustle meme",

        # ── Movie edits (cold/hard, not boring motivation) ──
        "wolf of wall street edit", "scarface edit",
        "american psycho edit", "peaky blinders edit",
        "breaking bad edit", "godfather edit",
        "goodfellas edit", "fight club edit",
        "joker edit", "batman edit", "dark knight edit",
        "john wick edit", "suits edit",
        "money heist edit", "narcos edit",
        "django unchained edit", "pulp fiction edit",
        "taxi driver edit", "nightcrawler edit",
        "top boy edit", "power edit",
        "succession edit", "ozark edit",
        "drive movie edit", "blade runner edit",
        "casino edit", "departed edit",
        "gangster movie edit", "mafia edit",

        # ── Viral edit formats (short, punchy) ──
        "phonk edit", "phonk edit funny",
        "hard edit", "edit that goes hard",
        "this edit goes crazy", "cold edit",
        "movie scene meme", "funny movie edit",
        "funny villain edit", "funny movie scene",
        "movie meme compilation", "cinema meme",
        "film meme edit", "movie edit viral",
    ],
}

# ─── Viral Caption Search ────────────────────────────────────────────
VIRAL_CAPTION_SEARCH = "this edit goes hard"
CAPTION_MATCH_THRESHOLD = 0.35

# ─── Bulk Mode: Multiple Viral Captions ──────────────────────────────
# Search these captions to find motion/grindset accounts and videos.
VIRAL_CAPTIONS = [
    # ── Funny movie edit captions (these find the right accounts) ──
    "this edit goes hard",
    "wolf of wall street will never get old",
    "patrick bateman is actually insane",
    "thomas shelby funny moments",
    "walter white was actually unhinged",
    "jordan belfort was actually crazy",
    "scarface tony montana best scenes",
    "the joker was right about everything",
    "harvey specter best moments",
    "peaky blinders best scenes",

    # ── Sigma / meme edit captions ──
    "sigma male edit that goes hard",
    "he was built different",
    "bro activated his villain arc",
    "villain arc activated",
    "this sigma edit is insane",
    "gigachad energy",
    "most cold blooded movie scene",
    "coldest movie moment",

    # ── Funny / viral format captions ──
    "this edit is insane",
    "hardest edit on tiktok",
    "phonk edits hit different at night",
    "nah this edit goes crazy",
    "im dead this is too accurate",
    "the way this edit hits",
    "bro this scene was actually cold",
    "who made this edit im crying",
    "funniest movie scene edit",
    "movie memes that hit different",
]

# ─── Niche Relevance Filter ──────────────────────────────────────────
# Block videos whose captions contain these terms (case-insensitive).
# This stops thirst traps, OF promos, and other off-niche garbage from
# being downloaded even when scraped from an otherwise-good account.
CAPTION_BLOCKLIST = [
    # Thirst trap / suggestive
    "thirst trap", "thirsttrap", "baddie", "baddies",
    "hot girl", "hotgirl", "body check", "bodycheck",
    "bikini", "lingerie", "onlyfans", "of link", "link in bio",
    "dm me", "dm for", "come find me", "spicy content",
    "18+", "nsfw", "uncensored", "explicit",
    "grwm date", "date night outfit", "fit check sexy",
    "thot", "thotiana", "freaky", "no bra",
    # Adult / OF promo
    "fansly", "fanvue", "manyvids", "cam girl", "camgirl",
    "sugar daddy", "sugar baby", "findom",
    # Romance / relationship bait
    "pov he", "pov she", "pov your crush", "pov boyfriend",
    "couple goals", "relationship goals",
    "kiss cam", "makeout", "making out",
    # Dance / model content (not memes)
    "dance challenge", "dance trend", "model walk",
    "runway walk", "slow mo walk",
    # Low quality / off-brand for motion
    "unboxing", "haul", "what i eat in a day",
    "get ready with me", "grwm", "skincare routine",
    "makeup tutorial", "cooking recipe", "food review",
    "asmr eating", "mukbang",
    "anime edit", "kpop edit", "kpop fancam",
    "fan edit", "fanfic", "wattpad",
    "sad edit", "crying edit", "depression",
    "self harm", "mental health vent",
    # Boring motivational speeches (not funny, not edits)
    "motivational speech", "morning routine motivation",
    "5am routine", "wake up at 5", "daily routine",
    "self improvement journey", "day in my life",
    "how to be successful", "10 rules of success",
    "motivational podcast", "podcast clip motivation",
    "life advice", "life lessons", "storytime",
    # Talking head / guru / lecture content
    "watch this before", "listen to this",
    "i made my first million", "how i got rich",
    "passive income", "dropshipping", "affiliate marketing",
    "real estate investing", "property investing",
    "financial freedom", "side hustle ideas",
    "money tips", "investing tips", "stock tips",
    "trading strategy", "trading tutorial",
    "how to invest", "how to trade",
    "motivation speech compilation", "best motivation",
    "powerful motivation", "never give up motivation",
]

# Require at least ONE of these terms in the caption for niche relevance.
# Leave empty to skip positive matching (only blocklist filtering).
# These are checked per-niche — set in NICHE_REQUIRED_TERMS below.
NICHE_REQUIRED_TERMS = {
    "memes": [],  # memes are broad — blocklist is enough (funny content comes in many forms)
    "ai_brainrot": [
        "ai", "artificial", "generated", "neural",
        "fruit", "food", "satisfying", "asmr",
        "cake", "candy", "chocolate", "jelly",
        "brainrot", "brain rot",
    ],
    "minecraft_parkour": [
        "minecraft", "parkour", "storytime", "story time",
        "subway surfers", "gameplay", "reddit",
        "confession", "aita", "scary story",
    ],
    "facts_brainrot": [
        "fact", "facts", "did you know", "mind blow",
        "country", "japan", "piezoelectric", "invention",
        "science", "history", "technology", "ai",
        "brainrot", "brain rot", "narrated",
    ],
    "motion": [
        "money", "cash", "rich", "wealth", "million", "billion",
        "hustle", "grind", "success", "motivation", "sigma",
        "wolf", "belfort", "scarface", "montana", "bateman",
        "shelby", "peaky", "breaking bad", "heisenberg",
        "godfather", "corleone", "gangster", "boss",
        "edit", "phonk", "motion", "movement", "level up",
        "trading", "forex", "crypto", "profit", "wins",
        "entrepreneur", "business", "empire", "luxury",
        "villain", "lone wolf", "alpha", "gigachad",
        "cold", "hard", "goes crazy", "pushing",
    ],
}

# Max videos to grab per discovered account
MAX_VIDEOS_PER_ACCOUNT = 30
MAX_VIDEOS_PER_KEYWORD = 200            # Videos to collect per keyword
MIN_VIEWS = 50_000                     # Higher bar — motion niche has tons of viral content
MIN_LIKES = 1_000                      # Minimum like count — filters out dead content
MIN_ENGAGEMENT_RATIO = 0.04            # Min likes/views ratio (4% = funny content gets higher engagement)
MIN_INTERACTIONS = 30_000              # Minimum total interactions — funny clips get shared heavily
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
