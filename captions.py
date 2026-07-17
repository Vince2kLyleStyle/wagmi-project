"""
Caption & Hashtag Generator — topcats online.

Strategy (Nunu 2026-07-15, revised 2026-07-16): post captions are a LONG cat
fact — Nunu's hard requirement is that the caption BE LONG, so each body is a
multi-sentence paragraph (~500-900 chars), not a one-liner. Led by the fact to
drive dwell-time, closed with a question to drive comments, then the brand
hashtag #kitty plus a rotating mix of cat + reach hashtags.

Never posts an identical caption (large fact pool + randomized question and
hashtag sampling).
"""

import random

# ─── Long cat facts (the caption body) ──────────────────────────────
# Genuine, interesting, and LONG — each is a multi-sentence paragraph.
# Keep them accurate: engagement dies on obviously-wrong "facts" and the
# comments will call them out.
CAT_FACTS = [
    "A cat's nose print is completely unique. The ridges and bumps on it form a "
    "pattern that no two cats on earth share, exactly like a human fingerprint. "
    "Some shelters have genuinely experimented with nose-printing as a way to "
    "identify lost cats, and there are apps now that try to match a photo of a "
    "nose to a database. So the next time your cat boops you, remember it is "
    "technically leaving evidence at the scene.",

    "Cats can rotate their ears 180 degrees, and each ear is powered by 32 "
    "separate muscles. Humans only have 6 per ear, which is why most of us "
    "cannot wiggle ours at all. Those muscles let a cat swivel each ear "
    "independently, so it can track two different sounds at once — one ear on "
    "you, one ear on the fridge. That slow ear swivel while they pretend to "
    "ignore you is not them ignoring you. They heard everything.",

    "A group of cats is called a clowder, and a litter of kittens is called a "
    "kindle. There are older regional terms too — a group of wild or stray cats "
    "was sometimes called a destruction, which feels about right. English "
    "collected these collective nouns during the medieval period, when naming "
    "groups of animals was a genuine status hobby among the nobility. So your "
    "three cats sitting on the counter are, formally speaking, a clowder.",

    "Cats spend about 70% of their lives asleep — roughly 12 to 16 hours a day, "
    "and older cats can push past 20. This is not laziness. Cats evolved as "
    "ambush predators, and hunting in short explosive bursts is metabolically "
    "expensive, so conserving energy between hunts is the whole strategy. Even "
    "asleep, they are barely off duty: cats spend much of that time in light "
    "sleep, ears still tracking the room, able to go from unconscious to "
    "airborne in under a second.",

    "A cat's purr vibrates between 25 and 150 Hz — a frequency range that has "
    "been shown to promote tissue healing and bone density. Researchers noticed "
    "cats purr not only when content but also when injured, giving birth, or "
    "dying, which suggests the purr is partly a self-repair mechanism. The "
    "leading theory is that it is a low-cost way to keep bones and tissue "
    "conditioned during those long hours of rest. Your cat is running physical "
    "therapy on your chest.",

    "Cats cannot taste sweetness at all. They are the only mammals known to lack "
    "a working sweet taste receptor — the gene for it is broken in every cat "
    "studied, from house cats to tigers. As obligate carnivores, their ancestors "
    "had no evolutionary use for detecting sugar, so the gene simply decayed. "
    "This is why a cat that seems to love ice cream is actually reacting to the "
    "fat and dairy, not the sugar. They have never once tasted a dessert.",

    "The oldest known pet cat was found in a 9,500-year-old grave in Cyprus, "
    "buried carefully beside its human. Cyprus had no native wild cats, which "
    "means someone brought that cat over by boat — a deliberate act, thousands "
    "of years before Egypt's famous cat worship. The two skeletons were laid out "
    "facing the same direction, only inches apart. Somebody 9,500 years ago "
    "loved their cat enough to sail it across the sea and be buried next to it.",

    "Cats walk like camels and giraffes. They move both right legs first, then "
    "both left legs — a gait called pacing, which shifts the whole body weight "
    "smoothly from side to side instead of bouncing it up and down. Almost no "
    "other small mammals move this way; most trot with diagonal pairs. It is "
    "part of why a cat crossing a room looks like it is gliding, and part of why "
    "they can move in near silence when they want to.",

    "A cat's whiskers are roughly as wide as its body, and that is not a "
    "coincidence. Whiskers work as a built-in measuring tape: if the whiskers "
    "fit through a gap, the cat fits through a gap. They are not hairs in the "
    "ordinary sense either — each one is rooted three times deeper than normal "
    "fur, wired into a dense bundle of nerves that reads air currents and "
    "vibration. This is also why an overweight cat can get genuinely confused "
    "about what it fits through. The whiskers did not get the memo.",

    "Cats can make over 100 different vocal sounds. Dogs manage only about 10. "
    "Even stranger, adult cats almost never meow at each other — meowing is "
    "essentially a language they invented for humans. Kittens meow at their "
    "mothers, then grow out of it with other cats, but keep it up with us "
    "forever because it works. Many cats develop specific meows for specific "
    "people. Your cat is not just talking. Your cat has a dialect for you.",

    "A cat's righting reflex lets it twist mid-air and land on its feet, and it "
    "needs only about 12 inches of fall to do it. The reflex appears at 3 to 4 "
    "weeks old and is fully developed by 7 weeks. It works because a cat's "
    "collarbone floats free and its spine is unusually flexible, letting the "
    "front and back halves of the body rotate in opposite directions like a "
    "wrung towel. Physicists genuinely argued about how it worked until "
    "high-speed film settled it in the 1890s.",

    "A house cat can sprint up to about 30 mph in short bursts — faster than "
    "Usain Bolt at his absolute peak. They achieve it with a flexible spine that "
    "coils and releases like a spring, extending their stride well past what "
    "their leg length should allow. The catch is that it is purely anaerobic: a "
    "cat can hold that speed for only a few hundred feet before overheating. "
    "Built entirely for the ambush, with no interest in the marathon.",

    "There is a reflective layer behind a cat's eyes called the tapetum lucidum, "
    "and it lets a cat see in about one-sixth the light a human needs. It works "
    "by bouncing light back through the retina a second time, giving the "
    "photoreceptors two chances at every photon. That mirror is also exactly why "
    "cat eyes glow in photos and headlights — you are seeing light reflect "
    "straight back out. The tradeoff is a slightly blurrier image. Cats traded "
    "sharpness for the dark, and it was worth it.",

    "Every kitten is born with blue eyes. The blue is not pigment at all — it is "
    "the same light-scattering effect that makes the sky look blue, showing "
    "through an iris that has not made any melanin yet. Their real adult color "
    "develops over the first several weeks as pigment fills in, usually settling "
    "somewhere between 6 and 12 weeks. Cats that stay blue-eyed as adults, like "
    "Siamese, are the ones whose irises never started producing pigment at all.",

    "Adult cats meow almost exclusively to communicate with humans, and rarely "
    "with each other. Between themselves, cats mostly use scent, posture, tail "
    "position, and ear angle — a silent language we are largely blind to. The "
    "meow is a deliberate adaptation to us, refined over roughly 10,000 years of "
    "living alongside people who respond to noise. Studies have found cats even "
    "tune the pitch of their meows to something closer to a human infant's cry, "
    "because we are wired to react to that.",

    "Ancient Egyptians revered cats so deeply that harming one — even "
    "accidentally — could be punished by death. When a household cat died "
    "naturally, the family would shave their eyebrows in mourning and keep them "
    "shaved until they grew back on their own. Cats were mummified in enormous "
    "numbers, and there are records of a battle where invaders reportedly used "
    "the taboo against them. Egypt also banned exporting cats, which mostly "
    "resulted in a thriving cat smuggling trade.",

    "Cats dream. They enter REM sleep just like we do, and during it their "
    "whiskers twitch, their paws paddle, and their eyes move behind the lids. "
    "In a famous set of experiments, researchers disabled the brain mechanism "
    "that paralyzes the body during REM, and the sleeping cats got up and began "
    "stalking, pouncing, and grooming invisible things — acting out their dreams. "
    "Cats appear to dream about being cats. Which is honestly the correct answer.",

    "A cat's brain structure is about 90% similar to a human's — closer to ours "
    "than a dog's brain is. They have the same basic regions for emotion, and a "
    "cerebral cortex with roughly twice as many neurons in the visual areas as "
    "dogs have. Their short-term memory outperforms dogs in several tests, and "
    "their long-term memory is genuinely excellent. When a cat remembers exactly "
    "which cupboard the treats live in three months later, that is not luck.",

    "Kittens knead to stimulate their mother's milk, pressing alternate paws "
    "against her to get it flowing. Many keep doing it their entire lives, on "
    "blankets, laps, and unfortunately bare skin. Adult kneading is generally "
    "read as a sign of deep contentment and safety — the cat is running a "
    "behavior it associates with being a warm, fed, unbothered kitten. There are "
    "also scent glands in their paw pads, so a kneading cat is quietly marking "
    "you as its property at the same time.",

    "The first cat in space was a French cat named Félicette, launched in 1963 — "
    "and she survived the flight. She was picked from a group of 14 street cats "
    "in Paris, flew to about 100 miles up, and came back down by parachute after "
    "roughly 15 minutes. For decades she was almost completely forgotten, and "
    "monuments often mistakenly showed a male cat named Felix. In 2019 a proper "
    "bronze statue of Félicette was finally unveiled, and she is now the only "
    "cat to have gone to space and returned.",

    "When a cat rubs its face on you, it is claiming you. Cats have scent glands "
    "packed into their cheeks, chin, forehead, and the base of the ears, and "
    "rubbing deposits pheromones that mark you as part of the group's shared "
    "scent. It is a social signal, not just affection — cats do the same thing to "
    "each other and to furniture to build one familiar smell across their whole "
    "territory. Your cat is not saying hello. Your cat is filing paperwork.",

    "A cat's tail holds nearly 10% of all the bones in its body — typically 19 to "
    "23 vertebrae out of about 230 total. That tail is a counterbalance, a "
    "rudder, and a full communication channel at once. Cats use it to correct "
    "mid-jump, to steady themselves on narrow ledges, and to broadcast mood: the "
    "straight-up tail with a small hook at the tip is a genuine greeting, one "
    "cats reserve for individuals they actually like. If you get that tail, you "
    "have been approved.",

    "The average house cat shares roughly 95.6% of its DNA with the tiger. The "
    "behaviors carry over almost completely intact: stalking, pouncing, scent "
    "marking, prey-caching, and the same grooming patterns all show up in both. "
    "The main differences are size and tolerance for company. Watching your cat "
    "flatten itself and rear-wiggle before launching at a bottle cap is watching "
    "genuine tiger software running on very small hardware.",

    "A cat's collarbone floats freely and is not attached to any other bone. It "
    "sits suspended in muscle instead, which lets the shoulders move "
    "independently and compress inward. That is the real reason a cat can pour "
    "itself through a gap that looks impossible — if the head and whiskers fit, "
    "the shoulders can be squeezed down to follow. That same free-floating "
    "collarbone also lengthens their stride when sprinting and absorbs impact on "
    "landing. It is a genuinely excellent piece of engineering.",

    "A purr is not always happiness. Cats also purr to self-soothe when they are "
    "stressed, injured, in labor, or dying — the purr shows up in vets' offices "
    "constantly, which is not a happy place for anyone. Some cats also mix a "
    "high-frequency cry into the purr that sits at a very similar pitch to a "
    "human baby's, producing a sound people find almost impossible to ignore. "
    "That specific purr is usually deployed near a food bowl, and it works "
    "every single time.",

    "Cats have around 470 taste buds, compared to about 9,000 in humans — but "
    "their sense of smell is roughly 14 times stronger than ours. For a cat, "
    "food is a smell-first experience, which is why a cat with a stuffy nose "
    "often stops eating entirely. They also have a second smelling organ in the "
    "roof of the mouth, the Jacobson's organ. When your cat freezes with its "
    "mouth slightly open looking deeply stupid, that is the flehmen response — "
    "it is not confused, it is tasting the air.",

    "Cats have whiskers on the backs of their front legs, not just on their "
    "faces. They are called carpal whiskers, and they exist because a cat's "
    "eyesight is genuinely poor at very close range — closer than about a foot, "
    "everything blurs. Once prey is in their paws, the cat effectively cannot "
    "see it, so the leg whiskers take over and report on whether it is still "
    "moving and which way. It is a targeting system for the exact moment their "
    "eyes stop working.",

    "Isaac Newton is widely credited with inventing the cat flap, reportedly "
    "because his cats kept nudging his laboratory door open and ruining his "
    "light experiments. Rather than fight them, he had holes cut in the door so "
    "they could come and go without wrecking the dark room. The story goes that "
    "he cut a large hole for the cat and a small one for her kittens, apparently "
    "not realizing they would just follow her through the big one. Possibly the "
    "greatest physicist in history, defeated entirely by cats.",
]

# ─── Engagement closers (drive comments) ────────────────────────────
QUESTIONS = [
    "Does your cat do this? 🐾",
    "Tag someone whose cat does this 😹",
    "Did you already know this one?",
    "Which one of your cats is this? 😭",
    "Be honest — is this your cat?",
    "Tell me your cat does this too 🥹",
    "Comment your cat's name 🎀",
    "Send this to your cat person 💌",
    "Is this your cat or is this your cat?",
    "Who else's cat is guilty of this? 😼",
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
    """A LONG cat fact + engagement question + #kitty + rotating hashtags."""
    fact = random.choice(CAT_FACTS)
    question = random.choice(QUESTIONS)

    tags = [BRAND_TAG]
    tags += random.sample(CAT_HASHTAGS, k=random.randint(4, 6))
    tags += random.sample(REACH_HASHTAGS, k=random.randint(2, 4))
    # de-dup while preserving order (brand tag stays first)
    seen, ordered = set(), []
    for t in tags:
        if t.lower() not in seen:
            seen.add(t.lower())
            ordered.append(t)

    return f"{fact}\n\n{question}\n\n{' '.join(ordered)}"


if __name__ == "__main__":
    lengths = []
    for _ in range(3):
        c = generate_caption()
        lengths.append(len(c))
        print(c)
        print("-" * 60)
    print(f"caption lengths: {lengths} chars")
