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
        # ── Motion culture / we ball ────────────────────────────────
        "we ball", "we ball hard", "we have motion", "he got motion",
        "motion check", "motion tiktok", "motion funny",
        "we on motion", "on motion", "balling funny",
        "sigma grindset funny", "sigma funny", "sigma meme",
        "sigma male funny tiktok", "sigma shitpost", "sigma rule meme",
        "villain arc funny", "villain arc meme",
        "gigachad funny", "gigachad meme",
        "grindset meme", "hustle meme",
        "money meme funny", "counting money meme", "money flex funny",
        "rich people funny", "gangster meme", "mafia meme",
        # ── Money (goes viral, fits motion perfectly) ───────────────
        "pov you just got paid", "pov you rich",
        "pov your account hits a million", "pov bag secured",
        "making money funny", "getting money funny",
        "broke vs rich funny", "when you finally get money",
        "when the check clears", "when the bag hits",
        "money motivation funny", "rich mindset funny",
        "spending money funny", "flexing money funny",
        "money printer go brrr", "money printer meme",
        "bag secured meme", "securing the bag funny",
        "drip check money", "outfit check rich",
        "lamborghini meme", "ferrari meme", "luxury car meme",
        "yacht meme funny", "rich lifestyle funny",
        "new money funny", "old money funny",
        "hood rich funny", "hood money meme",
        "when you finally get the bag", "first paycheck meme",
        "passive income meme", "passive income funny",
        "stock market meme", "crypto meme funny",
        "investing meme", "real estate meme funny",
        # ── POV — motion character POVs ────────────────────────────
        "pov sigma", "pov villain arc", "pov you're the main character",
        "pov breaking bad", "pov walter white", "pov patrick bateman",
        "pov thomas shelby", "pov jordan belfort", "pov tony montana",
        "pov joker", "pov john wick", "pov harvey specter",
        "pov you got money", "pov rich", "pov boss",
        # ── Me when / bro thinks ────────────────────────────────────
        "me when sigma", "me when money", "me when i get paid",
        "bro thinks hes patrick bateman", "bro thinks hes thomas shelby",
        "bro thinks hes walter white", "bro thinks hes jordan belfort",
        "that one friend who thinks hes sigma",
        "when bro activates villain arc", "when the quiet kid",
        # ── Brainrot (funny overexposure of motion characters) ──────
        "breaking bad brainrot", "walter white brainrot",
        "sigma brainrot", "patrick bateman brainrot",
        "peaky blinders brainrot", "wolf of wall street brainrot",
        "joker brainrot", "american psycho brainrot",
        # ── Breaking Bad / Better Call Saul ────────────────────────
        "walter white funny", "walter white meme", "walter white edit",
        "walter white im the one who knocks", "walter white i am the danger",
        "walter white say my name", "walter white heisenberg",
        "walter white pizza roof", "walter white laugh",
        "jesse pinkman funny", "jesse pinkman meme", "jesse pinkman edit",
        "jesse pinkman he cant keep getting away",
        "gus fring funny", "gus fring meme", "gus fring edit",
        "gus fring acceptable", "gus fring last walk",
        "saul goodman funny", "saul goodman meme", "saul goodman 3d",
        "better call saul funny", "better call saul meme",
        "mike ehrmantraut funny",
        "hank schrader funny",
        "breaking bad funny", "breaking bad meme",
        "breaking bad funny moments", "breaking bad edit",
        "breaking bad compilation funny", "breaking bad best moments",
        "walter white jesse pinkman funny",
        # ── Wolf of Wall Street ─────────────────────────────────────
        "wolf of wall street funny", "wolf of wall street meme",
        "wolf of wall street edit", "wolf of wall street best scenes",
        "wolf of wall street funny moments", "wolf of wall street shitpost",
        "jordan belfort funny", "jordan belfort meme", "jordan belfort edit",
        "jordan belfort chest pound", "jordan belfort im not leaving",
        "jordan belfort sell me this pen", "jordan belfort speech",
        "jordan belfort crawling", "jordan belfort money",
        "donnie azoff funny", "jonah hill wolf of wall street",
        # ── American Psycho / Patrick Bateman ───────────────────────
        "american psycho funny", "american psycho meme",
        "patrick bateman funny", "patrick bateman walking",
        "patrick bateman morning routine", "patrick bateman business card",
        "patrick bateman lets see paul allens card",
        # ── Peaky Blinders ──────────────────────────────────────────
        "peaky blinders funny", "peaky blinders meme",
        "thomas shelby funny", "thomas shelby walking",
        "thomas shelby by order of the peaky blinders",
        # ── Scarface ────────────────────────────────────────────────
        "scarface funny", "scarface meme",
        "tony montana say hello", "tony montana the world is yours",
        # ── Fight Club (currently viral) ────────────────────────────
        "fight club funny", "fight club meme", "fight club edit",
        "tyler durden funny", "tyler durden edit",
        "fight club tiktok", "fight club brainrot",
        # ── Joker ───────────────────────────────────────────────────
        "joker funny", "joker meme", "joker stairs dance",
        "joker we live in a society",
        # ── Sopranos ────────────────────────────────────────────────
        "sopranos funny", "sopranos meme",
        "tony soprano funny", "tony soprano meme",
        # ── Other motion universe shows/films ───────────────────────
        "goodfellas funny", "goodfellas meme",
        "godfather funny", "godfather meme",
        "suits funny", "suits meme", "harvey specter funny",
        "narcos funny", "narcos meme",
        "succession funny", "succession meme",
        "ozark funny", "ozark meme",
        "john wick funny", "john wick meme",
        "pulp fiction funny", "django funny",
        "the wire funny", "the wire meme",
        "game of thrones funny", "game of thrones meme",
        "prison break funny", "prison break meme",
        "power funny", "top boy funny",
        # ── Movie/edit formats that hit ─────────────────────────────
        "coldest movie scene", "hardest movie scene",
        "most badass movie scene", "movie villain edit",
        "phonk movie edit", "movie scene phonk",
        "edit that goes hard", "this edit goes crazy",
        "movie out of context", "best movie meme",
    ],
}
MAX_VIDEOS_PER_KEYWORD = 50            # Videos to collect per keyword
MIN_VIEWS = 100_000                    # Minimum view count (100k = solid traction)
MIN_LIKES = 0                          # Minimum like count (0 = no filter)
MIN_ENGAGEMENT_RATIO = 0.02            # Min likes/views ratio (2% = realistic TikTok avg)
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
