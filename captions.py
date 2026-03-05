"""
Fader v2 — Caption & Hashtag Generator
Never posts identical captions. Combines templates + random emojis + varied hashtags.
"""

import random

# ─── Caption Templates ──────────────────────────────────────────────
# {emoji} and {hashtags} are replaced at generation time.
# Add/remove as many as you want.
TEMPLATES = [
    "{emoji} thoughts? {hashtags}",
    "wait for it… {emoji} {hashtags}",
    "{emoji} this one hits different {hashtags}",
    "no caption needed {emoji} {hashtags}",
    "{emoji} vibes {hashtags}",
    "POV: you found this on your fyp {emoji} {hashtags}",
    "{emoji} save this {hashtags}",
    "tell me I'm wrong {emoji} {hashtags}",
    "{emoji} who else? {hashtags}",
    "had to post this {emoji} {hashtags}",
    "{emoji} iykyk {hashtags}",
    "rate this 1-10 {emoji} {hashtags}",
    "{emoji} real ones know {hashtags}",
    "bookmark this one {emoji} {hashtags}",
    "{emoji} mood {hashtags}",
    "tag someone who needs to see this {emoji} {hashtags}",
    "{emoji} what do you think? {hashtags}",
    "watch till the end {emoji} {hashtags}",
    "{emoji} follow for more {hashtags}",
    "share this with a friend {emoji} {hashtags}",
    "{emoji} just vibes {hashtags}",
    "double tap if you agree {emoji} {hashtags}",
    "{emoji} this {hashtags}",
    "say less {emoji} {hashtags}",
    "{emoji} drop a {emoji} if you relate {hashtags}",
]

# ─── Emoji Pool ─────────────────────────────────────────────────────
EMOJIS = [
    "🔥", "💯", "😂", "🤯", "👀", "💀", "🫠", "✨", "⚡", "🎯",
    "😤", "🙌", "💪", "🤝", "😍", "🥶", "🔑", "📈", "🎬", "🪄",
    "💎", "🚀", "🤫", "😈", "🧠", "❤️", "👑", "🫡", "😮‍💨", "🤌",
]

# ─── Hashtag Pool ───────────────────────────────────────────────────
# Organised by category. The generator picks from mixed categories.
HASHTAG_POOL = [
    # Viral / general
    "#viral", "#fyp", "#foryou", "#explore", "#trending",
    "#reels", "#reelsinstagram", "#instareels", "#viralreels",
    "#foryoupage", "#explorepage", "#discover",
    # Engagement
    "#follow", "#followme", "#like", "#share", "#comment",
    "#likeforlikes", "#followforfollowback",
    # Niche — edit these to match YOUR content niche
    "#motivation", "#lifestyle", "#funny", "#relatable",
    "#memes", "#comedy", "#entertainment", "#dailyvlog",
    "#inspo", "#aesthetic", "#mood", "#vibes",
    "#contentcreator", "#creator", "#influencer",
]


def generate_caption() -> str:
    """Build a unique-ish caption from template + random emoji + random hashtags."""
    template = random.choice(TEMPLATES)

    # Pick 1-3 random emojis (may repeat, that's fine)
    emoji_str = "".join(random.choices(EMOJIS, k=random.randint(1, 3)))

    # Pick 3-5 random hashtags without repeats
    tag_count = random.randint(3, 5)
    tags = random.sample(HASHTAG_POOL, k=min(tag_count, len(HASHTAG_POOL)))
    hashtag_str = " ".join(tags)

    caption = template.replace("{emoji}", emoji_str).replace("{hashtags}", hashtag_str)
    return caption.strip()
