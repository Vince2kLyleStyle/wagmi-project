"""
Fader v2 — Per-Niche Configuration
Each niche gets its own captions, hashtags, and content strategy.
Add new niches by adding a new entry to NICHE_PROFILES.
"""

import random

# ─── Niche Profiles ──────────────────────────────────────────────────
# Each niche defines:
#   - caption_templates: Short, engaging captions (like real meme pages use)
#   - hashtags: Niche-specific hashtag pool
#   - hashtag_count: (min, max) hashtags per post
#   - emoji_pool: Niche-appropriate emojis

NICHE_PROFILES = {
    "trading": {
        "caption_templates": [
            "{emoji} the markets don't care about your feelings",
            "POV: you finally understand support and resistance {emoji}",
            "{emoji} traders at 4am checking futures",
            "tell me you're a trader without telling me {emoji}",
            "that moment when your position goes green {emoji}",
            "{emoji} risk management is everything",
            "paper hands could never {emoji}",
            "{emoji} the chart never lies",
            "when the market opens and your calls are printing {emoji}",
            "diamond hands or bust {emoji}",
            "{emoji} caught this setup live",
            "patience pays {emoji}",
            "{emoji} this trade changed everything",
            "who else was in this trade? {emoji}",
            "the setup was right there {emoji}",
        ],
        "hashtags": [
            "#trading", "#trader", "#forex", "#stocks", "#crypto",
            "#daytrading", "#stockmarket", "#forextrader", "#bitcoin",
            "#investing", "#wallstreet", "#tradingview", "#options",
            "#swingtrading", "#cryptotrading", "#financialfreedom",
            "#tradingtips", "#pricaction", "#technicalanalysis",
            "#tradinglife", "#fyp", "#viral", "#explore",
        ],
        "hashtag_count": (3, 6),
        "emoji_pool": ["📈", "💰", "🔥", "💎", "🚀", "📊", "💵", "🤑", "⚡", "🧠"],
    },

    "gambling": {
        "caption_templates": [
            "{emoji} hit or miss?",
            "the rush when it hits {emoji}",
            "{emoji} bet you didn't see that coming",
            "all in {emoji}",
            "when luck is on your side {emoji}",
            "{emoji} the comeback was insane",
            "no way this just happened {emoji}",
            "would you have made this bet? {emoji}",
            "{emoji} that payout tho",
            "risk it for the biscuit {emoji}",
            "the table was HOT {emoji}",
            "{emoji} watch till the end",
            "doubled down and won {emoji}",
            "{emoji} biggest win today",
        ],
        "hashtags": [
            "#gambling", "#casino", "#poker", "#slots", "#blackjack",
            "#sportsbetting", "#betting", "#roulette", "#jackpot",
            "#bigwin", "#casinolife", "#pokerlife", "#gamblinglife",
            "#winners", "#lucky", "#megawin", "#slotmachine",
            "#fyp", "#viral", "#explore",
        ],
        "hashtag_count": (3, 5),
        "emoji_pool": ["🎰", "🃏", "💰", "🔥", "💎", "🎲", "🤑", "⚡", "👀", "🏆"],
    },

    "hustle": {
        "caption_templates": [
            "{emoji} outwork everyone",
            "they sleep, we grind {emoji}",
            "{emoji} broke is a mindset",
            "comfort zone is a prison {emoji}",
            "built different {emoji}",
            "{emoji} the grind doesn't stop",
            "while you scroll I work {emoji}",
            "no days off {emoji}",
            "{emoji} success leaves clues",
            "discipline over motivation {emoji}",
            "{emoji} level up or get left behind",
            "the results speak {emoji}",
            "started from nothing {emoji}",
            "{emoji} stay focused",
        ],
        "hashtags": [
            "#hustle", "#motivation", "#grindset", "#mindset",
            "#entrepreneur", "#success", "#millionaire", "#luxury",
            "#wealth", "#rich", "#lifestyle", "#goals",
            "#ambition", "#hustlehard", "#nevergiveup",
            "#moneymindset", "#bossmindset", "#sigmamale",
            "#fyp", "#viral", "#explore",
        ],
        "hashtag_count": (3, 6),
        "emoji_pool": ["💪", "🔥", "💰", "🚀", "👑", "⚡", "🧠", "💎", "😤", "🫡"],
    },

    "memes": {
        "caption_templates": [
            "{emoji} im dead",
            "why is this so accurate {emoji}",
            "{emoji} tag someone who does this",
            "no but fr tho {emoji}",
            "{emoji} caught in 4k",
            "this is too real {emoji}",
            "send this to your friend with no context {emoji}",
            "{emoji} I can't breathe",
            "me on a daily basis {emoji}",
            "every single time {emoji}",
            "{emoji} the accuracy",
            "who made this {emoji}",
            "tell me I'm not the only one {emoji}",
            "{emoji} facts",
            "real ones know {emoji}",
        ],
        "hashtags": [
            "#memes", "#funny", "#comedy", "#humor", "#relatable",
            "#lol", "#meme", "#funnyvideos", "#funnymemes",
            "#dankmemes", "#memesdaily", "#comedyvideos",
            "#dailymemes", "#viralvideos", "#trending",
            "#fyp", "#viral", "#explore", "#foryou",
        ],
        "hashtag_count": (3, 5),
        "emoji_pool": ["😂", "💀", "🤣", "😭", "🫠", "💀", "😮‍💨", "🤡", "👀", "🔥"],
    },

    "brainrot": {
        "caption_templates": [
            "{emoji} normalize this",
            "hear me out {emoji}",
            "{emoji} no thoughts just vibes",
            "why does this make sense {emoji}",
            "the unserious energy is real {emoji}",
            "{emoji} this is peak behavior",
            "i refuse to be serious about this {emoji}",
            "tell me why this is so real {emoji}",
            "{emoji} rent free in my head",
            "the bar is underground {emoji}",
            "{emoji} i'm not even sorry",
            "pov: you've given up being normal {emoji}",
            "who else just exists {emoji}",
            "{emoji} chronically online and proud",
            "absolutely unhinged {emoji}",
            "society peaked here {emoji}",
            "{emoji} this is fine",
            "we're all just npcs fr {emoji}",
            "the delusion is immaculate {emoji}",
            "{emoji} core memory unlocked",
        ],
        "hashtags": [
            "#brainrot", "#absurd", "#unserious", "#humor", "#satire",
            "#shitpost", "#chronicallyonline", "#memes", "#funny",
            "#comedy", "#relatable", "#npc", "#delulu", "#chaotic",
            "#peakcomedy", "#nothoughts", "#braindead", "#feral",
            "#fyp", "#viral", "#foryou", "#explore",
        ],
        "hashtag_count": (3, 6),
        "emoji_pool": ["💀", "🫠", "🧠", "🤡", "😭", "🗿", "👁️", "🫡", "😮‍💨", "🤌", "💅", "🦧"],
    },

    "fitness": {
        "caption_templates": [
            "{emoji} no excuses",
            "chest day hits different {emoji}",
            "{emoji} form check",
            "the pump is real {emoji}",
            "{emoji} gains don't sleep",
            "train like nobody's watching {emoji}",
            "your only competition is yesterday {emoji}",
            "{emoji} PRs don't chase you, you chase PRs",
            "consistency over intensity {emoji}",
            "{emoji} built not bought",
        ],
        "hashtags": [
            "#fitness", "#gym", "#workout", "#fitnessmotivation",
            "#bodybuilding", "#fit", "#gains", "#muscle",
            "#training", "#gymlife", "#fitfam", "#lifting",
            "#strength", "#physique", "#gymrat",
            "#fyp", "#viral", "#explore",
        ],
        "hashtag_count": (3, 5),
        "emoji_pool": ["💪", "🔥", "🏋️", "⚡", "🫡", "😤", "🧠", "👑", "💯", "🔱"],
    },
}


def get_niche_caption(niche: str) -> str:
    """Generate a caption for the given niche with emojis and hashtags."""
    profile = NICHE_PROFILES.get(niche)
    if not profile:
        profile = NICHE_PROFILES.get("memes", list(NICHE_PROFILES.values())[0])

    template = random.choice(profile["caption_templates"])
    emoji = random.choice(profile["emoji_pool"])

    min_tags, max_tags = profile["hashtag_count"]
    tag_count = random.randint(min_tags, max_tags)
    tags = random.sample(profile["hashtags"], k=min(tag_count, len(profile["hashtags"])))

    caption = template.replace("{emoji}", emoji)
    caption = f"{caption}\n.\n.\n{' '.join(tags)}"
    return caption


def get_burst_caption(niche: str) -> str:
    """
    Generate ONE caption to be reused across an entire burst (3 reels).
    Same caption per burst = consistent presence in the algorithm.
    Call this once per burst, then pass the result to each upload.
    """
    return get_niche_caption(niche)


def list_niches() -> list[str]:
    """Return all available niche names."""
    return list(NICHE_PROFILES.keys())
