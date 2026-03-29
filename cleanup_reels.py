#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║          CLEANUP — Delete Low-Performing Reels                ║
║          + Pin a Comment on Keepers                           ║
╚═══════════════════════════════════════════════════════════════╝

Scans your posted Reels, deletes ones that flopped, and pins an
engagement comment on the ones worth keeping.

Usage:
    python cleanup_reels.py                       # dry run (preview)
    python cleanup_reels.py --go                  # actually delete + comment
    python cleanup_reels.py --min-views 500       # custom view threshold
    python cleanup_reels.py --min-age 24          # only check posts older than 24h
    python cleanup_reels.py --comment-only        # skip deleting, just pin comments
    python cleanup_reels.py --delete-only         # skip comments, just delete flops

Requires: pip install instagrapi
"""

import argparse
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone

from instagrapi import Client
from instagrapi.exceptions import (
    ChallengeRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
    RateLimitError,
)

import config
import devices

# ─── Defaults ─────────────────────────────────────────────────────────

# Delete reels below this view count
DEFAULT_MIN_VIEWS = 200

# Only evaluate posts older than this many hours (give them time to perform)
DEFAULT_MIN_AGE_HOURS = 24

# How many posts to scan (0 = all)
DEFAULT_SCAN_COUNT = 100

# Pinned comment options — randomly picked per post
PIN_COMMENTS = [
    "Follow for more 😂🔥",
    "Drop a 💀 if this got you",
    "Tag someone who needs to see this 😭",
    "More on the way 🔥 follow so you don't miss",
    "This one hit different 😂 follow for daily laughs",
    "W or L? 👇",
    "Share this with someone who needs a laugh 😂",
    "Follow if this made you laugh 💀",
]

# Delay between API actions to avoid rate limits
ACTION_DELAY_MIN = 3
ACTION_DELAY_MAX = 8


# ─── Client Setup ────────────────────────────────────────────────────

def create_client(session_file=None):
    """Create & login an instagrapi Client."""
    cl = Client()

    if config.PROXY:
        cl.set_proxy(config.PROXY)

    dev = devices.get_device()
    cl.set_device(dev)
    cl.delay_range = [2, 6]

    if session_file and os.path.exists(session_file):
        try:
            cl.load_settings(session_file)
            cl.login(config.USERNAME, config.PASSWORD)
            print(f"  [session] Resumed from {session_file}")
            return cl
        except Exception as e:
            print(f"  [session] Could not resume ({e}), fresh login...")

    cl.login(config.USERNAME, config.PASSWORD)
    print(f"  [session] Logged in as @{config.USERNAME}")

    if session_file:
        os.makedirs(os.path.dirname(session_file), exist_ok=True)
        cl.dump_settings(session_file)

    return cl


# ─── Core Logic ───────────────────────────────────────────────────────

def get_my_reels(cl, amount=100):
    """Fetch your recent reels/clips using the private API (avoids 429s)."""
    user_id = cl.user_id  # already set after login — no extra request needed
    # user_medias_v1 uses the private API instead of public GraphQL
    medias = cl.user_medias_v1(user_id, amount=amount)
    # Filter to only clips/reels (media_type 2 = video, product_type = clips)
    reels = [
        m for m in medias
        if m.media_type == 2 or getattr(m, 'product_type', '') == 'clips'
    ]
    return reels


def get_reel_stats(media):
    """Extract view/like/comment counts from a Media object."""
    views = getattr(media, 'play_count', 0) or getattr(media, 'view_count', 0) or 0
    likes = getattr(media, 'like_count', 0) or 0
    comments = getattr(media, 'comment_count', 0) or 0
    return {
        "views": views,
        "likes": likes,
        "comments": comments,
        "taken_at": media.taken_at,
        "pk": media.pk,
        "id": media.id,
        "caption": (media.caption_text or "")[:60] if hasattr(media, 'caption_text') else "",
    }


def should_delete(stats, min_views, min_age_hours, before_date=None):
    """Decide if a reel should be deleted based on performance."""
    if stats["taken_at"]:
        taken = stats["taken_at"]
        if taken.tzinfo is None:
            taken = taken.replace(tzinfo=timezone.utc)

        # Skip posts that are too new (haven't had time to get views)
        age = datetime.now(timezone.utc) - taken
        if age < timedelta(hours=min_age_hours):
            return False, "too_new"

        # Skip posts after the before_date cutoff (keep those)
        if before_date:
            cutoff = datetime.strptime(before_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if taken >= cutoff:
                return False, "after_cutoff"

    if stats["views"] < min_views:
        return True, "low_views"

    return False, "keeper"


def delete_reel(cl, media_id):
    """Delete a reel. Returns True on success."""
    try:
        result = cl.media_delete(media_id)
        return bool(result)
    except (PleaseWaitFewMinutes, RateLimitError) as e:
        print(f"    [!!] Rate limited: {e}")
        return False
    except Exception as e:
        print(f"    [!!] Delete error: {e}")
        return False


def pin_comment(cl, media_id, text):
    """Post a comment and pin it. Returns True on success."""
    try:
        comment = cl.media_comment(media_id, text)
        comment_pk = comment.pk
        time.sleep(random.uniform(1, 3))
        cl.comment_pin(media_id, comment_pk)
        return True
    except (PleaseWaitFewMinutes, RateLimitError) as e:
        print(f"    [!!] Rate limited on comment: {e}")
        return False
    except Exception as e:
        print(f"    [!!] Comment/pin error: {e}")
        return False


def has_pinned_comment(cl, media_id):
    """Check if the post already has a pinned comment from us."""
    try:
        comments = cl.media_comments(media_id, amount=20)
        my_user_id = cl.user_id
        for c in comments:
            # Check if it's our comment and it's pinned
            is_ours = str(getattr(c, 'user', {}).pk if hasattr(getattr(c, 'user', None), 'pk') else '') == str(my_user_id)
            is_pinned = getattr(c, 'is_pinned', False)
            if is_ours and is_pinned:
                return True
    except Exception:
        pass
    return False


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cleanup low-performing Reels")
    parser.add_argument(
        "--go", action="store_true",
        help="Actually perform deletions and comments (default: dry run)"
    )
    parser.add_argument(
        "--min-views", type=int, default=DEFAULT_MIN_VIEWS,
        help=f"Delete reels below this view count (default: {DEFAULT_MIN_VIEWS})"
    )
    parser.add_argument(
        "--min-age", type=int, default=DEFAULT_MIN_AGE_HOURS,
        help=f"Only check posts older than this many hours (default: {DEFAULT_MIN_AGE_HOURS})"
    )
    parser.add_argument(
        "--scan", type=int, default=DEFAULT_SCAN_COUNT,
        help=f"Number of recent posts to scan (default: {DEFAULT_SCAN_COUNT})"
    )
    parser.add_argument(
        "--delete-only", action="store_true",
        help="Only delete flops, don't add pinned comments"
    )
    parser.add_argument(
        "--comment-only", action="store_true",
        help="Only add pinned comments, don't delete anything"
    )
    parser.add_argument(
        "--before", type=str, default=None,
        help="Only delete posts BEFORE this date (YYYY-MM-DD). Posts on/after this date are kept."
    )
    parser.add_argument(
        "--username", "-u", default=None,
        help="Override IG username"
    )
    args = parser.parse_args()

    if args.username:
        config.USERNAME = args.username
        config.SESSION_FILE = os.path.join(config.SESSION_DIR, f"{args.username}_session.json")

    print(r"""
    ╔═══════════════════════════════════════════════╗
    ║     CLEANUP — Reel Performance Manager        ║
    ║     Delete flops · Pin comments on keepers    ║
    ╚═══════════════════════════════════════════════╝
    """)

    mode = "DRY RUN" if not args.go else "LIVE"
    print(f"  Account:     @{config.USERNAME}")
    print(f"  Mode:        {mode}")
    print(f"  Min views:   {args.min_views}")
    print(f"  Min age:     {args.min_age}h")
    print(f"  Scan count:  {args.scan}")
    print(f"  Delete:      {'OFF' if args.comment_only else 'ON'}")
    print(f"  Pin comment: {'OFF' if args.delete_only else 'ON'}")
    print()

    if not args.go:
        print("  *** DRY RUN — nothing will be changed. Use --go to execute. ***\n")

    # Login
    print("[*] Logging in...")
    cl = create_client(config.SESSION_FILE)

    # Fetch reels
    print(f"[*] Fetching your last {args.scan} posts...\n")
    reels = get_my_reels(cl, amount=args.scan)
    print(f"[*] Found {len(reels)} reels\n")

    if not reels:
        print("  No reels found.")
        return

    # Analyze
    to_delete = []
    keepers = []
    too_new = []

    for media in reels:
        stats = get_reel_stats(media)
        should_del, reason = should_delete(stats, args.min_views, args.min_age, args.before)

        if reason == "too_new":
            too_new.append(stats)
        elif should_del:
            to_delete.append(stats)
        else:
            keepers.append(stats)

    # Summary
    print(f"{'─' * 60}")
    print(f"  RESULTS")
    print(f"{'─' * 60}")
    print(f"  Too new (< {args.min_age}h):  {len(too_new)}")
    print(f"  Keepers (>= {args.min_views} views): {len(keepers)}")
    print(f"  Flops (< {args.min_views} views):    {len(to_delete)}")
    print()

    # Show flops
    if to_delete:
        print(f"  FLOPS (will delete):")
        for s in sorted(to_delete, key=lambda x: x["views"]):
            age = ""
            if s["taken_at"]:
                taken = s["taken_at"]
                if taken.tzinfo is None:
                    taken = taken.replace(tzinfo=timezone.utc)
                age_h = int((datetime.now(timezone.utc) - taken).total_seconds() / 3600)
                age = f"{age_h}h ago"
            cap = s["caption"][:35] + "..." if len(s["caption"]) > 35 else s["caption"]
            print(f"    {s['views']:>6} views | {s['likes']:>4} likes | {age:>7} | {cap}")
        print()

    # Show keepers
    if keepers and not args.delete_only:
        print(f"  KEEPERS (will pin comment if missing):")
        for s in sorted(keepers, key=lambda x: x["views"], reverse=True)[:15]:
            cap = s["caption"][:35] + "..." if len(s["caption"]) > 35 else s["caption"]
            print(f"    {s['views']:>8} views | {s['likes']:>5} likes | {cap}")
        if len(keepers) > 15:
            print(f"    ... and {len(keepers) - 15} more")
        print()

    if not args.go:
        print(f"  Run with --go to execute these actions.")
        return

    # ─── Execute ──────────────────────────────────────────────────
    deleted = 0
    commented = 0

    # Delete flops
    if to_delete and not args.comment_only:
        print(f"\n[*] Deleting {len(to_delete)} low-performing reels...")
        for i, stats in enumerate(to_delete, 1):
            print(f"  [{i}/{len(to_delete)}] Deleting (pk={stats['pk']}, {stats['views']} views)...", end="")
            success = delete_reel(cl, stats["id"])
            if success:
                deleted += 1
                print(" done")
            else:
                print(" FAILED")
            time.sleep(random.uniform(ACTION_DELAY_MIN, ACTION_DELAY_MAX))

    # Pin comments on keepers
    if keepers and not args.delete_only:
        print(f"\n[*] Pinning comments on {len(keepers)} keepers...")
        for i, stats in enumerate(keepers, 1):
            # Check if already has a pinned comment from us
            print(f"  [{i}/{len(keepers)}] Checking pk={stats['pk']} ({stats['views']} views)...", end="")

            already_pinned = has_pinned_comment(cl, stats["id"])
            if already_pinned:
                print(" already has pinned comment, skip")
            else:
                comment_text = random.choice(PIN_COMMENTS)
                success = pin_comment(cl, stats["id"], comment_text)
                if success:
                    commented += 1
                    print(f" pinned: \"{comment_text}\"")
                else:
                    print(" FAILED")

            time.sleep(random.uniform(ACTION_DELAY_MIN, ACTION_DELAY_MAX))

    # Done
    print(f"\n{'═' * 60}")
    print(f"  DONE!")
    print(f"  Deleted:          {deleted} flops")
    print(f"  Comments pinned:  {commented} keepers")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
