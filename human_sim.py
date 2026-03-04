"""
Fader v2 — Human Simulation Module
Performs realistic "human browsing" actions before/after posting
to warm up the session and avoid looking robotic.
"""

import random
import time
import sys

from instagrapi import Client

import config


def _rand_sleep(lo: float, hi: float, label: str = ""):
    """Sleep a random duration between lo and hi seconds, with countdown."""
    duration = random.uniform(lo, hi)
    if label:
        print(f"  [{label}] pausing {duration:.0f}s ...", end="", flush=True)
    time.sleep(duration)
    if label:
        print(" done.", flush=True)


def warmup_session(cl: Client) -> None:
    """
    Warm-up phase: spend 30-60 min just browsing (no posting).
    Views stories and likes feed posts to look like a real user.
    """
    warmup_sec = random.randint(config.WARMUP_MIN_SEC, config.WARMUP_MAX_SEC)
    print(f"\n{'='*60}")
    print(f"  WARM-UP PHASE — browsing for ~{warmup_sec // 60} minutes")
    print(f"{'='*60}")

    deadline = time.time() + warmup_sec
    actions_done = 0

    while time.time() < deadline:
        action = random.choice(["story", "feed_like", "explore", "pause"])

        try:
            if action == "story":
                _view_random_stories(cl, 1, 4)
            elif action == "feed_like":
                _like_random_feed(cl, 1, 2)
            elif action == "explore":
                _browse_explore(cl)
            else:
                _rand_sleep(15, 60, "idle scroll")
        except Exception as e:
            print(f"  [warmup] non-critical error: {e}")

        actions_done += 1
        # Random pause between warm-up actions
        _rand_sleep(20, 90)

    print(f"  Warm-up complete — {actions_done} actions performed.\n")


def pre_upload_actions(cl: Client) -> None:
    """Simulate human browsing right before an upload."""
    print("  [pre-upload] simulating human activity...")

    # View some stories
    story_count = random.randint(config.PRE_STORIES_MIN, config.PRE_STORIES_MAX)
    _view_random_stories(cl, story_count // 2, story_count)

    # Like some feed posts
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
    """View stories from random users in the timeline tray."""
    try:
        count = random.randint(lo, max(lo, hi))
        reels_tray = cl.get_reels_tray_feed()

        if not reels_tray or not hasattr(reels_tray, '__iter__'):
            print("  [stories] no story tray available")
            return

        tray_list = list(reels_tray)
        if not tray_list:
            print("  [stories] empty tray")
            return

        to_view = random.sample(tray_list, k=min(count, len(tray_list)))
        for reel in to_view:
            try:
                user_id = None
                if hasattr(reel, 'user'):
                    user_id = reel.user.pk if hasattr(reel.user, 'pk') else None
                elif hasattr(reel, 'id'):
                    user_id = reel.id

                if user_id:
                    stories = cl.user_stories(user_id)
                    if stories:
                        # Mark as seen by viewing
                        story = random.choice(stories)
                        cl.story_seen([story.pk])
                        print(f"    viewed story from user {user_id}")
            except Exception:
                pass
            _rand_sleep(2, 8)
    except Exception as e:
        print(f"  [stories] error: {e}")


def _like_random_feed(cl: Client, lo: int, hi: int) -> None:
    """Like random posts from the user's timeline feed."""
    try:
        count = random.randint(lo, max(lo, hi))
        # Get timeline feed medias
        feed = cl.get_timeline_feed()

        if not feed or "feed_items" not in feed:
            print("  [likes] no feed available")
            return

        items = [
            item.get("media_or_ad")
            for item in feed.get("feed_items", [])
            if item.get("media_or_ad")
        ]

        if not items:
            return

        to_like = random.sample(items, k=min(count, len(items)))
        for media in to_like:
            try:
                media_id = media.get("pk") or media.get("id")
                if media_id:
                    cl.media_like(media_id)
                    print(f"    liked media {media_id}")
            except Exception:
                pass
            _rand_sleep(3, 12)
    except Exception as e:
        print(f"  [likes] error: {e}")


def _browse_explore(cl: Client) -> None:
    """Briefly hit the explore endpoint to look like real browsing."""
    try:
        # Just fetch explore — we don't need to do anything with it
        cl.explore_page()
        print("    browsed explore page")
    except Exception as e:
        print(f"  [explore] error: {e}")
    _rand_sleep(5, 15)
