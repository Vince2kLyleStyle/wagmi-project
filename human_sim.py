"""
Fader v2 — Human Simulation (Lite)
Just enough delay and activity to not look like a script firing uploads
back-to-back. Nothing fancy.
"""

import random
import time

from instagrapi import Client

import config


def _pause(lo: float, hi: float, label: str = ""):
    """Sleep a random duration."""
    duration = random.uniform(lo, hi)
    if label:
        print(f"  [{label}] pausing {duration:.0f}s ...", end="", flush=True)
    time.sleep(duration)
    if label:
        print(" done.", flush=True)


def warmup_session(cl: Client) -> None:
    """
    Quick warm-up: like a few posts from the timeline so the session
    has some non-upload activity before we start posting.
    Takes ~2-5 minutes, not 30-60.
    """
    print(f"\n{'='*60}")
    print(f"  WARM-UP — liking a few posts to warm the session")
    print(f"{'='*60}")

    try:
        feed = cl.get_timeline_feed()
        if not isinstance(feed, dict):
            print("  [warmup] couldn't fetch feed, skipping")
            return

        items = []
        for item in feed.get("feed_items", []):
            media = item.get("media_or_ad")
            if media:
                items.append(media)

        if not items:
            print("  [warmup] no feed items, skipping")
            return

        # Like 3-6 random posts
        count = min(random.randint(3, 6), len(items))
        to_like = random.sample(items, k=count)

        for media in to_like:
            try:
                media_id = media.get("pk") or media.get("id")
                if media_id:
                    cl.media_like(str(media_id))
                    print(f"    liked media {media_id}")
            except Exception:
                pass
            _pause(3, 10)

    except Exception as e:
        print(f"  [warmup] error (non-fatal): {e}")

    print(f"  Warm-up done.\n")


def pre_upload_pause() -> None:
    """Short random pause before each upload."""
    _pause(2, 8, "pre-upload")


def post_upload_pause() -> None:
    """Short random pause after each upload."""
    _pause(3, 12, "post-upload")
