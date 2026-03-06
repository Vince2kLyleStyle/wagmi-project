"""
Fader v2 — Per-Niche Configuration
Each niche gets its own captions, hashtags, and content strategy.

Caption style: Long-form informational hooks with trailing "..."
to maximize engagement and watch time. Each caption reads like a
mini fact/story that draws people in.
"""

import random

# ─── Niche Profiles ──────────────────────────────────────────────────
# Each niche defines:
#   - caption_templates: Long-form informational hook captions
#   - hashtags: Niche-specific hashtag pool
#   - hashtag_count: (min, max) hashtags per post
#
# Caption format: "#Topic + fact/hook + explanation + trailing ..."
# Example: "#Japan is turning footsteps into electricity! Using piezoelectric
#           tiles, every step generates energy. A brilliant way to create
#           a sustainable and smart city • turning m..."

NICHE_PROFILES = {
    "trading": {
        "caption_templates": [
            "#WallStreet traders used to communicate through hand signals on the trading floor! Each gesture represented a different order — buy, sell, quantity. Despite billions moving through these signals, the system was nearly flawless • a lost art of financial comm...",
            "#Bitcoin was mass-adopted by El Salvador as legal tender! Every citizen received $30 in BTC through the Chivo wallet. Street vendors, taxi drivers, even McDonald's accepted it. A tiny country became the world's biggest crypto experiment • reshaping how we think about mo...",
            "#Japan's stock market was once the largest in the world! In 1989, the Tokyo Stock Exchange surpassed NYSE in market cap. Japanese real estate was so overvalued that Tokyo's Imperial Palace was worth more than all of California • the bubble that changed investing fore...",
            "#Renaissance Technologies has averaged 66% annual returns since 1988! Jim Simons hired mathematicians, not MBAs. Their Medallion Fund used pattern recognition and data science before anyone called it AI • the most successful hedge fund in hist...",
            "#Options trading volume has exploded 500% since 2019! Retail traders discovered 0DTE contracts — options that expire the same day. Some turn $500 into $50,000 in hours. The risk is insane but the potential gains are unmatched • changing how a generation trad...",
            "#Warren Buffett made 99% of his wealth after age 50! He started investing at age 11 and didn't hit his first billion until 56. Compound interest is the real cheat code — time in the market beats timing the market every single time • the power of patie...",
            "#The forex market moves $7.5 trillion every single day! That's more than the GDP of most countries combined. It never sleeps — Tokyo opens, London takes over, then New York. Trillions flowing through invisible channels 24 hours a day • the world's largest financial mar...",
            "#Michael Burry predicted the 2008 crash and made $700 million! He spotted the housing bubble when everyone called him crazy. Banks laughed at his credit default swaps. Then the entire financial system collapsed exactly like he said • one man against Wall Str...",
            "#Dark pools handle over 40% of all US stock trades! These private exchanges let institutions trade massive blocks without moving the market. Regular investors can't see the orders until after they execute • a hidden layer of the market most people never kn...",
            "#The fear and greed index predicted every major crash! When euphoria peaks, smart money exits. When fear maxes out, they buy everything. The crowd is almost always wrong at the extremes • emotions are the biggest enemy in trad...",
            "#South Korea has the highest retail trading participation in the world! Over 70% of young adults actively trade stocks. They call it the 'stock investment craze' — entire social circles revolve around market moves • a nation obsessed with financial mark...",
            "#George Soros broke the Bank of England in 1992! He shorted the British pound with $10 billion and forced the UK out of the European Exchange Rate Mechanism. He made $1 billion in a single day • the trade that shook an entire nat...",
            "#Algorithmic trading now accounts for 70% of all market volume! Machines execute trades in microseconds — faster than a human can blink. They detect patterns across millions of data points simultaneously • the stock market is now a battle between supercomput...",
            "#The dot-com bubble wiped out $5 trillion in market value! Companies with zero revenue had billion-dollar valuations. Pets.com raised $82 million and went bankrupt in 268 days. The lessons from 2000 are still relevant today • history always rhym...",
            "#Cathie Wood turned $5 billion into $50 billion with ARK Invest! She bet everything on innovation — Tesla, Bitcoin, genomics, AI. Her conviction trades made her the most famous investor of a generation • high risk, high conviction inves...",
        ],
        "hashtags": [
            "#trading", "#trader", "#forex", "#stocks", "#crypto",
            "#daytrading", "#stockmarket", "#forextrader", "#bitcoin",
            "#investing", "#wallstreet", "#tradingview", "#options",
            "#swingtrading", "#cryptotrading", "#financialfreedom",
            "#tradingtips", "#priceaction", "#technicalanalysis",
            "#tradinglife", "#fyp", "#viral", "#explore",
        ],
        "hashtag_count": (3, 6),
    },

    "memes": {
        "caption_templates": [
            "#Laughter is literally contagious — your brain has mirror neurons that fire when you hear someone laugh! Scientists found that laughter activates the same brain regions as a reward. That's why funny videos hit different at 3am • your brain is wired to find this funn...",
            "#The average person laughs 17 times a day but watches 45 minutes of memes! Social media has rewired our humor — we process jokes faster than any generation before us. A meme that took 2 seconds to make can reach 50 million people overnight • the economics of funn...",
            "#Scientists discovered that people who laugh more live up to 8 years longer! Laughter reduces cortisol, boosts immunity, and releases endorphins. Watching funny videos is literally medicine — your doctor should be prescribing memes • the science behind why you can't stop scrol...",
            "#The word 'meme' was invented by Richard Dawkins in 1976! He described it as a cultural unit that spreads from brain to brain — like a gene but for ideas. He never imagined it would become a picture of a cat with Impact font • from evolutionary biology to internet cult...",
            "#Your brain processes humor in 400 milliseconds! That's faster than you can consciously think. The punchline hits your amygdala before your prefrontal cortex even catches up. That's why you laugh before you fully understand the joke • neuroscience of com...",
            "#The most shared video of all time was a comedy clip! Funny content gets 3x more shares than any other type. Humor triggers the brain's reward center AND the social bonding center simultaneously — you literally feel compelled to share it • why memes dominate the inter...",
            "#Babies start laughing at 3-4 months old — before they can even talk! Laughter is one of the first social behaviors humans develop. It's hardwired into our DNA as a bonding mechanism. We were built to find things funny • humor is literally in our gen...",
            "#Japan has a laughing festival where thousands of people laugh for no reason! The Warai Matsuri has been happening for over 1,000 years. Participants laugh together until real laughter takes over. The entire town joins in • ancient proof that laughter is the best medic...",
            "#Comedians have higher IQs on average than the general population! Studies show humor requires complex pattern recognition, timing, and social intelligence. Making someone laugh is one of the hardest cognitive tasks the brain can perform • comedy is genius in disg...",
            "#The internet creates 500,000 new memes every single day! That's more creative output than the entire Renaissance produced in a century. Most die instantly but the ones that survive become part of global culture • we're living in the golden age of hum...",
            "#Laughter burns 40 calories per 15 minutes of genuine laughing! Your abs contract, your heart rate increases, and your breathing changes. Watching memes for an hour is basically a workout — science says so • the fitness routine nobody talks ab...",
            "#Psychologists found that inside jokes create stronger bonds than deep conversations! Shared humor activates the same neural pathways as love and trust. That meme your friend group quotes constantly is literally strengthening your friendships • humor is the glue of human connect...",
            "#Monkeys laugh when they're tickled — humor evolved millions of years ago! Great apes have a 'play face' identical to human laughter. Dogs do a breathy panting when they're amused. Humor isn't uniquely human — it's an ancient survival mechanism • even nature thinks things are fun...",
            "#The funniest time to scroll memes is between 11pm and 2am! Your prefrontal cortex gets tired and your inhibitions drop — that's why everything is funnier late at night. Sleep deprivation actually lowers your humor threshold • science explains the 3am meme sess...",
            "#A study found that couples who laugh together are 67% more likely to stay together! Shared humor creates a private world between two people. Inside jokes become a love language. The funniest couples have the strongest relationships • laughter is the secret to last...",
        ],
        "hashtags": [
            "#memes", "#funny", "#comedy", "#humor", "#relatable",
            "#lol", "#meme", "#funnyvideos", "#funnymemes",
            "#dankmemes", "#memesdaily", "#comedyvideos",
            "#dailymemes", "#viralvideos", "#trending",
            "#fyp", "#viral", "#explore", "#foryou",
        ],
        "hashtag_count": (3, 5),
    },

    "brainrot": {
        "caption_templates": [
            "#Scientists proved that overthinking literally shrinks your brain! The prefrontal cortex physically reduces in volume from chronic stress and rumination. Meanwhile the people who just vibe and don't think about anything are neurologically thriving • ignorance really is bl...",
            "#The average person has 6,200 thoughts per day and 80% of them are completely useless! Your brain is running background processes about things that don't matter. That random thought about something embarrassing from 2017? Your brain chose that over something productive • mental chaos is the default set...",
            "#Goldfish actually have a longer attention span than humans now! Since smartphones, the human attention span dropped from 12 seconds to 8.25 seconds. A goldfish sits at 9 seconds. We literally devolved past aquarium pets • evolution went in rever...",
            "#There's a town in Norway where the sun doesn't set for 76 days straight! People in Hammerfest experience continuous daylight from May to July. Sleep schedules become meaningless. Some residents just stop checking the time altogether • imagine the vibes of losing all concept of ti...",
            "#NASA spent $12 billion developing a pen that works in zero gravity! Meanwhile Russian cosmonauts just used a pencil. Sometimes the simplest solution is right there but we're too busy overcomplicating everything • the most expensive pen in human hist...",
            "#Octopuses have three hearts and blue blood! Two hearts pump blood to the gills while the third pumps it to the body. When they swim, the main heart actually stops beating. They literally have a cardiac event every time they move • the most dramatic animal in the oc...",
            "#There's a lake in Africa that turns animals into stone! Lake Natron in Tanzania has such extreme alkalinity that any animal that dies in it becomes calcified. Birds frozen mid-flight, bats with wings spread — perfectly preserved like statues • nature's most terrifying art gal...",
            "#The inventor of the Pringles can is buried in one! Fredric Baur designed the iconic tube shape and was so proud of it that his family honored his wish to be cremated and placed inside a Pringles can • once you pop you literally can't st...",
            "#Honey never expires — archaeologists found 3,000-year-old honey in Egyptian tombs that was still perfectly edible! The unique chemical composition creates an environment where bacteria literally cannot survive. Ancient Egyptians knew this and used it to preserve everything • the only food that lasts fore...",
            "#Bananas are technically berries but strawberries aren't! Botanically, a berry must come from a single ovary flower. Bananas, grapes, and even watermelons qualify. Strawberries, raspberries, and blackberries are imposters • everything you know about fruit is a l...",
            "#There's a species of jellyfish that is biologically immortal! Turritopsis dohrnii can revert back to its juvenile stage after reaching maturity. It literally ages backward. Scientists have been studying it for decades trying to unlock the secret • the creature that broke bio...",
            "#Cleopatra lived closer in time to the iPhone than to the building of the Great Pyramid! The pyramids were built around 2560 BC. Cleopatra lived around 30 BC. The iPhone launched in 2007. The timeline of human history makes absolutely zero sense • nothing is real and time is a fl...",
            "#A group of flamingos is called a 'flamboyance'! A group of crows is a 'murder.' A group of pugs is called a 'grumble.' The people who named animal groups were clearly having the time of their lives • the English language peaked with collective nou...",
            "#Your body replaces every single atom every 7-10 years! You are literally not the same person you were a decade ago — physically, atomically, completely different. The you from 2016 doesn't exist anymore in any measurable way • existential crisis in 3, 2, ...",
            "#There are more possible chess games than atoms in the observable universe! The Shannon number estimates 10^120 possible games. The universe has roughly 10^80 atoms. A board game has more complexity than the cosmos itself • the game that broke mathem...",
            "#Cows have best friends and get stressed when separated! Studies show their heart rate increases and cortisol spikes when their companion is taken away. They also produce more milk when they're happy. Cows are emotionally complex beings • the friendship nobody talks ab...",
            "#The shortest war in history lasted 38 minutes! In 1896, the British Empire declared war on Zanzibar. The Sultan's palace was bombarded and he surrendered in under an hour. An entire war from declaration to surrender in the time it takes to watch an episode of something • speed-running world hist...",
            "#Wombat poop is cube-shaped! They produce about 100 cube-shaped droppings per night. Scientists finally figured out it's because of the varying elasticity of their intestinal walls. They use the cubes to mark territory because they don't roll away • the most engineered poop in nat...",
            "#Oxford University is older than the Aztec Empire! Teaching existed at Oxford as early as 1096. The Aztec Empire wasn't founded until 1428. A British university was producing graduates for 300 years before the Aztecs even started building Tenochtitlan • the timeline of civilization is bro...",
            "#Sharks existed before trees did! Sharks have been around for about 450 million years. Trees didn't appear until about 350 million years ago. Sharks were swimming in the ocean for 100 million years before the first tree ever grew • the original apex pred...",
        ],
        "hashtags": [
            "#brainrot", "#facts", "#didyouknow", "#mindblown", "#unserious",
            "#absurd", "#humor", "#funfacts", "#interestingfacts",
            "#comedy", "#relatable", "#random", "#chaotic",
            "#themoreyouknow", "#todayilearned", "#randomfacts",
            "#fyp", "#viral", "#foryou", "#explore",
        ],
        "hashtag_count": (3, 6),
    },

    # ─── Legacy niches (kept for backward compat, not actively used) ──
    "gambling": {
        "caption_templates": [
            "#Vegas casinos pump oxygen into the air to keep gamblers awake longer! The entire floor is designed with no clocks, no windows, and maze-like layouts so you lose track of time. Every design choice is engineered to keep you playing • the psychology of casi...",
            "#The MIT Blackjack Team turned $300,000 into $5 million using card counting! A group of college students beat casinos for over a decade. They used sophisticated signals and rotating teams. Vegas eventually banned them all — but the money was already made • students vs the hou...",
        ],
        "hashtags": [
            "#gambling", "#casino", "#poker", "#slots", "#blackjack",
            "#sportsbetting", "#betting", "#bigwin", "#jackpot",
            "#fyp", "#viral", "#explore",
        ],
        "hashtag_count": (3, 5),
    },

    "hustle": {
        "caption_templates": [
            "#Elon Musk slept on the Tesla factory floor for months! While building the Model 3, he refused to leave the production line. He worked 120-hour weeks and said it nearly broke him. The obsession is what separates builders from dreamers • the cost of changing the wor...",
            "#The average millionaire has 7 streams of income! They don't rely on a single paycheck — they build systems that generate money while they sleep. Dividends, real estate, businesses, royalties. Wealth is built through multiplication, not addition • the blueprint to financial free...",
        ],
        "hashtags": [
            "#hustle", "#motivation", "#grindset", "#mindset",
            "#entrepreneur", "#success", "#wealth",
            "#fyp", "#viral", "#explore",
        ],
        "hashtag_count": (3, 6),
    },

    "fitness": {
        "caption_templates": [
            "#Your muscles don't actually grow in the gym — they grow while you sleep! Training creates micro-tears in muscle fibers. Growth hormone released during deep sleep repairs and enlarges them. Skipping sleep is literally skipping gains • recovery is the real work...",
            "#Arnold Schwarzenegger trained 5 hours a day, 6 days a week! He split sessions into morning and evening to maximize volume. His work ethic was so extreme that other bodybuilders thought he was lying about his routine • the discipline that built a leg...",
        ],
        "hashtags": [
            "#fitness", "#gym", "#workout", "#fitnessmotivation",
            "#bodybuilding", "#gains", "#gymlife",
            "#fyp", "#viral", "#explore",
        ],
        "hashtag_count": (3, 5),
    },
}


def get_niche_caption(niche: str) -> str:
    """
    Generate a long-form informational hook caption with hashtags.
    Format: "#Topic fact/hook + explanation + trailing ..." + hashtags
    """
    profile = NICHE_PROFILES.get(niche)
    if not profile:
        profile = NICHE_PROFILES.get("memes", list(NICHE_PROFILES.values())[0])

    caption = random.choice(profile["caption_templates"])

    min_tags, max_tags = profile["hashtag_count"]
    tag_count = random.randint(min_tags, max_tags)
    tags = random.sample(profile["hashtags"], k=min(tag_count, len(profile["hashtags"])))

    # Caption already has hashtag at start + trailing "..."
    # Append additional hashtags at the bottom
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
