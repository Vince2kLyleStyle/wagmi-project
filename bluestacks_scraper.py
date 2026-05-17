"""
BlueStacks Explore Scraper
===========================
Scrolls through the Instagram Reels/Explore feed inside BlueStacks,
copies each reel's link, sends it to the Telegram download bot via
Telethon, and saves the clean video locally.

Completely undetectable - looks like a real user browsing reels.

Flow per reel:
  1. View reel on Reels tab in BlueStacks
  2. Tap Share -> Copy link (goes to Windows clipboard via BlueStacks sync)
  3. Read URL from Windows clipboard (powershell Get-Clipboard)
  4. Send URL to Telegram bot via Telethon (already configured)
  5. Bot returns clean watermark-free video -> save to tiktok_videos/motion/
  6. Swipe up to next reel
  7. Repeat

Usage:
    python bluestacks_scraper.py                  # scrape 20 reels (default)
    python bluestacks_scraper.py --amount 50      # scrape 50 reels
    python bluestacks_scraper.py --skip-own       # skip reels from your own account
"""

import argparse
import os
import random
import subprocess
import sys
import time

# Fix Windows console encoding for emoji in telegram_sender output
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import config
import scraper_config as tg_cfg
from telegram_sender import send_and_download_sync

# ---- Paths ----
VIDEO_DIR      = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")
SEEN_LOG       = os.path.join(os.path.dirname(__file__), "ig_scraped.txt")
HOT_ACCOUNTS   = os.path.join(os.path.dirname(__file__), "hot_accounts.txt")

# ---- ADB ----
ADB_SERIAL = None


def adb(cmd: list, timeout: int = 30) -> str:
    """Run ADB command targeting BlueStacks."""
    try:
        prefix = ["adb"]
        if ADB_SERIAL:
            prefix = ["adb", "-s", ADB_SERIAL]
        env = os.environ.copy()
        env["MSYS_NO_PATHCONV"] = "1"
        result = subprocess.run(
            prefix + cmd,
            capture_output=True, text=True, timeout=timeout, env=env,
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"[!!] ADB error: {e}")
        return ""


def connect_bluestacks() -> bool:
    """Find and connect to BlueStacks. Sets ADB_SERIAL."""
    global ADB_SERIAL
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10)
    lines = [l for l in result.stdout.splitlines() if "\tdevice" in l]

    for line in lines:
        serial = line.split("\t")[0]
        if serial.startswith("127.0.0.1"):
            ADB_SERIAL = serial
            print(f"[+] Using device: {ADB_SERIAL}")
            return True
    for line in lines:
        serial = line.split("\t")[0]
        if serial.startswith("emulator"):
            ADB_SERIAL = serial
            print(f"[+] Using device: {ADB_SERIAL}")
            return True

    print("[*] Trying to connect to BlueStacks...")
    for port in [5555, 5556, 5565, 5575]:
        out = subprocess.run(
            ["adb", "connect", f"127.0.0.1:{port}"],
            capture_output=True, text=True, timeout=10
        ).stdout
        if "connected" in out.lower():
            ADB_SERIAL = f"127.0.0.1:{port}"
            print(f"[+] Connected on port {port}")
            time.sleep(2)
            return True

    print("[!!] Could not connect to BlueStacks.")
    return False


def restart_bluestacks() -> bool:
    """Kill and restart BlueStacks, wait for ADB to come online."""
    BS_PATH = "C:/Program Files/BlueStacks_nxt/HD-Player.exe"
    if not os.path.exists(BS_PATH):
        print("[!!] BlueStacks not found at expected path")
        return False

    print("[*] Restarting BlueStacks...")
    subprocess.run(["taskkill", "/F", "/IM", "HD-Player.exe"],
                   capture_output=True, timeout=10)
    subprocess.run(["taskkill", "/F", "/IM", "BstkSVC.exe"],
                   capture_output=True, timeout=10)
    time.sleep(5)

    subprocess.Popen([BS_PATH])
    print("[*] Waiting for BlueStacks to boot...")

    for i in range(24):  # up to 2 minutes
        time.sleep(10)
        try:
            env = os.environ.copy()
            env["MSYS_NO_PATHCONV"] = "1"
            result = subprocess.run(
                ["adb", "connect", "127.0.0.1:5555"],
                capture_output=True, text=True, timeout=10, env=env
            )
            if "connected" in result.stdout.lower():
                time.sleep(5)
                # Set portrait mode
                subprocess.run(
                    ["adb", "-s", "127.0.0.1:5555", "shell", "wm", "size", "1080x1920"],
                    capture_output=True, text=True, timeout=10, env=env
                )
                time.sleep(3)
                print(f"[+] BlueStacks back online after ~{(i+1)*10}s")
                return connect_bluestacks()
        except Exception:
            pass
        print(f"  Attempt {i+1} -- not ready yet...")

    print("[!!] BlueStacks failed to restart")
    return False


def is_bluestacks_alive() -> bool:
    """Quick check if BlueStacks ADB is responding."""
    try:
        env = os.environ.copy()
        env["MSYS_NO_PATHCONV"] = "1"
        prefix = ["adb"]
        if ADB_SERIAL:
            prefix = ["adb", "-s", ADB_SERIAL]
        result = subprocess.run(
            prefix + ["shell", "echo", "alive"],
            capture_output=True, text=True, timeout=5, env=env
        )
        return "alive" in result.stdout
    except Exception:
        return False


def get_clipboard() -> str:
    """Read Windows clipboard (shared with BlueStacks)."""
    try:
        result = subprocess.run(
            ["powershell", "-command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def load_seen_urls() -> set:
    """Load URLs we've already scraped."""
    if not os.path.exists(SEEN_LOG):
        return set()
    with open(SEEN_LOG, "r") as f:
        return {line.strip() for line in f if line.strip()}


def mark_seen(url: str):
    """Mark a URL as already scraped."""
    with open(SEEN_LOG, "a") as f:
        f.write(url + "\n")


def log_hot_account(username: str):
    """Log accounts we scraped from — review later to add as competitors."""
    if not username or username == config.USERNAME:
        return
    from datetime import datetime
    with open(HOT_ACCOUNTS, "a", encoding="utf-8") as f:
        f.write(f"@{username} | explore reel | {datetime.now().strftime('%Y-%m-%d')}\n")


def human_delay(base: float, jitter: float = 0.5):
    """Sleep with random jitter to look human."""
    time.sleep(base + random.uniform(-jitter, jitter))


def is_on_reels_tab() -> bool:
    """Check if we're currently on the Reels tab."""
    pos = find_element(text="Reels")
    # The Reels header text appears at the top when on the Reels tab
    if pos and pos[1] < 200:
        return True
    return False


def open_reels_tab():
    """Launch Instagram and navigate to Reels tab."""
    print("[*] Opening Instagram Reels tab...")
    adb(["shell", "am", "start",
         "-n", "com.instagram.android/com.instagram.android.activity.MainTabActivity"])
    time.sleep(5)
    # Tap Reels tab (bottom nav, second icon)
    adb(["shell", "input", "tap", "324", "1876"])
    time.sleep(3)
    if is_on_reels_tab():
        print("[+] On Reels tab")
    else:
        print("[~] May not be on Reels tab -- retrying")
        adb(["shell", "input", "tap", "324", "1876"])
        time.sleep(2)


def find_element(text=None, content_desc=None):
    """Find UI element by text or content_desc. Returns (x, y) or None."""
    import re
    import xml.etree.ElementTree as ET

    adb(["shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"])
    time.sleep(0.5)
    adb(["pull", "/sdcard/ui_dump.xml", "ui_dump.xml"])
    adb(["shell", "rm", "/sdcard/ui_dump.xml"])

    try:
        tree = ET.parse("ui_dump.xml")
        for node in tree.getroot().iter("node"):
            match = False
            if text and node.get("text", "").lower() == text.lower():
                match = True
            if content_desc and content_desc.lower() in node.get("content-desc", "").lower():
                match = True
            if match:
                bounds = node.get("bounds", "")
                nums = re.findall(r"\d+", bounds)
                if len(nums) == 4:
                    cx = (int(nums[0]) + int(nums[2])) // 2
                    cy = (int(nums[1]) + int(nums[3])) // 2
                    return cx, cy
    except Exception:
        pass
    finally:
        try:
            os.remove("ui_dump.xml")
        except OSError:
            pass
    return None


def copy_reel_link() -> str:
    """
    Tap Share -> Copy link on the current reel.
    Returns the Instagram reel URL from Windows clipboard, or empty string.

    Uses uiautomator to find buttons precisely. The Reels tab share button
    has content_desc="Share" and sits on the right side of the screen.
    """
    import re as _re
    import xml.etree.ElementTree as _ET

    # Clear Windows clipboard first
    subprocess.run(
        ["powershell", "-command", "Set-Clipboard -Value ''"],
        capture_output=True, timeout=5,
    )

    # Find the Share button specifically on the right side (Reels action bar)
    # There may be multiple "Share" elements — we want the one on the right side
    adb(["shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"])
    time.sleep(0.5)
    adb(["pull", "/sdcard/ui_dump.xml", "ui_dump.xml"])
    adb(["shell", "rm", "/sdcard/ui_dump.xml"])

    share_pos = None
    try:
        tree = _ET.parse("ui_dump.xml")
        for node in tree.getroot().iter("node"):
            cdesc = node.get("content-desc", "")
            # Share button in Reels is content_desc="Share" on the right side
            if cdesc == "Share":
                bounds = node.get("bounds", "")
                nums = _re.findall(r"\d+", bounds)
                if len(nums) == 4:
                    cx = (int(nums[0]) + int(nums[2])) // 2
                    cy = (int(nums[1]) + int(nums[3])) // 2
                    # Only accept if it's on the right side (x > 900) — the action bar
                    if cx > 900:
                        share_pos = (cx, cy)
                        break
    except Exception:
        pass
    finally:
        try:
            os.remove("ui_dump.xml")
        except OSError:
            pass

    if not share_pos:
        return ""

    # Tap Share
    adb(["shell", "input", "tap", str(share_pos[0]), str(share_pos[1])])
    human_delay(2.5)

    # Find and tap "Copy link" in the share sheet
    copy_pos = find_element(text="Copy link")
    if not copy_pos:
        copy_pos = find_element(content_desc="Copy link")
    if not copy_pos:
        # Dismiss share sheet and bail
        adb(["shell", "input", "keyevent", "4"])
        human_delay(0.5)
        return ""

    adb(["shell", "input", "tap", str(copy_pos[0]), str(copy_pos[1])])
    human_delay(2.0)

    # Read URL from Windows clipboard (BlueStacks shares clipboard with Windows)
    url = get_clipboard()

    # Dismiss any remaining overlay
    adb(["shell", "input", "keyevent", "4"])
    human_delay(0.5)

    if url and "instagram.com" in url:
        return url
    return ""


def swipe_to_next_reel():
    """Swipe up to go to the next reel. Re-launches Instagram if we drifted."""
    # Check we're still on Reels before swiping
    if not is_on_reels_tab():
        print("  [!] Not on Reels tab -- relaunching Instagram")
        open_reels_tab()

    adb(["shell", "input", "swipe", "540", "1400", "540", "400", "300"])
    human_delay(2.5, 1.0)


def get_reel_info() -> dict:
    """Get info about the current reel from uiautomator."""
    import re
    import xml.etree.ElementTree as ET

    adb(["shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"])
    time.sleep(0.5)
    adb(["pull", "/sdcard/ui_dump.xml", "ui_dump.xml"])
    adb(["shell", "rm", "/sdcard/ui_dump.xml"])

    info = {"username": "", "description": "", "is_ad": False}
    try:
        tree = ET.parse("ui_dump.xml")
        for node in tree.getroot().iter("node"):
            cdesc = node.get("content-desc", "")
            text = node.get("text", "")
            rid = node.get("resource-id", "")

            # Username
            if "row_feed_photo_profile_name" in rid or \
               (cdesc and "reel by" in cdesc.lower()):
                if "reel by" in cdesc.lower():
                    # "Reel by username. Double tap..."
                    parts = cdesc.split(".")
                    name = parts[0].replace("Reel by ", "").strip()
                    info["username"] = name
                elif text:
                    info["username"] = text

            # Detect ads: only "Sponsored" text (NOT Follow buttons —
            # those appear on all non-followed accounts in Reels)
            if text == "Sponsored" or text == "Ad" or \
               "sponsored" in cdesc.lower():
                info["is_ad"] = True

            # Description from "See more"
            if cdesc and "see more" in cdesc.lower():
                info["has_caption"] = True
    except Exception:
        pass
    finally:
        try:
            os.remove("ui_dump.xml")
        except OSError:
            pass

    return info


# ---- Competitor accounts (motion/sigma niche) ----
COMPETITOR_ACCOUNTS = [
    "twinkpotato",
    "womenconsumer",
    "uncrustamemes",
    "unbustable.nuttt",
    "pebbleism",
]
REELS_PER_ACCOUNT = 5  # how many reels to grab from each account


def navigate_to_profile(username: str) -> bool:
    """Navigate to a user's profile via the search tab."""
    # Tap Search tab (bottom nav)
    adb(["shell", "input", "tap", "574", "1860"])
    human_delay(2.0)

    # Tap the search bar at the top
    search_pos = find_element(text="Search")
    if not search_pos:
        search_pos = find_element(content_desc="Search")
    if search_pos:
        adb(["shell", "input", "tap", str(search_pos[0]), str(search_pos[1])])
    else:
        adb(["shell", "input", "tap", "540", "140"])
    human_delay(1.5)

    # Clear any existing text and type username
    adb(["shell", "input", "keyevent", "28"])  # clear field (KEYCODE_CLEAR)
    human_delay(0.3)
    # Select all + delete
    adb(["shell", "input", "keyevent", "67"])  # backspace a bunch
    for _ in range(20):
        adb(["shell", "input", "keyevent", "67"])
    human_delay(0.3)
    adb(["shell", "input", "text", username])
    human_delay(3.0)  # wait for search results

    # Tap first result (should be the account)
    # Search results start around y=280 for the first result
    adb(["shell", "input", "tap", "540", "300"])
    human_delay(3.0)

    # Verify we're on the right profile
    profile_name = find_element(text=username)
    if profile_name:
        print(f"  [nav] On @{username}'s profile")
        return True

    # Might be slightly different — accept if we see a profile with posts
    posts_el = find_element(text="posts")
    if posts_el:
        print(f"  [nav] On a profile (may be @{username})")
        return True

    print(f"  [!!] Could not navigate to @{username}")
    return False


def open_profile_reels_tab():
    """Tap the Reels tab on a profile page (the video icon)."""
    # On a profile, the Reels tab is the second icon in the grid tabs
    # Grid / Reels / Tagged — Reels icon is roughly at x=320, y varies
    reels_pos = find_element(content_desc="Reels")
    if reels_pos:
        adb(["shell", "input", "tap", str(reels_pos[0]), str(reels_pos[1])])
        human_delay(2.0)
        return True
    # Fallback: tap the second tab icon area
    adb(["shell", "input", "tap", "320", "700"])
    human_delay(2.0)
    return True


def scrape_competitor_reels(username: str, target: int, seen_urls: set) -> int:
    """Scrape reels from a specific competitor account. Returns count downloaded."""
    print(f"\n{'='*54}")
    print(f"  Scraping @{username} ({target} reels)")
    print(f"{'='*54}")

    if not navigate_to_profile(username):
        return 0

    open_profile_reels_tab()
    human_delay(1.0)

    # Tap the first reel thumbnail to enter fullscreen reels view
    # First reel is at approximately (180, 830) on a profile grid
    adb(["shell", "input", "tap", "180", "830"])
    human_delay(3.0)

    downloaded = 0
    fails = 0
    for i in range(target + 10):  # extra attempts for skips
        if downloaded >= target:
            break
        if fails > 5:
            print(f"  [!!] Too many fails on @{username} — moving on")
            break

        # Copy link from current reel
        url = copy_reel_link()
        if not url:
            print(f"  [{downloaded+1}/{target}] Could not copy link — swiping")
            fails += 1
            swipe_to_next_reel()
            continue

        base_url = url.split("?")[0]
        if base_url in seen_urls:
            print(f"  [{downloaded+1}/{target}] Already scraped — swiping")
            swipe_to_next_reel()
            continue

        print(f"  [{downloaded+1}/{target}] {base_url}")
        print(f"  [tg] Sending to Telegram bot...")

        try:
            sent, dl, failed = send_and_download_sync(
                [url],
                bot_username=tg_cfg.TELEGRAM_BOT_USERNAME,
                download_dir=VIDEO_DIR,
            )
            if dl > 0:
                mark_seen(base_url)
                seen_urls.add(base_url)
                log_hot_account(username)
                downloaded += 1
                print(f"  [++] Downloaded ({downloaded}/{target})")
                fails = 0
            else:
                print(f"  [!!] Telegram download failed")
                fails += 1
        except Exception as e:
            print(f"  [!!] Telegram error: {e}")
            fails += 1

        swipe_to_next_reel()
        human_delay(random.uniform(2, 4))

    # Go back to home
    adb(["shell", "input", "keyevent", "4"])  # back
    human_delay(1.0)
    adb(["shell", "input", "keyevent", "4"])  # back again
    human_delay(1.0)

    print(f"  [done] @{username}: {downloaded} reels downloaded")
    return downloaded


def main():
    parser = argparse.ArgumentParser(description="BlueStacks Explore Scraper")
    parser.add_argument("--amount", type=int, default=20, help="Number of reels to scrape")
    parser.add_argument("--skip-own", action="store_true", help="Skip reels from your own account")
    parser.add_argument("--competitors", action="store_true",
                        help="Scrape from competitor accounts instead of explore feed")
    parser.add_argument("--accounts", nargs="*", default=None,
                        help="Specific accounts to scrape (overrides default list)")
    args = parser.parse_args()

    print()
    print("=" * 54)
    print("  BlueStacks Explore Scraper")
    print("  Browse Reels -> Copy link -> Telegram -> Save")
    print("=" * 54)
    print()

    os.makedirs(VIDEO_DIR, exist_ok=True)

    if not connect_bluestacks():
        sys.exit(1)

    own_username = config.USERNAME
    seen_urls = load_seen_urls()
    downloaded = 0
    skipped = 0
    consecutive_fails = 0
    target = args.amount

    print(f"[*] Target: {target} reels")
    print(f"[*] Save to: {VIDEO_DIR}")
    print(f"[*] Already scraped: {len(seen_urls)} URLs")
    print()

    # ── Competitor mode: scrape from specific accounts ──────────────
    if args.competitors or args.accounts:
        accounts = args.accounts if args.accounts else COMPETITOR_ACCOUNTS
        per_account = max(1, target // len(accounts))
        print(f"[*] Competitor mode: {len(accounts)} accounts, ~{per_account} each")
        print(f"[*] Accounts: {', '.join('@' + a for a in accounts)}")
        print()

        # Launch Instagram
        adb(["shell", "am", "start",
             "-n", "com.instagram.android/com.instagram.android.activity.MainTabActivity"])
        time.sleep(8)

        total = 0
        for acct in accounts:
            if total >= target:
                break
            remaining = min(per_account, target - total)
            got = scrape_competitor_reels(acct, remaining, seen_urls)
            total += got

        print()
        print("=" * 54)
        print(f"  Done: {total} reels downloaded from {len(accounts)} accounts")
        print("=" * 54)
        return

    # ── Explore mode: scroll Reels tab (default) ──────────────────
    open_reels_tab()

    while downloaded < target:
        # Get info about current reel
        info = get_reel_info()
        username = info.get("username", "unknown")
        is_ad = info.get("is_ad", False)
        print(f"\n[{downloaded+1}/{target}] Reel by @{username}{'  [AD]' if is_ad else ''}")

        # Skip ads
        if is_ad:
            print(f"  [skip] Sponsored/ad -- swiping")
            swipe_to_next_reel()
            continue

        # Skip own account
        if args.skip_own and username.lower() == own_username.lower():
            print(f"  [skip] Own account -- swiping")
            swipe_to_next_reel()
            continue

        # Check BlueStacks is alive before trying to copy
        if not is_bluestacks_alive():
            print("[!!] BlueStacks crashed -- restarting...")
            if restart_bluestacks():
                open_reels_tab()
                continue
            else:
                print("[!!] Could not restart BlueStacks -- stopping")
                break

        # Copy link
        url = copy_reel_link()
        if not url:
            print(f"  [!!] Could not get URL -- swiping")
            consecutive_fails += 1
            if consecutive_fails > 5:
                # Probably lost the Reels tab — full relaunch
                print("  [!] Too many consecutive fails -- relaunching Instagram")
                adb(["shell", "am", "force-stop", "com.instagram.android"])
                time.sleep(2)
                open_reels_tab()
                consecutive_fails = 0
            else:
                swipe_to_next_reel()
            skipped += 1
            if skipped > 50:
                print("[!!] Too many total failures -- stopping")
                break
            continue
        consecutive_fails = 0

        # Check if already scraped
        # Normalize URL (strip query params for dedup)
        base_url = url.split("?")[0]
        if base_url in seen_urls:
            print(f"  [skip] Already scraped -- swiping")
            swipe_to_next_reel()
            continue

        print(f"  [link] {base_url}")

        # Send to Telegram bot for download
        print(f"  [tg] Sending to Telegram bot...")
        try:
            sent, dl, failed = send_and_download_sync(
                [url],
                bot_username=tg_cfg.TELEGRAM_BOT_USERNAME,
                download_dir=VIDEO_DIR,
            )
            if dl > 0:
                mark_seen(base_url)
                seen_urls.add(base_url)
                log_hot_account(username)
                downloaded += 1
                print(f"  [++] Downloaded ({downloaded}/{target})")
            else:
                print(f"  [!!] Telegram download failed")
                skipped += 1
        except Exception as e:
            print(f"  [!!] Telegram error: {e}")
            skipped += 1

        # Swipe to next reel
        swipe_to_next_reel()

        # Human-like browsing delay
        human_delay(random.uniform(2, 5))

    print()
    print("=" * 54)
    print(f"  Done: {downloaded} reels downloaded, {skipped} skipped")
    print("=" * 54)


if __name__ == "__main__":
    main()
