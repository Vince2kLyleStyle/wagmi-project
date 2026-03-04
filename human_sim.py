"""
Fader v2 — Human Simulation Module
Performs realistic browsing actions before/after posting
to warm up the session and reduce detection risk.

Verified against instagrapi 2.x API — only calls methods that actually exist.
"""

import random
import time

from instagrapi import Client

import config


def _rand_sleep(lo: float, hi: float, label: str = ""):
    """Sleep a random duration between lo and hi seconds."""
    duration = random.uniform(lo, hi)
    if label:
        print(f"  [{label}] pausing {duration:.0f}s ...", end="", flush=True)
    time.sleep(duration)
    if label:
        print(" done.", flush=True)


def warmup_session(cl: Client) -> None:
    """
    Warm-up phase: browse for a while before posting.
    Views stories and likes feed posts to generate normal-looking activity.
    """
    warmup_sec = random.randint(config.WARMUP_MIN_SEC, config.WARMUP_MAX_SEC)
    print(f"\n{'='*60}")
    print(f"  WARM-UP PHASE — browsing for ~{warmup_sec // 60} minutes")
    print(f"{'='*60}")

    deadline = time.time() + warmup_sec
    actions_done = 0

    while time.time() < deadline:
        action = random.choice(["story", "feed_like", "pause"])

        try:
            if action == "story":
                _view_random_stories(cl, 1, 4)
            elif action == "feed_like":
                _like_random_feed(cl, 1, 2)
            else:
                _rand_sleep(15, 60, "idle scroll")
        except Exception as e:
            print(f"  [warmup] non-critical error: {e}")

        actions_done += 1
        _rand_sleep(20, 90)

    print(f"  Warm-up complete — {actions_done} actions performed.\n")


def pre_upload_actions(cl: Client) -> None:
    """Simulate human browsing right before an upload."""
    print("  [pre-upload] simulating human activity...")

    story_count = random.randint(config.PRE_STORIES_MIN, config.PRE_STORIES_MAX)
    _view_random_stories(cl, story_count // 2, story_count)

    like_count = random.randint(config.PRE_LIKES_MIN, config.PRE_LIKES_MAX)
    _like_random_feed(cl, like_count // 2, like_count)

    _rand_sleep(5, 20, "settling")


def post_upload_actions(cl: Client) -> None:
    """Simulate post-upload browsing (optional likes)."""
    like_count = random.randint(config.POST_LIKES_MIN, config.POST_LIKES_MAX)
    if like_count > 0:
        print(f"  [post-upload] liking {like_count} posts...")
        _like_random_feed(cl, 1, like_count)


# ─── Internal Helpers ───────────────────────────────────────────────

def _view_random_stories(cl: Client, lo: int, hi: int) -> None:
    """
    View stories from random users in the timeline tray.

    get_reels_tray_feed() returns a raw dict from Instagram's API.
    The "tray" key contains a list of reel dicts, each with a "user" dict
    containing an "pk" field.
    """
    try:
        count = random.randint(lo, max(lo, hi))
        tray_response = cl.get_reels_tray_feed()

        if not isinstance(tray_response, dict):
            print("  [stories] unexpected tray response type")
            return

        tray_list = tray_response.get("tray", [])
        if not tray_list:
            print("  [stories] empty tray")
            return

        to_view = random.sample(tray_list, k=min(count, len(tray_list)))
        for reel in to_view:
            try:
                # Each reel in the tray is a dict with "user" -> "pk"
                user_info = reel.get("user", {})
                user_id = user_info.get("pk")

                if not user_id:
                    continue

                stories = cl.user_stories(user_id)
                if stories:
                    story = random.choice(stories)
                    # story_seen takes a list of story PKs
                    cl.story_seen([story.pk])
                    print(f"    viewed story from user {user_id}")
            except Exception:
                pass
            _rand_sleep(2, 8)
    except Exception as e:
        print(f"  [stories] error: {e}")


def _like_random_feed(cl: Client, lo: int, hi: int) -> None:
    """
    Like random posts from the user's timeline feed.

    get_timeline_feed() returns a raw dict. The "feed_items" key contains
    a list of dicts, each with a "media_or_ad" dict that has "pk" or "id".
    """
    try:
        count = random.randint(lo, max(lo, hi))
        feed = cl.get_timeline_feed()

        if not isinstance(feed, dict):
            print("  [likes] unexpected feed response type")
            return

        feed_items = feed.get("feed_items", [])
        if not feed_items:
            print("  [likes] no feed items available")
            return

        items = []
        for item in feed_items:
            media = item.get("media_or_ad")
            if media:
                items.append(media)

        if not items:
            return

        to_like = random.sample(items, k=min(count, len(items)))
        for media in to_like:
            try:
                media_id = media.get("pk") or media.get("id")
                if media_id:
                    cl.media_like(str(media_id))
                    print(f"    liked media {media_id}")
            except Exception:
                pass
            _rand_sleep(3, 12)
    except Exception as e:
        print(f"  [likes] error: {e}")
