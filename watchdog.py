"""
Posting Watchdog — BlueStacks Only
===================================
Monitors bluestacks_poster.py, restarts if stalled or crashed.
Clears phantom success.txt entries when queue is empty.

Run:  python watchdog.py
"""

import glob
import os
import subprocess
import sys
import time
from datetime import datetime

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

VIDEO_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", os.getenv("NICHE", "juicy"))
MEMES_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "memes")
SUCCESS_LOG = os.path.join(os.path.dirname(__file__), "success.txt")
WATCHDOG_LOG = os.path.join(os.path.dirname(__file__), "watchdog_log.txt")
POSTER_LOG = os.path.join(os.path.dirname(__file__), "bluestacks_poster_output.log")

STALL_THRESHOLD_MINUTES = 45
HARD_STALL_MINUTES = 90  # If stalled this long, restart BlueStacks entirely
LOW_QUEUE_THRESHOLD = 10
REFILL_BATCH_SIZE = 15  # how many memes to copy in when running low
CHECK_INTERVAL = 600  # 10 minutes
BLUESTACKS_EXE = r"C:\Program Files\BlueStacks_nxt\HD-Player.exe"


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(WATCHDOG_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_poster_pids() -> list[int]:
    """Return PIDs of running bluestacks_poster.py (real python only, not stubs)."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-WmiObject Win32_Process -Filter \"name='python.exe'\" | "
             "Where-Object { $_.CommandLine -match 'bluestacks_poster' -and "
             "$_.CommandLine -notmatch 'WindowsApps' } | "
             "Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=15
        )
        return [int(p.strip()) for p in result.stdout.strip().split("\n") if p.strip().isdigit()]
    except Exception:
        return []


def kill_all_posters():
    """Kill every bluestacks_poster process."""
    subprocess.run(
        ["powershell", "-Command",
         "Get-WmiObject Win32_Process -Filter \"name='python.exe'\" | "
         "Where-Object { $_.CommandLine -match 'bluestacks_poster' } | "
         "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
        capture_output=True, timeout=15
    )
    time.sleep(2)


def kill_api_poster():
    """Kill any api_poster that may have been started by mistake."""
    subprocess.run(
        ["powershell", "-Command",
         "Get-WmiObject Win32_Process -Filter \"name='python.exe'\" | "
         "Where-Object { $_.CommandLine -match 'api_poster' } | "
         "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
        capture_output=True, timeout=15
    )


def start_poster():
    """Start a single bluestacks_poster.py instance."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    subprocess.Popen(
        ["python", "-u", "bluestacks_poster.py"],
        stdout=open(POSTER_LOG, "a", encoding="utf-8"),
        stderr=subprocess.STDOUT,
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    log("  Started bluestacks_poster.py")


def restart_bluestacks():
    """Full BlueStacks restart — nuclear option for when IG is completely stuck."""
    log("  NUCLEAR: Restarting BlueStacks entirely...")
    kill_all_posters()

    # Kill BlueStacks
    subprocess.run(
        ["powershell", "-Command",
         "Get-Process -Name 'HD-Player','BlueStacksAppplayerWeb','BlueStacksServices' "
         "-ErrorAction SilentlyContinue | Stop-Process -Force"],
        capture_output=True, timeout=15
    )
    time.sleep(15)

    # Relaunch (instance is Pie64 — check C:\ProgramData\BlueStacks_nxt\Engine\)
    subprocess.Popen(
        [BLUESTACKS_EXE, "--instance", "Pie64"],
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    log("  BlueStacks relaunching, waiting 120s for boot...")
    time.sleep(120)

    # Reconnect ADB
    subprocess.run(["adb", "kill-server"], capture_output=True, timeout=10)
    time.sleep(3)
    subprocess.run(["adb", "start-server"], capture_output=True, timeout=10)
    time.sleep(3)
    result = subprocess.run(
        ["adb", "connect", "127.0.0.1:5555"],
        capture_output=True, text=True, timeout=10
    )
    log(f"  ADB reconnect: {result.stdout.strip()}")
    time.sleep(5)

    # Verify device is online
    result = subprocess.run(
        ["adb", "devices"], capture_output=True, text=True, timeout=10
    )
    if "device" in result.stdout and "offline" not in result.stdout.split("5555")[1][:20] if "5555" in result.stdout else False:
        log("  BlueStacks is back online")
    else:
        log(f"  WARNING: BlueStacks may not be ready yet — devices: {result.stdout.strip()}")

    # Start poster
    start_poster()


def is_instagram_stuck() -> bool:
    """Check if Instagram is stuck on splash screen or not responding."""
    try:
        env = os.environ.copy()
        env["MSYS_NO_PATHCONV"] = "1"
        result = subprocess.run(
            ["adb", "-s", "127.0.0.1:5555", "shell",
             "dumpsys activity activities | grep -i 'instagram.*Resumed'"],
            capture_output=True, text=True, timeout=10, env=env
        )
        # If Instagram has a resumed activity, it's loaded
        return "instagram" not in result.stdout.lower()
    except Exception:
        return True


def get_last_post_time() -> datetime | None:
    if not os.path.exists(SUCCESS_LOG):
        return None
    try:
        with open(SUCCESS_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            return None
        ts_str = lines[-1].strip().split(" | ")[0].strip()
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def get_queue_size() -> int:
    videos = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
    posted = set()
    if os.path.exists(SUCCESS_LOG):
        with open(SUCCESS_LOG, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(" | ")
                if len(parts) >= 2:
                    posted.add(parts[1].strip())
    return len([v for v in videos if os.path.basename(v) not in posted])


def clear_phantom_entries() -> int:
    """Remove success.txt entries for files still on disk (race condition leftovers)."""
    videos = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
    if not videos:
        return 0
    on_disk = {os.path.basename(v) for v in videos}
    if not os.path.exists(SUCCESS_LOG):
        return 0

    with open(SUCCESS_LOG, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned = []
    removed = 0
    for line in lines:
        parts = line.strip().split(" | ")
        if len(parts) >= 2 and parts[1].strip() in on_disk:
            removed += 1
        else:
            cleaned.append(line)

    if removed > 0:
        with open(SUCCESS_LOG, "w", encoding="utf-8") as f:
            f.writelines(cleaned)
        log(f"  Cleared {removed} phantom entries — recovered videos for reposting")
    return removed


def refill_from_memes() -> int:
    """Copy unposted mp4s from tiktok_videos/memes/ into the motion queue.
    Used when the IG scraper is broken (login_required) and we need to
    keep posting without manual intervention. Returns the number copied."""
    if not os.path.isdir(MEMES_DIR):
        return 0
    posted = set()
    if os.path.exists(SUCCESS_LOG):
        with open(SUCCESS_LOG, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(" | ")
                if len(parts) >= 2:
                    posted.add(parts[1].strip())
    motion_existing = {os.path.basename(p) for p in glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))}
    candidates = sorted(glob.glob(os.path.join(MEMES_DIR, "*.mp4")))
    import shutil
    moved = 0
    for src in candidates:
        name = os.path.basename(src)
        if name in posted or name in motion_existing:
            continue
        try:
            shutil.copy2(src, os.path.join(VIDEO_DIR, name))
            moved += 1
        except Exception as e:
            log(f"  refill copy failed for {name}: {e}")
        if moved >= REFILL_BATCH_SIZE:
            break
    if moved:
        log(f"  refilled {moved} videos from memes/ into motion/")
    return moved


def check_and_fix():
    now = datetime.now()
    pids = get_poster_pids()
    last_post = get_last_post_time()
    queue_size = get_queue_size()
    count = len(pids)

    minutes_since = (now - last_post).total_seconds() / 60 if last_post else 999

    log(f"Check: procs={count}, queue={queue_size}, last_post={last_post} ({minutes_since:.0f}m ago)")

    # Always kill any rogue api_poster
    kill_api_poster()

    # Fix duplicates — kill all, restart one
    if count > 1:
        log(f"  ISSUE: {count} bluestacks_poster instances — killing all, restarting 1")
        kill_all_posters()
        start_poster()
        return

    # Fix dead poster
    if count == 0:
        log("  ISSUE: bluestacks_poster not running — starting")
        start_poster()
        return

    # Fix hard stall — BlueStacks/IG is probably frozen, nuclear restart
    if minutes_since > HARD_STALL_MINUTES and queue_size > 0:
        log(f"  CRITICAL: No post in {minutes_since:.0f}m — restarting BlueStacks")
        restart_bluestacks()
        return

    # Fix soft stall (process alive but not posting)
    if minutes_since > STALL_THRESHOLD_MINUTES and queue_size > 0:
        log(f"  ISSUE: No post in {minutes_since:.0f}m with {queue_size} in queue — restarting poster")
        kill_all_posters()
        time.sleep(3)
        clear_phantom_entries()
        start_poster()
        return

    # Queue empty — try to recover phantom entries
    if queue_size == 0:
        total_on_disk = len(glob.glob(os.path.join(VIDEO_DIR, "*.mp4")))
        if total_on_disk > 0:
            cleared = clear_phantom_entries()
            if cleared > 0:
                log(f"  Queue was empty but {total_on_disk} files on disk — recovered {cleared}")
        else:
            # NOTE: memes refill disabled — content was off-niche.
            # Use bluestacks_scraper.py to get on-brand content instead.
            log("  WARNING: Queue empty — run: python bluestacks_scraper.py --amount 20")

    # Queue getting low warning
    elif queue_size <= LOW_QUEUE_THRESHOLD:
        log(f"  WARNING: Queue low ({queue_size} videos) — run bluestacks_scraper.py")


def main():
    log("=" * 50)
    log("Watchdog started (BlueStacks-only mode)")
    log("=" * 50)

    # Grace period on startup: skip the first stall check because the
    # poster may have been down for hours/days. Without this, watchdog
    # immediately triggers NUCLEAR restart on the first check.
    first_run = True
    while True:
        try:
            if first_run:
                log("  (startup grace — skipping stall check, just verifying poster is running)")
                pids = get_poster_pids()
                queue_size = get_queue_size()
                log(f"  procs={len(pids)}, queue={queue_size}")
                if len(pids) == 0:
                    log("  poster not running — starting")
                    start_poster()
                first_run = False
            else:
                check_and_fix()
        except Exception as e:
            log(f"  ERROR: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
