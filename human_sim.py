"""
Fader v2 — Human Simulation
Realistic warm-up and browsing behavior to make the session look organic.
A real person doesn't open Instagram and immediately start uploading 70 Reels.
They scroll, they like, they view stories — THEN maybe they post something.
"""

import random
import time

from instagrapi import Client


def _pause(lo: float, hi: float, label: str = ""):
    """Sleep a random duration."""
    duration = random.uniform(lo, hi)
    if label:
        print(f"  [{label}] pausing {duration:.0f}s ...", end="", flush=True)
    time.sleep(duration)
    if label:
        print(" done.", flush=True)


def warmup_session(cl: Client, intensity: str = "normal") -> None:
    """
    Warm up the session with organic-looking activity before uploading.

    intensity:
        "light"  — Quick warm-up (~1-2 min): like 2-3 posts
        "normal" — Standard (~3-8 min): scroll feed, like posts, view profiles
        "full"   — Deep warm-up (~8-15 min): all of the above + stories + explore
    """
    print(f"\n{'='*60}")
    print(f"  WARM-UP — building organic session activity ({intensity})")
    print(f"{'='*60}")

    actions_done = 0

    # ─── Phase 1: Scroll and like feed posts ────────────────────
    try:
        feed = cl.get_timeline_feed()
        if isinstance(feed, dict):
            items = []
            for item in feed.get("feed_items", []):
                media = item.get("media_or_ad")
                if media:
                    items.append(media)

            if items:
                # Like some posts (varies by intensity)
                like_count = {
                    "light": random.randint(2, 3),
                    "normal": random.randint(3, 6),
                    "full": random.randint(5, 10),
                }.get(intensity, random.randint(3, 6))

                like_count = min(like_count, len(items))
                to_like = random.sample(items, k=like_count)

                for media in to_like:
                    try:
                        media_id = media.get("pk") or media.get("id")
                        if media_id:
                            cl.media_like(str(media_id))
                            actions_done += 1
                            print(f"    liked post {media_id}")
                    except Exception:
                        pass
                    _pause(3, 10)
    except Exception as e:
        print(f"  [warmup] feed error (non-fatal): {e}")

    # ─── Phase 2: Browse a couple of user profiles ──────────────
    if intensity in ("normal", "full"):
        try:
            _pause(5, 15, "browsing")
            # View 1-3 user profiles from the feed
            feed = cl.get_timeline_feed()
            if isinstance(feed, dict):
                users_seen = set()
                for item in feed.get("feed_items", []):
                    media = item.get("media_or_ad")
                    if media:
                        user = media.get("user", {})
                        uid = user.get("pk")
                        if uid and uid not in users_seen:
                            users_seen.add(uid)

                profile_count = min(random.randint(1, 3), len(users_seen))
                for uid in list(users_seen)[:profile_count]:
                    try:
                        cl.user_info(uid)
                        actions_done += 1
                        print(f"    viewed profile {uid}")
                    except Exception:
                        pass
                    _pause(4, 12)
        except Exception as e:
            print(f"  [warmup] profile browse error (non-fatal): {e}")

    # ─── Phase 3: View stories (full warm-up only) ──────────────
    if intensity == "full":
        try:
            _pause(5, 15, "stories")
            reels_tray = cl.get_reels_tray_feed()
            if hasattr(reels_tray, 'tray') or isinstance(reels_tray, dict):
                tray = reels_tray if isinstance(reels_tray, list) else []
                if isinstance(reels_tray, dict):
                    tray = reels_tray.get("tray", [])
                elif hasattr(reels_tray, 'tray'):
                    tray = reels_tray.tray or []

                story_count = min(random.randint(2, 5), len(tray))
                for reel in tray[:story_count]:
                    try:
                        uid = reel.get("user", {}).get("pk") if isinstance(reel, dict) else getattr(reel, 'user', None)
                        if uid:
                            pk = uid if isinstance(uid, (int, str)) else getattr(uid, 'pk', None)
                            if pk:
                                cl.user_stories(int(pk))
                                actions_done += 1
                                print(f"    viewed stories for user {pk}")
                    except Exception:
                        pass
                    _pause(3, 8)
        except Exception as e:
            print(f"  [warmup] stories error (non-fatal): {e}")

    # ─── Phase 4: Brief explore page scroll (full only) ─────────
    if intensity == "full":
        try:
            _pause(3, 8, "explore")
            # Just hit the explore endpoint to register the activity
            cl.explore()
            actions_done += 1
            print(f"    browsed explore page")
        except Exception:
            pass

    # ─── Final pause before we start uploading ──────────────────
    if intensity == "full":
        _pause(30, 90, "settling in")
    elif intensity == "normal":
        _pause(15, 45, "settling in")
    else:
        _pause(5, 15, "settling in")

    print(f"  Warm-up done ({actions_done} actions).\n")


def pre_upload_pause() -> None:
    """Short random pause before each upload."""
    _pause(3, 12, "pre-upload")


def post_upload_pause() -> None:
    """Short random pause after each upload."""
    _pause(5, 20, "post-upload")


def between_session_activity(cl: Client) -> None:
    """
    Light activity between upload batches to keep the session looking active.
    Called during long inter-batch delays.
    """
    if random.random() < 0.4:  # 40% chance of mid-session activity
        try:
            feed = cl.get_timeline_feed()
            if isinstance(feed, dict):
                items = []
                for item in feed.get("feed_items", []):
                    media = item.get("media_or_ad")
                    if media:
                        items.append(media)
                if items:
                    media = random.choice(items)
                    media_id = media.get("pk") or media.get("id")
                    if media_id:
                        cl.media_like(str(media_id))
                        print(f"    [mid-session] liked post {media_id}")
        except Exception:
            pass
