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
        # ── Movie edits (the bread and butter) ──
        "wolf of wall street edit", "wolf of wall street sigma",
        "jordan belfort edit", "jordan belfort motivation",
        "scarface edit", "scarface tony montana",
        "tony montana edit", "tony montana sigma",
        "american psycho edit", "patrick bateman edit",
        "peaky blinders edit", "thomas shelby edit",
        "thomas shelby sigma", "tommy shelby motivation",
        "breaking bad edit", "walter white sigma",
        "walter white edit", "heisenberg edit",
        "godfather edit", "michael corleone edit",
        "goodfellas edit", "gangster movie edit",
        # ── More movie / TV edits ──
        "fight club edit", "tyler durden edit", "tyler durden sigma",
        "joker edit", "joker sigma", "joker motivation",
        "batman edit", "batman sigma", "dark knight rises edit",
        "john wick edit", "john wick sigma",
        "suits edit", "harvey specter edit", "harvey specter sigma",
        "succession edit", "logan roy edit",
        "taxi driver edit", "travis bickle edit",
        "casino edit", "casino movie edit",
        "gangs of new york edit", "there will be blood edit",
        "money heist edit", "professor money heist",
        "ozark edit", "marty byrde edit",
        "power edit", "ghost power edit",
        "top boy edit", "top boy sigma",
        "drive movie edit", "driver gosling edit",
        "nightcrawler edit", "lou bloom edit",
        "wall street movie edit", "gordon gekko edit",
        "the departed edit", "departed sigma",
        "no country for old men edit", "anton chigurh edit",
        "django unchained edit", "django sigma",
        "pulp fiction edit", "pulp fiction sigma",
        "blade runner edit", "ryan gosling edit sigma",
        # ── Money / success / hustle ──
        "money motivation", "money edit", "counting money",
        "cash counting", "money aesthetic", "money lifestyle",
        "rich lifestyle", "luxury lifestyle edit",
        "billionaire lifestyle", "millionaire motivation",
        "success motivation", "success edit",
        "hustle motivation", "grind motivation",
        "grindset", "entrepreneur motivation",
        "business motivation", "trading success",
        "trading wins", "forex wins", "crypto wins",
        # ── Sigma / mindset edits ──
        "sigma male edit", "sigma edit", "sigma grindset",
        "sigma rule", "gigachad edit", "gigachad motivation",
        "dark knight edit", "villain arc edit",
        "villain motivation", "lone wolf edit",
        "lone wolf motivation", "alpha mindset",
        # ── Motion / movement ──
        "motion edit", "motion lifestyle", "motion money",
        "pushing packs", "street motion", "get money edit",
        "on the move motivation", "movement edit",
        "making moves", "level up edit",
        # ── Meme / gangster money crossover ──
        "hood money meme", "gangster meme money",
        "money meme edit", "money meme compilation",
        "trap money edit", "trap lifestyle edit",
        "hood motivation", "street money motivation",
        "gangster lifestyle edit", "mafia edit",
        "narcos edit", "pablo escobar edit",
        "money printer", "money flex edit",
        "bag secured", "securing the bag edit",
        "get rich edit", "money dance",
        # ── Viral edit formats ──
        "after effects edit", "phonk edit",
        "phonk motivation", "phonk money",
        "4k edit motivation", "cinematic edit sigma",
        "movie scene edit", "movie motivation edit",
        "hard edit", "edit that goes hard",
        "this edit goes crazy", "cold edit",
        # ── Funny motion / money humor (these go viral) ──
        "wolf of wall street funny", "scarface funny scene",
        "peaky blinders funny", "breaking bad funny",
        "american psycho funny", "patrick bateman meme",
        "sigma male funny", "sigma meme", "gigachad meme",
        "jordan belfort funny", "money meme funny",
        "gangster movie funny scene", "funny movie edit",
        "funny villain edit", "funny sigma edit",
        "movie scene meme", "hood funny money",
        "counting money funny", "rich people funny",
        "hustle meme funny", "grindset meme",
        "thomas shelby funny", "walter white meme",
        "joker funny scene", "batman funny edit",
        "funny money flex", "money humor edit",
    ],
}

# ─── Viral Caption Search ────────────────────────────────────────────
VIRAL_CAPTION_SEARCH = "this edit goes hard"
CAPTION_MATCH_THRESHOLD = 0.35

# ─── Bulk Mode: Multiple Viral Captions ──────────────────────────────
# Search these captions to find motion/grindset accounts and videos.
VIRAL_CAPTIONS = [
    # ── Movie edit captions ──
    "this edit goes hard",
    "wolf of wall street never gets old",
    "jordan belfort was different",
    "scarface understood the game",
    "thomas shelby was not a man to be messed with",
    "patrick bateman was ahead of his time",
    "walter white transformation edit",
    "peaky blinders hits different",
    "the godfather is a masterpiece",
    "goodfellas never misses",

    # ── Sigma / grindset ──
    "sigma rule number one",
    "he was built different",
    "the grind never stops",
    "sigma male grindset",
    "lone wolf mentality",
    "not everyone will understand your grind",
    "they laughed at me now they watch",
    "silence is the best reply",
    "work in silence let success make the noise",
    "discipline is the bridge between goals and accomplishment",

    # ── Money / success ──
    "money is the motive",
    "billionaire mindset hits different",
    "the only way is up",
    "money talks everything else walks",
    "get money or die trying",
    "rich mindset vs poor mindset",
    "this is what success looks like",
    "making money while they sleep",
    "the bag doesn't stop",
    "secure the bag",

    # ── Edit format captions ──
    "cold edit that goes crazy",
    "phonk edit money motivation",
    "this edit is insane",
    "hardest edit on tiktok",
    "after effects edit goes hard",
    "4k edit that hits different",
    "cinematic edit motivation",
    "phonk edits hit different at night",
    "villain arc activated",
    "dark knight energy",
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
