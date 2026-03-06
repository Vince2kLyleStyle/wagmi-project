"""
Fader v2 — Multi-Account Rotation Runner
Cycles through multiple IG accounts with safety-managed limits per account.

Usage:
    python multi_account.py

accounts.json format:
[
    {
        "niche": "trading",
        "username": "account1",
        "password": "pass1",
        "daily_cap": null,
        "warmup_intensity": "normal"
    },
    {
        "niche": "memes",
        "username": "account2",
        "password": "pass2"
    }
]

daily_cap: null or omit → uses safety module's progressive limit
warmup_intensity: "light", "normal", "full" (default: "normal")
"""

import json
import os
import random
import sys
import time
from datetime import datetime, timedelta

import config
import human_sim
import safety
from fader_reels import (
    create_client,
    relogin_client,
    upload_reel,
    log_success,
    countdown_timer,
    get_video_queue,
)

ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), "accounts.json")


def load_accounts() -> list[dict]:
    """Load account list from accounts.json."""
    if not os.path.exists(ACCOUNTS_FILE):
        print(f"[!!] {ACCOUNTS_FILE} not found!")
        print(f"[!!] Create it with your account credentials. See accounts.example.json.")
        sys.exit(1)

    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)

    if not accounts:
        print("[!!] accounts.json is empty!")
        sys.exit(1)

    print(f"[*] Loaded {len(accounts)} accounts from {ACCOUNTS_FILE}")
    return accounts


def run_account_session(acct: dict) -> int:
    """
    Run a single daily session for one account.
    Returns the number of successful uploads.
    """
    username = acct["username"]
    password = acct["password"]
    niche = acct.get("niche", "")
    video_dir = acct.get("video_dir", os.path.join(
        os.path.dirname(__file__), "tiktok_videos", niche
    ) if niche else config.VIDEO_DIR)
    warmup_intensity = acct.get("warmup_intensity", "normal")

    # Daily target
    explicit_cap = acct.get("daily_cap")
    if explicit_cap:
        daily_cap = explicit_cap
    else:
        daily_cap = random.randint(config.DAILY_MIN, config.DAILY_MAX)

    # Override config for this account
    config.USERNAME = username
    config.PASSWORD = password
    config.VIDEO_DIR = video_dir
    config.CURRENT_NICHE = niche

    session_file = os.path.join(config.SESSION_DIR, f"{username}_session.json")

    print(f"\n{'='*60}")
    print(f"  ACCOUNT: @{username}")
    print(f"  Niche:     {niche or 'generic'}")
    print(f"  Video dir: {video_dir}")
    print(f"  Daily cap: {daily_cap}")
    print(f"  Burst:     {config.BATCH_SIZE} reels every ~{config.INTER_BATCH_CENTER//60}min")
    print(f"{'='*60}\n")

    # Check for active IG error cooldown
    safety.print_account_status(username)
    can, reason = safety.can_upload(username)
    if not can:
        print(f"[!!] @{username}: {reason}")
        print(f"[!!] Skipping this account.\n")
        return 0

    # Login
    print(f"[*] Logging in as @{username}...")
    try:
        cl = create_client(session_file, username)
    except Exception as e:
        print(f"[!!] Login failed for @{username}: {e}")
        safety.record_failure(username, "login_failed")
        return 0

    # Warm-up
    human_sim.warmup_session(cl, intensity=warmup_intensity)

    # Load videos
    import glob as globmod
    pattern = os.path.join(video_dir, "*.mp4")
    videos = sorted(globmod.glob(pattern))
    if not videos:
        print(f"[!!] No videos found in {video_dir}, skipping account.")
        return 0

    total_videos = len(videos)
    print(f"[*] Found {total_videos} videos for @{username}")

    uploads = 0
    video_idx = 0
    batch_num = 0
    total_batches = (min(daily_cap, total_videos) + config.BATCH_SIZE - 1) // config.BATCH_SIZE

    import niche_config as nc

    while video_idx < total_videos and uploads < daily_cap:
        # Check for IG error cooldown
        can, reason = safety.can_upload(username)
        if not can:
            print(f"[*] @{username}: {reason} — ending session")
            break

        # Build burst
        batch_num += 1
        batch_end = min(video_idx + config.BATCH_SIZE, total_videos)
        batch_videos = videos[video_idx:batch_end]

        # Same caption for entire burst
        if niche and niche in nc.NICHE_PROFILES:
            burst_caption = nc.get_burst_caption(niche)
        else:
            from captions import generate_caption
            burst_caption = generate_caption()

        print(f"\n{'─'*60}")
        print(f"  @{username} — Burst {batch_num}/{total_batches}  |  "
              f"Uploaded: {uploads}/{daily_cap}")
        print(f"  Caption: {burst_caption[:60]}...")
        print(f"{'─'*60}")

        for i, vpath in enumerate(batch_videos):
            if uploads >= daily_cap:
                break

            filename = os.path.basename(vpath)
            human_sim.pre_upload_pause()

            print(f"\n  Uploading [{video_idx + 1}]: {filename}")
            result = upload_reel(cl, vpath, niche=niche, burst_caption=burst_caption)

            if result == "THROTTLED":
                safety.record_failure(username, "rate_limited")
                sleep_sec = random.randint(config.THROTTLE_SLEEP_MIN, config.THROTTLE_SLEEP_MAX)
                print(f"  [!!] Rate limited — sleeping {sleep_sec//60}min then retry")
                countdown_timer(sleep_sec, "Throttle cooldown")
                result = upload_reel(cl, vpath, niche=niche, burst_caption=burst_caption)

            if result == "CHALLENGE":
                safety.record_failure(username, "challenge")
                print(f"  [!!] Challenge on @{username} — ending session.")
                return uploads

            if result == "LOGIN_EXPIRED":
                cl = relogin_client(cl, session_file)
                result = upload_reel(cl, vpath, niche=niche, burst_caption=burst_caption)

            if result and result not in ("THROTTLED", "CHALLENGE", "LOGIN_EXPIRED"):
                print(f"  [++] Successfully uploaded: {filename}")
                log_success(filename, result, niche=niche)
                safety.record_upload(username)

                if config.DELETE_AFTER_UPLOAD:
                    try:
                        os.remove(vpath)
                    except OSError:
                        pass

                uploads += 1
                human_sim.post_upload_pause()
            else:
                print(f"  [!!] Failed: {filename}")

            video_idx += 1

            # Short delay within burst
            if i < len(batch_videos) - 1 and uploads < daily_cap:
                delay = random.randint(config.INTRA_BATCH_MIN, config.INTRA_BATCH_MAX)
                countdown_timer(delay, "Burst delay")

        print(f"\n  Burst {batch_num} complete!")

        # ~30 min gap between bursts
        if video_idx < total_videos and uploads < daily_cap:
            from fader_reels import gaussian_delay
            delay = gaussian_delay(
                config.INTER_BATCH_CENTER,
                config.INTER_BATCH_SPREAD,
                config.INTER_BATCH_FLOOR,
                config.INTER_BATCH_CEIL,
            )
            mins, secs = divmod(delay, 60)
            print(f"  Next burst in: {mins}m {secs}s")
            human_sim.between_session_activity(cl)
            countdown_timer(delay, "Burst gap")

    print(f"\n[*] @{username} session done — {uploads} uploads today.")
    safety.print_account_status(username)
    return uploads


def main() -> None:
    print(r"""
    ╔═══════════════════════════════════════════════════════════╗
    ║    F A D E R  v2  —  Multi-Account Rotation Runner       ║
    ║        Burst Mode · Multi-Niche Edition                   ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    accounts = load_accounts()

    # Show safety status for all accounts
    print("\n  Account Safety Overview:")
    print(f"  {'─'*50}")
    for acct in accounts:
        status = safety.get_account_status(acct["username"])
        can, reason = status["can_upload"]
        niche = acct.get("niche", "generic")
        flag = "READY" if can else "BLOCKED"
        print(f"  @{acct['username']:20s}  {niche:12s}  "
              f"Day {status['days_automated']:3d}  "
              f"{status['uploads_today']}/{status['daily_limit']} today  "
              f"[{flag}]")
    print(f"  {'─'*50}\n")

    cycle = 0

    try:
        while True:
            cycle += 1
            print(f"\n{'#'*60}")
            print(f"  ROTATION CYCLE {cycle}")
            print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'#'*60}")

            total_uploads = 0

            for idx, acct in enumerate(accounts):
                print(f"\n[*] Account {idx + 1}/{len(accounts)}")
                uploads = run_account_session(acct)
                total_uploads += uploads

                # Delay between accounts
                if idx < len(accounts) - 1:
                    gap = random.randint(600, 1800)  # 10-30 min
                    print(f"\n[*] Switching accounts in {gap // 60}m...")
                    countdown_timer(gap, "Account switch")

            print(f"\n[*] Cycle {cycle} complete — {total_uploads} total uploads")

            # Sleep until next day (randomized morning start)
            now = datetime.now()
            tomorrow = (now + timedelta(days=1)).replace(
                hour=random.randint(7, 11),
                minute=random.randint(0, 59),
                second=0,
            )
            sleep_sec = int((tomorrow - now).total_seconds())
            print(f"[*] All accounts done. Sleeping until {tomorrow.strftime('%H:%M:%S')}...")
            countdown_timer(sleep_sec, "Nightly sleep")

    except KeyboardInterrupt:
        print("\n\n[*] Stopped by user. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
