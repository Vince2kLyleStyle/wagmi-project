"""
Fader v2 — Per-Niche Configuration
Each niche gets its own captions, hashtags, and content strategy.

Captions: Proven viral long-form hooks. Same two captions across all niches
for maximum algorithm consistency.
"""

import random

# ─── Viral Captions (proven performers — do NOT change) ─────────────
# These exact captions drive engagement. Used across all niches.
VIRAL_CAPTIONS = [
    (
        "1997년 개봉한 영화 Titanic은 잭과 로즈의 운명적인 사랑을 통해 비극 속에서도 오래 남는 감정의 깊이를 보여주는 작품입니다. "
        "화려한 연출보다 인물의 감정에 더 집중한 제임스 카메론 감독의 스타일은 지금 다시 봐도 묘하게 가슴을 울리죠. "
        "배가 침몰하는 장면이 아닌, 두 사람이 서로를 바라보던 순간들이 더 강하게 기억에 남는 영화이기도 합니다. "
        "이 감정을 완성해주는 곡이 바로 셀린 디온의 \"My Heart Will Go On\"입니다. "
        "처음 들으면 잔잔한데, 어느 순간 자연스럽게 가슴이 벅차오르는 느낌을 줍니다. "
        "특히 후반부의 고조되는 보컬은 영화 속 잭과 로즈의 마지막 장면과 겹쳐지면서 괜히 마음이 서늘해지기도 하고요. "
        "많은 분들이 \"이 노래가 나오면 왜 그 장면이 자동으로 떠오르는지 모르겠다\"고 말하는데, 그만큼 영화와 음악이 자연스럽게 얽혀 있는 곡입니다. "
        "1998년 아카데미 주제가상을 비롯해 여러 상을 휩쓴 건 단지 인기 때문만은 아닙니다. "
        "누가 들어도 '한 시대의 감정'을 담고 있다는 게 느껴지고, 시간이 지나도 촌스러워지지 않는 힘이 있거든요. "
        "오랜만에 다시 들으면, 괜히 조용한 밤에 혼자 영화 한 편을 끝낸 것 같은 기분이 듭니다. "
        "흥미롭게도 이 노래는 처음부터 만들어진 게 아니에요. "
        "제임스 호너가 영화 스코어를 작업하다가 엔딩 크레딧에 보컬 버전을 넣고 싶어해서 급히 만든 곡인데, "
        "셀린 디온 본인은 데모를 듣고 \"별로 매력적이지 않다\"고 거절하려 했대요. "
        "남편이자 매니저였던 르네 안젤릴이 설득해서 한 번만 녹음해보자고 해서 겨우 완성됐죠. "
        "그런데 그 한 번의 녹음으로 역사적인 히트곡이 탄생한 거예요. "
        "호너는 원래 노르웨이 가수 시셀을 염두에 뒀지만, 결국 디온의 목소리가 영화와 완벽하게 맞아떨어졌습니다. "
        "이 노래는 단순히 타이타닉의 테마를 넘어, 사랑과 상실의 보편적인 감정을 상징하는 문화 아이콘이 됐어요. "
        "1998년 그래미에서 올해의 레코드상과 올해의 노래상을 포함해 4관왕을 차지했고, "
        "전 세계적으로 1,800만 장 이상 팔리며 디온의 시그니처 송이 됐죠. "
        "최근에는 2025년 미국 의회도서관 국가 녹음 등록부에 등재되면서 '문화적으로 중요한 작품'으로 공식 인정받았습니다. "
        "심지어 팬데믹 기간에는 이웃들을 위해 발코니에서 피아노로 연주하는 사람들도 있었고, "
        "스포츠 하이라이트에 키 체인지 부분을 삽입하는 밈까지 생길 정도로 대중문화에 깊이 스며들었어요."
        "\n#사실 #지식 #기술 #과학 #트렌드"
    ),
    (
        "#Japan is turning footsteps into electricity! Using piezoelectric tiles, "
        "every step you take generates a small amount of energy. Millions of steps "
        "together can power LED lights and displays in busy places like Shibuya Station. "
        "A brilliant way to create a sustainable and smart city \u2022 turning m..."
    ),
]

# ─── Niche Profiles ──────────────────────────────────────────────────
# All niches share the same proven viral captions.
# Each niche defines its own hashtags for discoverability.

NICHE_PROFILES = {
    "trading": {
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
        "hashtags": [
            "#brainrot", "#facts", "#didyouknow", "#mindblown", "#unserious",
            "#absurd", "#humor", "#funfacts", "#interestingfacts",
            "#comedy", "#relatable", "#random", "#chaotic",
            "#themoreyouknow", "#todayilearned", "#randomfacts",
            "#fyp", "#viral", "#foryou", "#explore",
        ],
        "hashtag_count": (3, 6),
    },

    "gambling": {
        "hashtags": [
            "#gambling", "#casino", "#poker", "#slots", "#blackjack",
            "#sportsbetting", "#betting", "#bigwin", "#jackpot",
            "#fyp", "#viral", "#explore",
        ],
        "hashtag_count": (3, 5),
    },

    "hustle": {
        "hashtags": [
            "#hustle", "#motivation", "#grindset", "#mindset",
            "#entrepreneur", "#success", "#wealth",
            "#fyp", "#viral", "#explore",
        ],
        "hashtag_count": (3, 6),
    },

    "fitness": {
        "hashtags": [
            "#fitness", "#gym", "#workout", "#fitnessmotivation",
            "#bodybuilding", "#gains", "#gymlife",
            "#fyp", "#viral", "#explore",
        ],
        "hashtag_count": (3, 5),
    },
}


def get_niche_caption(niche: str) -> str:
    """Pick one of the proven viral captions + niche-specific hashtags."""
    profile = NICHE_PROFILES.get(niche)
    if not profile:
        profile = NICHE_PROFILES.get("memes", list(NICHE_PROFILES.values())[0])

    caption = random.choice(VIRAL_CAPTIONS)

    min_tags, max_tags = profile["hashtag_count"]
    tag_count = random.randint(min_tags, max_tags)
    tags = random.sample(profile["hashtags"], k=min(tag_count, len(profile["hashtags"])))

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
