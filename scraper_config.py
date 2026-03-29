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
    "motion": [
        "pov sigma", "pov villain arc", "pov you're the main character",
        "pov breaking bad", "pov walter white", "pov patrick bateman",
        "pov thomas shelby", "pov jordan belfort", "pov tony montana",
        "pov joker", "pov john wick", "pov harvey specter",
        "pov you got money", "pov rich", "pov boss",
        "me when sigma", "me when money", "me when i get paid",
        "bro thinks hes patrick bateman", "bro thinks hes thomas shelby",
        "bro thinks hes walter white", "bro thinks hes the joker",
        "bro thinks hes jordan belfort", "bro thinks hes tony montana",
        "that one friend who thinks hes sigma", "when the quiet kid",
        "when bro activates villain arc",
        "breaking bad brainrot", "sigma brainrot", "movie brainrot",
        "cinema brainrot", "patrick bateman brainrot",
        "walter white brainrot", "peaky blinders brainrot",
        "joker brainrot", "american psycho brainrot",
        "scarface brainrot", "wolf of wall street brainrot",
        "patrick bateman business card", "patrick bateman walking",
        "patrick bateman morning routine", "patrick bateman axe",
        "patrick bateman lets see paul allens card",
        "thomas shelby cigarette", "thomas shelby walking",
        "thomas shelby by order of the peaky blinders",
        "tony montana say hello", "tony montana the world is yours",
        "joker stairs dance", "joker society",
        "joker we live in a society", "joker you wouldnt get it",
        "joker hospital scene",
        "tyler durden soap", "tyler durden rules of fight club",
        "harvey specter can opener", "harvey specter get out",
        "gustavo fring i will kill your family",
        "mike ehrmantraut half measures",
        "walter white funny", "walter white meme", "walter white edit",
        "walter white transformation", "walter white heisenberg",
        "walter white cooking", "walter white i am the danger",
        "walter white say my name", "walter white pizza roof",
        "walter white underwear", "walter white tighty whities",
        "walter white laugh", "walter white crawl space",
        "walter white you got me", "walter white stay out of my territory",
        "walter white we need to cook", "walter white im the one who knocks",
        "jesse pinkman funny", "jesse pinkman meme", "jesse pinkman edit",
        "jesse pinkman bitch", "jesse pinkman yo mr white",
        "jesse pinkman science", "jesse pinkman yeah science",
        "jesse pinkman magnets", "jesse pinkman cap",
        "jesse pinkman crying", "jesse pinkman he cant keep getting away",
        "gus fring funny", "gus fring meme", "gus fring edit",
        "gus fring face off", "gus fring box cutter",
        "gus fring last walk", "gus fring pollos hermanos",
        "gus fring acceptable", "gus fring stare",
        "saul goodman funny", "saul goodman meme",
        "better call saul funny", "saul goodman ad",
        "saul goodman commercial", "better call saul meme",
        "better call saul out of context", "jimmy mcgill funny",
        "saul goodman 3d", "hank schrader funny",
        "hank schrader minerals", "hank schrader theyre minerals marie",
        "mike ehrmantraut funny", "mike ehrmantraut no half measures",
        "tuco salamanca funny", "tuco tight tight tight",
        "skinny pete funny", "badger funny", "skinny pete badger",
        "breaking bad funny", "breaking bad meme",
        "breaking bad funny moments", "breaking bad tiktok",
        "breaking bad edit", "breaking bad out of context",
        "breaking bad shitpost", "breaking bad no context",
        "breaking bad compilation funny", "breaking bad best moments",
        "walter white jesse pinkman funny",
        "wolf of wall street funny", "wolf of wall street meme",
        "wolf of wall street edit", "wolf of wall street tiktok",
        "wolf of wall street out of context",
        "wolf of wall street best scenes",
        "wolf of wall street funny moments",
        "jordan belfort funny", "jordan belfort meme",
        "jordan belfort edit", "jordan belfort chest pound",
        "jordan belfort im not leaving", "jordan belfort quaalude",
        "jordan belfort crawling", "jordan belfort sell me this pen",
        "jordan belfort speech", "jordan belfort party scene",
        "jordan belfort yacht", "jordan belfort money",
        "jordan belfort lambo", "donnie azoff funny",
        "jonah hill wolf of wall street",
        "wolf of wall street phone scene",
        "wolf of wall street office scene",
        "wolf of wall street shitpost", "wolf of wall street brainrot",
        "scarface funny", "scarface meme", "scarface out of context",
        "american psycho funny", "american psycho meme",
        "american psycho out of context",
        "peaky blinders funny", "peaky blinders meme",
        "peaky blinders out of context",
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
        "sopranos funny", "sopranos meme", "sopranos out of context",
        "tony soprano funny", "tony soprano meme",
        "the wire funny", "the wire meme",
        "game of thrones funny", "game of thrones meme",
        "house of cards funny", "frank underwood meme",
        "sherlock funny", "sherlock meme",
        "prison break funny", "prison break meme",
        "movie out of context", "movie scene out of context",
        "film out of context", "cinema out of context",
        "movie shitpost", "film shitpost",
        "movie scene no context", "best movie meme",
        "sigma meme", "sigma male meme", "sigma funny",
        "sigma rule meme", "gigachad meme", "gigachad funny",
        "villain arc meme", "villain arc funny",
        "grindset meme", "hustle meme",
        "sigma male funny tiktok", "sigma shitpost",
        "money meme", "money meme funny",
        "counting money meme", "money flex funny",
        "rich people funny", "hood money meme",
        "gangster meme", "mafia meme",
        "money printer meme", "bag secured meme",
        "phonk edit", "phonk movie edit",
        "coldest movie scene", "hardest movie scene",
        "movie scene phonk", "cold edit",
        "edit that goes hard", "this edit goes crazy",
        "most badass movie scene", "movie villain edit",
    ],
}
MAX_VIDEOS_PER_KEYWORD = 50            # Videos to collect per keyword
MIN_VIEWS = 1_000_000                  # Minimum view count — viral only
MIN_LIKES = 0                          # Minimum like count (0 = no filter)
MIN_ENGAGEMENT_RATIO = 0.05            # Min likes/views ratio (5% = genuinely good)
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
