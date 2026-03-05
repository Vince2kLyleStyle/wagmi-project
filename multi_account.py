"""
╔═══════════════════════════════════════════════════════════════╗
║       FADER v2 — Multi-Account Rotation Runner               ║
║   Cycles through multiple IG accounts for higher volume      ║
╚═══════════════════════════════════════════════════════════════╝

Usage:
    python multi_account.py

Reads accounts from accounts.json (create it first — see example below).

accounts.json format:
[
    {
        "username": "account1",
        "password": "pass1",
        "video_dir": "tiktok_videos/account1",
        "daily_cap": 10
    },
    {
        "username": "account2",
        "password": "pass2",
        "video_dir": "tiktok_videos/account2",
        "daily_cap": 12
    }
]

The runner will:
  1. Pick the next account in rotation
  2. Run a full daily session (warm-up → upload → daily cap → sleep)
  3. Move to the next account
  4. Repeat forever

Press Ctrl+C to stop gracefully.
"""

import json
import os
import random
import sys
import time
from datetime import datetime, timedelta

import config
import human_sim
from fader_reels import (
    create_client,
    relogin_client,
    upload_reel,
    log_success,
    countdown_timer,
    gaussian_delay,
    get_video_queue,
)

ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), "accounts.json")


def load_accounts() -> list[dict]:
    """Load account list from accounts.json."""
    if not os.path.exists(ACCOUNTS_FILE):
        print(f"[!!] {ACCOUNTS_FILE} not found!")
        print(f"[!!] Create it with your account credentials. See docstring for format.")
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
    video_dir = acct.get("video_dir", config.VIDEO_DIR)
    daily_cap = acct.get("daily_cap", random.randint(config.DAILY_MIN, config.DAILY_MAX))

    # Override config for this account
    config.USERNAME = username
    config.PASSWORD = password
    config.VIDEO_DIR = video_dir

    session_file = os.path.join(config.SESSION_DIR, f"{username}_session.json")

    print(f"\n{'='*60}")
    print(f"  ACCOUNT: @{username}")
    print(f"  Video dir: {video_dir}")
    print(f"  Daily cap: {daily_cap}")
    print(f"{'='*60}\n")

    # Login
    print(f"[*] Logging in as @{username}...")
    try:
        cl = create_client(session_file)
    except Exception as e:
        print(f"[!!] Login failed for @{username}: {e}")
        return 0

    # Warm-up
    human_sim.warmup_session(cl)

    # Load videos
    import glob
    pattern = os.path.join(video_dir, "*.mp4")
    videos = sorted(glob.glob(pattern))
    if not videos:
        print(f"[!!] No videos found in {video_dir}, skipping account.")
        return 0

    total_videos = len(videos)
    print(f"[*] Found {total_videos} videos for @{username}")

    uploads = 0
    video_idx = 0
    batch_num = 0
    total_batches = (min(daily_cap, total_videos) + config.BATCH_SIZE - 1) // config.BATCH_SIZE

    while video_idx < total_videos and uploads < daily_cap:
        # Build batch
        batch_num += 1
        batch_end = min(video_idx + config.BATCH_SIZE, total_videos)
        batch_videos = videos[video_idx:batch_end]

        print(f"\n{'─'*60}")
        print(f"  @{username} — Batch {batch_num}/{total_batches}  |  "
              f"Uploaded: {uploads}/{daily_cap}")
        print(f"{'─'*60}")

        for i, vpath in enumerate(batch_videos):
            if uploads >= daily_cap:
                break

            filename = os.path.basename(vpath)
            human_sim.pre_upload_pause()

            print(f"\n  Uploading [{video_idx + 1}]: {filename}")
            result = upload_reel(cl, vpath)

            # Handle errors same as single-account mode
            if result == "THROTTLED":
                sleep_sec = random.randint(config.THROTTLE_SLEEP_MIN, config.THROTTLE_SLEEP_MAX)
                countdown_timer(sleep_sec, "Throttle cooldown")
                result = upload_reel(cl, vpath)

            if result == "CHALLENGE":
                print(f"  [!!] Challenge on @{username} — skipping rest of session.")
                return uploads

            if result == "LOGIN_EXPIRED":
                cl = relogin_client(cl, session_file)
                result = upload_reel(cl, vpath)

            if result and result not in ("THROTTLED", "CHALLENGE", "LOGIN_EXPIRED"):
                print(f"  [++] Successfully uploaded: {filename}")
                log_success(filename, result)

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

            if i < len(batch_videos) - 1 and uploads < daily_cap:
                delay = random.randint(config.INTRA_BATCH_MIN, config.INTRA_BATCH_MAX)
                countdown_timer(delay, "Intra-batch delay")

        print(f"\n  Batch {batch_num} complete!")

        if video_idx < total_videos and uploads < daily_cap:
            delay = gaussian_delay(
                config.INTER_BATCH_CENTER,
                config.INTER_BATCH_SPREAD,
                config.INTER_BATCH_FLOOR,
                config.INTER_BATCH_CEIL,
            )
            mins, secs = divmod(delay, 60)
            print(f"  Batch delay: {mins}m {secs}s")
            countdown_timer(delay, "Batch delay")

    print(f"\n[*] @{username} session done — {uploads} uploads today.\n")
    return uploads


def main() -> None:
    print(r"""
    ╔═══════════════════════════════════════════════════════════╗
    ║    F A D E R  v2  —  Multi-Account Rotation Runner       ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    accounts = load_accounts()
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

                # Delay between accounts (look less suspicious)
                if idx < len(accounts) - 1:
                    gap = random.randint(600, 1800)  # 10-30 min
                    print(f"\n[*] Switching accounts in {gap // 60}m...")
                    countdown_timer(gap, "Account switch")

            print(f"\n[*] Cycle {cycle} complete — {total_uploads} total uploads")

            # Sleep until next day
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
