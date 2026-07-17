"""
Poster watchdog — topcats online.

Keeps bluestacks_poster.py alive unattended. Two failure modes it heals:

  1. the poster process dies (uncaught exception, adb blow-up)  -> relaunch
  2. BlueStacks freezes (adb `echo` answers but `input` hangs)   -> restart
     BlueStacks, then relaunch the poster

WHY THIS IS NOT wipe_watchdog.py: the deleter worked continuously, so "no
progress for 150s" reliably meant frozen. The poster is IDLE BY DESIGN —
50-70 min between batches, plus a 2-8am rest window — so that rule would
false-positive constantly and restart BlueStacks all night. Instead:

  * a stall is only suspected after STALL_MINS with no post, which is set
    well past the longest legitimate gap (max batch interval + batch length)
  * the rest window is skipped entirely — silence there is expected
  * BlueStacks is only probed once a stall is already suspected, so the
    probe can't collide with the poster mid-post (one thing drives the
    emulator at a time)

Safety: the poster is launched with --expect-handle, so a watchdog-relaunch
can never start posting into the wrong account.

Usage:
  python poster_watchdog.py                    # run (foreground)
  python poster_watchdog.py --handle topcats.online
"""

import argparse
import os
import re
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SERIAL = "127.0.0.1:5555"
INSTANCE = "Pie64"
HD_PLAYER = r"C:\Program Files\BlueStacks_nxt\HD-Player.exe"
POSTER_LOG = os.path.join(HERE, "topcats_poster.log")
WD_LOG = os.path.join(HERE, "poster_watchdog.log")

# Longest legitimate silence: max batch interval (70m) + a slow batch (~15m)
# + margin. Anything past this with the poster alive means something is stuck.
STALL_MINS = 100
CHECK_EVERY = 120          # seconds between health checks
BOOT_WAIT_TRIES = 72       # ~12 min max to boot

# Mirror config.py's rest window — no posts are expected in it.
REST_START, REST_END = 2, 8


def wlog(msg):
    line = f"[watchdog {time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(WD_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def adb(*args, timeout=15):
    try:
        return subprocess.run(["adb", "-s", SERIAL, *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return subprocess.CompletedProcess(args, -1, "", "")


def boot_completed():
    return (adb("shell", "getprop", "sys.boot_completed",
                timeout=10).stdout or "").strip() == "1"


def input_responsive():
    """A BlueStacks freeze = `adb shell echo` still answers but `input` hangs.
    Probe `input` directly (KEYCODE_WAKEUP is harmless). Two tries to avoid a
    one-off blip. Only called once a stall is already suspected."""
    for _ in range(2):
        r = adb("shell", "input", "keyevent", "KEYCODE_WAKEUP", timeout=8)
        if r.returncode == 0:
            return True
    return False


def poster_pids():
    r = subprocess.run(["powershell", "-NonInteractive", "-Command",
        "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        "Where-Object {$_.CommandLine -like '*bluestacks_poster*'}).ProcessId"],
        capture_output=True, text=True)
    return [p for p in (r.stdout or "").split() if p.strip()]


def kill_poster():
    for pid in poster_pids():
        subprocess.run(["taskkill", "/PID", pid, "/T", "/F"], capture_output=True)
    time.sleep(2)


def kill_bluestacks():
    subprocess.run(["taskkill", "/IM", "HD-Player.exe", "/F"], capture_output=True)
    time.sleep(6)


def start_bluestacks():
    try:
        subprocess.Popen([HD_PLAYER, "--instance", INSTANCE])
    except OSError as e:
        wlog(f"failed to launch HD-Player: {e}")
        return False
    for _ in range(BOOT_WAIT_TRIES):
        subprocess.run(["adb", "connect", SERIAL], capture_output=True)
        if boot_completed():
            time.sleep(12)  # let IG/home settle
            return True
        time.sleep(10)
    return False


def restart_bluestacks():
    wlog("FREEZE RECOVERY: restarting BlueStacks")
    kill_poster()
    kill_bluestacks()
    subprocess.run(["adb", "kill-server"], capture_output=True)
    time.sleep(3)
    subprocess.run(["adb", "start-server"], capture_output=True)
    ok = start_bluestacks()
    wlog(f"BlueStacks restart: booted={ok}")
    return ok


def launch_poster(handle):
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    f = open(POSTER_LOG, "a", encoding="utf-8")
    f.write(f"\n===== poster (watchdog-launched {time.strftime('%H:%M:%S')}) =====\n")
    f.flush()
    p = subprocess.Popen(
        [sys.executable, "-u", "bluestacks_poster.py", "--expect-handle", handle],
        stdout=f, stderr=subprocess.STDOUT, env=env, cwd=HERE)
    wlog(f"launched poster pid {p.pid}")
    return p


def last_post_dt():
    """When the poster last reported a real post, read from SUCCESS_LOG (the
    honest record — only written on an actual post). None if never."""
    path = os.path.join(HERE, "success.txt")
    if not os.path.exists(path):
        return None
    last = None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line.strip())
                if m:
                    last = m.group(1)
    except OSError:
        return None
    if not last:
        return None
    try:
        return datetime.strptime(last, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def silence_baseline(watchdog_start, last_relaunch):
    """The most recent moment from which silence actually means something.

    Silence is only evidence of a stall if the poster was SUPPOSED to be
    posting through it. Three things legitimately reset that clock:

      * the rest window ending — the 6h overnight gap is by design, and
        measuring from the last post makes the poster look 379 min stalled
        the instant it wakes at 08:00 (this false-fired on 2026-07-17 and
        would have killed the poster every 2 min, forever, since a freshly
        relaunched poster has not posted yet either)
      * the watchdog starting — it inherits whatever gap preceded it
      * a relaunch — the new poster needs time to produce its first post

    So take the latest of those and the last real post.
    """
    now = datetime.now()
    candidates = [watchdog_start, last_relaunch]
    rest_end_today = now.replace(hour=REST_END, minute=0, second=0, microsecond=0)
    if rest_end_today <= now:
        candidates.append(rest_end_today)
    lp = last_post_dt()
    if lp:
        candidates.append(lp)
    return max(candidates)


def in_rest_window():
    return REST_START <= datetime.now().hour < REST_END


def poster_blocked_out():
    """The poster hard-exits after 3 consecutive action-blocks. That is a
    deliberate stop, not a crash — relaunching would undo the protection."""
    try:
        with open(POSTER_LOG, "r", encoding="utf-8", errors="replace") as f:
            tail = f.read()[-4000:]
    except OSError:
        return False
    return "3 consecutive blocks" in tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", default="topcats.online",
                    help="account the poster is guarded to")
    args = ap.parse_args()

    watchdog_start = datetime.now()
    last_relaunch = watchdog_start

    wlog(f"watchdog up — guarding poster on '{args.handle}' "
         f"(stall threshold {STALL_MINS}m, rest {REST_START}-{REST_END})")

    if not poster_pids():
        launch_poster(args.handle)
        last_relaunch = datetime.now()

    while True:
        time.sleep(CHECK_EVERY)

        if poster_blocked_out():
            wlog("poster stopped itself after 3 action-blocks — standing down. "
                 "Not relaunching; Instagram is pushing back.")
            return

        alive = bool(poster_pids())

        if not alive:
            wlog("poster process is gone — relaunching")
            if not input_responsive():
                restart_bluestacks()
            launch_poster(args.handle)
            last_relaunch = datetime.now()
            continue

        if in_rest_window():
            continue  # silence is expected here

        age = (datetime.now()
               - silence_baseline(watchdog_start, last_relaunch)
               ).total_seconds() / 60.0
        if age < STALL_MINS:
            continue

        # Alive, outside rest, and genuinely silent since the last moment it
        # should have been posting.
        wlog(f"STALL suspected: nothing posted for {age:.0f}m since the poster "
             f"was last expected to be working (threshold {STALL_MINS}m)")
        if input_responsive():
            wlog("BlueStacks responds — poster is stuck without a freeze; "
                 "restarting the poster only")
            kill_poster()
            launch_poster(args.handle)
        else:
            wlog("BlueStacks not responding to input — frozen")
            if restart_bluestacks():
                launch_poster(args.handle)
        last_relaunch = datetime.now()


if __name__ == "__main__":
    main()
