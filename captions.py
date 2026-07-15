"""
Caption & Hashtag Generator — topcats online.

Strategy (Nunu 2026-07-15): post captions are a LONG CAT FACT, led by the
fact so it drives dwell-time/comments, followed by the brand hashtag #kitty
plus a small rotating mix of cat + reach hashtags. Never posts an identical
caption (large fact pool + randomized hashtag sampling).
"""

import random

# ─── Long cat facts (the caption body) ──────────────────────────────
# Genuine, interesting facts. Keep them accurate — engagement dies on
# obviously-wrong "facts" and comments will call them out.
CAT_FACTS = [
    "A cat's nose print is completely unique — no two cats share the same one, just like human fingerprints.",
    "Cats can rotate their ears 180 degrees using 32 muscles in each ear (humans only have 6 per ear).",
    "A group of cats is called a 'clowder,' and a litter of kittens is called a 'kindle.'",
    "Cats spend about 70% of their lives asleep — that's 12 to 16 hours a day.",
    "A cat's purr vibrates between 25 and 150 Hz, a frequency range shown to promote healing and bone density.",
    "Cats can't taste sweetness at all — they're the only mammals known to lack the sweet taste receptor.",
    "The oldest known pet cat was found in a 9,500-year-old grave in Cyprus, buried beside its human.",
    "Cats walk like camels and giraffes: they move both right legs first, then both left legs.",
    "Cats have five toes on their front paws but only four on the back.",
    "A cat's whiskers are roughly as wide as its body, so it can judge whether it'll fit through a gap.",
    "Cats can make over 100 different vocal sounds. Dogs make only about 10.",
    "Adult cats meow almost exclusively to communicate with humans — rarely with other cats.",
    "A cat's righting reflex lets it twist mid-air and land on its feet, needing only about 12 inches to do it.",
    "Cats only sweat through the pads of their paws.",
    "A house cat can sprint up to about 30 mph in short bursts — faster than Usain Bolt's top speed.",
    "A reflective layer behind a cat's eyes, the tapetum lucidum, lets it see in one-sixth the light a human needs.",
    "Every kitten is born with blue eyes; their true adult color develops over the first few weeks.",
    "A cat's brain structure is about 90% similar to a human's — closer to ours than a dog's is.",
    "Kittens knead to stimulate their mother's milk, and many keep doing it into adulthood as a sign of contentment.",
    "The first cat in space was a French cat named Félicette, launched in 1963 — and she survived.",
    "When a cat rubs its face on you, it's marking you as its own using scent glands in its cheeks.",
    "A cat's tail holds nearly 10% of all the bones in its body.",
    "Cats can leap up to six times their own body length in a single jump.",
    "Ancient Egyptians revered cats so deeply that harming one — even accidentally — could be punished by death.",
    "Cats dream: they enter REM sleep and their whiskers and paws twitch, just like ours do.",
    "A cat's field of vision spans about 200 degrees, noticeably wider than a human's 180.",
    "Cats have around 470 taste buds (humans have ~9,000) but a sense of smell about 14 times stronger than ours.",
    "A cat's collarbone floats freely and isn't attached to other bones — that's how they squeeze through tight spaces.",
    "Cats can be right- or left-pawed, and studies suggest it often correlates with their sex.",
    "A purr isn't always happiness — cats also purr to self-soothe when they're stressed, injured, or afraid.",
    "The average house cat shares roughly 95.6% of its DNA with the tiger.",
    "A cat named Stubbs served as the honorary mayor of Talkeetna, Alaska, for 20 years.",
    "Isaac Newton is widely credited with inventing the cat flap so his cats wouldn't disturb his experiments.",
    "Cats have whiskers on the backs of their front legs, not just on their faces, to help them feel their prey.",
    "A cat's heart beats almost twice as fast as a human's — around 110 to 140 beats per minute.",
    "Cats have a third eyelid, the nictitating membrane, that sweeps across the eye to keep it moist and protected.",
]

# ─── Hashtags ───────────────────────────────────────────────────────
BRAND_TAG = "#kitty"  # Nunu's chosen primary hashtag — always first.
CAT_HASHTAGS = [
    "#cat", "#cats", "#catsofinstagram", "#kitten", "#kittensofinstagram",
    "#catlover", "#catlovers", "#catmemes", "#funnycats", "#funnycat",
    "#catvideos", "#cutecat", "#cutecats", "#meow", "#catlife",
    "#kittycat", "#catstagram", "#catoftheday", "#hellokitty", "#sanrio",
]
REACH_HASHTAGS = [
    "#reels", "#reelsinstagram", "#fyp", "#foryou", "#explore",
    "#explorepage", "#viral", "#viralreels", "#trending",
]


def generate_caption() -> str:
    """A long cat fact + #kitty + a rotating mix of cat/reach hashtags."""
    fact = random.choice(CAT_FACTS)

    tags = [BRAND_TAG]
    tags += random.sample(CAT_HASHTAGS, k=random.randint(4, 6))
    tags += random.sample(REACH_HASHTAGS, k=random.randint(2, 4))
    # de-dup while preserving order (brand tag stays first)
    seen, ordered = set(), []
    for t in tags:
        if t.lower() not in seen:
            seen.add(t.lower())
            ordered.append(t)

    return f"{fact}\n\n{' '.join(ordered)}"


if __name__ == "__main__":
    for _ in range(3):
        print(generate_caption())
        print("-" * 60)
