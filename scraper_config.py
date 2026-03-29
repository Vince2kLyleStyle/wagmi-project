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
        # ═══════════════════════════════════════════════════════
        # TIER 1: VIRAL FORMATS — these are how funny content
        # is actually tagged on TikTok. Search by FORMAT not just
        # movie name. These pull the short punchy clips.
        # ═══════════════════════════════════════════════════════

        # ── "POV" format (relatable movie clips) ──
        "pov sigma", "pov villain arc", "pov you're the main character",
        "pov breaking bad", "pov walter white", "pov patrick bateman",
        "pov thomas shelby", "pov jordan belfort", "pov tony montana",
        "pov joker", "pov john wick", "pov harvey specter",
        "pov you got money", "pov rich", "pov boss",

        # ── "Me when" / "bro thinks he's" format (meme clips) ──
        "me when sigma", "me when money", "me when i get paid",
        "bro thinks hes patrick bateman", "bro thinks hes thomas shelby",
        "bro thinks hes walter white", "bro thinks hes the joker",
        "bro thinks hes jordan belfort", "bro thinks hes tony montana",
        "that one friend who thinks hes sigma",
        "when the quiet kid", "when bro activates villain arc",

        # ── Brainrot / unhinged (the funniest content) ──
        "breaking bad brainrot", "sigma brainrot",
        "movie brainrot", "cinema brainrot",
        "patrick bateman brainrot", "walter white brainrot",
        "peaky blinders brainrot", "joker brainrot",
        "american psycho brainrot", "scarface brainrot",
        "wolf of wall street brainrot",

        # ── Specific iconic MOMENTS that became memes ──
        "patrick bateman business card", "patrick bateman walking",
        "patrick bateman morning routine", "patrick bateman axe",
        "patrick bateman lets see paul allens card",
        "thomas shelby cigarette", "thomas shelby walking",
        "thomas shelby by order of the peaky blinders",
        "tony montana say hello", "tony montana the world is yours",
        "joker stairs dance", "joker society", "joker we live in a society",
        "joker you wouldnt get it", "joker hospital scene",
        "tyler durden soap", "tyler durden rules of fight club",
        "harvey specter can opener", "harvey specter get out",
        "gustavo fring i will kill your family",
        "mike ehrmantraut half measures",

        # ═══════════════════════════════════════════════════════
        # TIER 2: BREAKING BAD MEGA DEEP DIVE
        # Every character, every meme scene, every format
        # ═══════════════════════════════════════════════════════

        # Walter White
        "walter white funny", "walter white meme", "walter white edit",
        "walter white transformation", "walter white heisenberg",
        "walter white cooking", "walter white i am the danger",
        "walter white say my name", "walter white pizza roof",
        "walter white underwear", "walter white tighty whities",
        "walter white laugh", "walter white crawl space",
        "walter white you got me", "walter white stay out of my territory",
        "walter white we need to cook", "walter white im the one who knocks",

        # Jesse Pinkman
        "jesse pinkman funny", "jesse pinkman meme", "jesse pinkman edit",
        "jesse pinkman bitch", "jesse pinkman yo mr white",
        "jesse pinkman science", "jesse pinkman yeah science",
        "jesse pinkman magnets", "jesse pinkman cap",
        "jesse pinkman crying", "jesse pinkman he cant keep getting away",

        # Gus Fring
        "gus fring funny", "gus fring meme", "gus fring edit",
        "gus fring face off", "gus fring box cutter",
        "gus fring last walk", "gus fring pollos hermanos",
        "gus fring acceptable", "gus fring stare",

        # Saul / Better Call Saul
        "saul goodman funny", "saul goodman meme", "better call saul funny",
        "saul goodman ad", "saul goodman commercial",
        "better call saul meme", "better call saul out of context",
        "jimmy mcgill funny", "saul goodman 3d",

        # Other BB characters
        "hank schrader funny", "hank schrader minerals",
        "hank schrader theyre minerals marie",
        "mike ehrmantraut funny", "mike ehrmantraut no half measures",
        "tuco salamanca funny", "tuco tight tight tight",
        "skinny pete funny", "badger funny", "skinny pete badger",

        # Breaking Bad formats
        "breaking bad funny", "breaking bad meme", "breaking bad funny moments",
        "breaking bad tiktok", "breaking bad edit",
        "breaking bad out of context", "breaking bad shitpost",
        "breaking bad brainrot", "breaking bad no context",
        "breaking bad compilation funny", "breaking bad best moments",
        "walter white jesse pinkman funny",

        # ═══════════════════════════════════════════════════════
        # TIER 2B: WOLF OF WALL STREET DEEP DIVE
        # ═══════════════════════════════════════════════════════
        "wolf of wall street funny", "wolf of wall street meme",
        "wolf of wall street edit", "wolf of wall street tiktok",
        "wolf of wall street out of context",
        "wolf of wall street best scenes", "wolf of wall street funny moments",
        "jordan belfort funny", "jordan belfort meme", "jordan belfort edit",
        "jordan belfort chest pound", "jordan belfort im not leaving",
        "jordan belfort quaalude", "jordan belfort crawling",
        "jordan belfort sell me this pen", "jordan belfort speech",
        "jordan belfort party scene", "jordan belfort yacht",
        "jordan belfort money", "jordan belfort lambo",
        "donnie azoff funny", "jonah hill wolf of wall street",
        "wolf of wall street phone scene", "wolf of wall street office scene",
        "wolf of wall street shitpost", "wolf of wall street brainrot",

        # ═══════════════════════════════════════════════════════
        # TIER 3: OTHER MOVIE MEMES (BB & WoWS covered above)
        # ═══════════════════════════════════════════════════════
        "scarface funny", "scarface meme", "scarface out of context",
        "american psycho funny", "american psycho meme", "american psycho out of context",
        "peaky blinders funny", "peaky blinders meme", "peaky blinders out of context",
        "godfather funny", "godfather meme",
        "goodfellas funny", "goodfellas meme", "goodfellas out of context",
        "fight club funny", "fight club meme",
        "joker funny", "joker meme",
        "john wick funny", "john wick meme",
        "suits funny", "suits meme", "suits out of context",
        "narcos funny", "narcos meme", "narcos out of context",
        "money heist funny", "money heist meme",
        "top boy funny", "power funny",
        "succession funny", "succession meme",
        "ozark funny", "ozark meme",
        "django funny", "pulp fiction funny",
        "taxi driver meme", "nightcrawler meme",
        "drive movie meme", "blade runner meme",
        # Bonus shows that produce great meme content
        "sopranos funny", "sopranos meme", "sopranos out of context",
        "tony soprano funny", "tony soprano meme",
        "the wire funny", "the wire meme",
        "game of thrones funny", "game of thrones meme",
        "house of cards funny", "frank underwood meme",
        "sherlock funny", "sherlock meme",
        "prison break funny", "prison break meme",

        # ── Movie out of context / shitpost (pure gold) ──
        "movie out of context", "movie scene out of context",
        "film out of context", "cinema out of context",
        "movie shitpost", "film shitpost",
        "movie scene no context", "best movie meme",

        # ── Sigma / gigachad MEMES (funny only) ──
        "sigma meme", "sigma male meme", "sigma funny",
        "sigma rule meme", "gigachad meme", "gigachad funny",
        "villain arc meme", "villain arc funny",
        "grindset meme", "hustle meme",
        "sigma male funny tiktok", "sigma shitpost",

        # ── Money memes (funny, not guru content) ──
        "money meme", "money meme funny",
        "counting money meme", "money flex funny",
        "rich people funny", "hood money meme",
        "gangster meme", "mafia meme",
        "money printer meme", "bag secured meme",

        # ── Phonk / cold edits (short bangers) ──
        "phonk edit", "phonk movie edit",
        "coldest movie scene", "hardest movie scene",
        "movie scene phonk", "cold edit",
        "edit that goes hard", "this edit goes crazy",
        "most badass movie scene", "movie villain edit",
    ],
}

# ─── Viral Caption Search ────────────────────────────────────────────
VIRAL_CAPTION_SEARCH = "this edit goes hard"
CAPTION_MATCH_THRESHOLD = 0.35

# ─── Bulk Mode: Multiple Viral Captions ──────────────────────────────
# Search these captions to find motion/grindset accounts and videos.
VIRAL_CAPTIONS = [
    # ── POV / relatable format (finds meme accounts) ──
    "pov you just activated your villain arc",
    "bro thinks hes patrick bateman",
    "bro thinks hes thomas shelby",
    "when the quiet kid starts quoting walter white",
    "me when i get my paycheck",
    "that one friend who watches too many gangster movies",

    # ── Out of context / shitpost (finds funny accounts) ──
    "breaking bad out of context",
    "movie scenes out of context",
    "this scene is unhinged",
    "no context just cinema",
    "how did this get approved",

    # ── Specific moment memes (finds clip accounts) ──
    "patrick bateman business card scene will never get old",
    "jesse pinkman is the funniest character ever",
    "walter white pizza scene",
    "jordan belfort chest thump",
    "gus fring was actually terrifying",
    "saul goodman is comedy gold",

    # ── Edit appreciation (finds edit pages) ──
    "this edit goes hard",
    "nah this edit goes crazy",
    "hardest edit on tiktok",
    "who made this edit",
    "the way this edit hits different",
    "phonk edits at 3am hit different",
    "coldest movie scene ever edited",
    "movie memes that hit different",

    # ── Brainrot / unhinged ──
    "breaking bad brainrot",
    "cinema brainrot",
    "sigma brainrot is taking over",
    "this is peak cinema",
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
MIN_VIEWS = 25_000                     # Catch good newer content that hasn't blown up yet
MIN_LIKES = 500                        # Must have some engagement
MIN_ENGAGEMENT_RATIO = 0.04            # 4% engagement — funny content gets liked more
MIN_INTERACTIONS = 5_000               # Lower bar — good memes sometimes have fewer shares
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
