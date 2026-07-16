#!/usr/bin/env python3
"""
Wipe watchdog — runs delete_all_posts.py to completion (0 posts), and
AUTOMATICALLY RESTARTS BlueStacks whenever it freezes, so the wipe finishes
unattended. BlueStacks on this box freezes intermittently: adb `shell echo`
still answers but `input`/uiautomator hang for 30s each, so the deleter stalls
without progress. This watchdog detects that (no post-count drop + piling adb
timeouts, or a dead deleter) and does a full BlueStacks restart, then relaunches
the resumable deleter. It will NOT restart during a legit action-block backoff.

Run:  python wipe_watchdog.py
Stop: kill this process (it kills the deleter on exit paths it controls).
"""
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SERIAL = "127.0.0.1:5555"
INSTANCE = "Pie64"
HD_PLAYER = r"C:\Program Files\BlueStacks_nxt\HD-Player.exe"
LOG = os.path.join(HERE, "delete_progress.log")

STALL_SECS = 150          # no count drop this long + adb timeouts => frozen
CHECK_EVERY = 30
BOOT_WAIT_TRIES = 72      # ~12 min max to boot


def wlog(msg):
    line = f"[watchdog {time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
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
    return (adb("shell", "getprop", "sys.boot_completed", timeout=10).stdout or "").strip() == "1"


def input_responsive():
    """A BlueStacks freeze = `adb shell echo` still answers but `input` hangs
    for 30s. So probe `input` directly (KEYCODE_WAKEUP is harmless): if it
    times out, the emulator is frozen. Two tries to avoid a one-off blip."""
    for _ in range(2):
        r = adb("shell", "input", "keyevent", "KEYCODE_WAKEUP", timeout=8)
        if r.returncode == 0:
            return True
    return False


def deleter_pids():
    r = subprocess.run(["powershell", "-NonInteractive", "-Command",
        "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        "Where-Object {$_.CommandLine -like '*delete_all_posts*'}).ProcessId"],
        capture_output=True, text=True)
    return [p for p in (r.stdout or "").split() if p.strip()]


def kill_deleter():
    for pid in deleter_pids():
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
    kill_deleter()
    kill_bluestacks()
    subprocess.run(["adb", "kill-server"], capture_output=True)
    time.sleep(3)
    subprocess.run(["adb", "start-server"], capture_output=True)
    ok = start_bluestacks()
    wlog(f"BlueStacks restart: booted={ok}")
    return ok


def launch_deleter():
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    f = open(LOG, "a", encoding="utf-8")
    f.write(f"\n===== deleter (watchdog-launched {time.strftime('%H:%M:%S')}) =====\n")
    f.flush()
    p = subprocess.Popen([sys.executable, "delete_all_posts.py"],
                         stdout=f, stderr=subprocess.STDOUT, env=env, cwd=HERE)
    wlog(f"launched deleter pid {p.pid}")
    return p


def log_tail(n=120):
    try:
        with open(LOG, encoding="utf-8", errors="replace") as f:
            return f.readlines()[-n:]
    except OSError:
        return []


def parse_state(tail):
    """Return (posts_left, done, recent_adb_timeouts, in_backoff)."""
    posts_left, done = None, False
    for ln in tail:
        m = re.search(r"(\d+) posts left", ln)
        if m:
            posts_left = int(m.group(1))
        m2 = re.search(r"posts = (\d+)", ln)
        if m2 and posts_left is None:
            posts_left = int(m2.group(1))
        if "[done] 0 posts remaining" in ln:
            done = True
    recent = tail[-15:]
    timeouts = sum("adb timed out" in ln for ln in recent)
    in_backoff = any("[BLOCKED]" in ln or "Backing off" in ln for ln in recent)
    return posts_left, done, timeouts, in_backoff


def main():
    wlog("=== WIPE WATCHDOG START — drive deleter to 0, auto-restart on freeze ===")
    kill_deleter()
    # BlueStacks is currently frozen -> start clean.
    if not (boot_completed() and input_responsive()):
        restart_bluestacks()

    launch_deleter()
    last_left = None
    last_progress = time.time()

    while True:
        time.sleep(CHECK_EVERY)
        tail = log_tail()
        left, done, timeouts, in_backoff = parse_state(tail)

        if done or left == 0:
            wlog("=== WIPE COMPLETE — 0 posts remaining. Watchdog done. ===")
            kill_deleter()
            break

        # progress?
        if left is not None and (last_left is None or left < last_left):
            last_left = left
            last_progress = time.time()

        no_progress = (time.time() - last_progress)
        pids = deleter_pids()

        if not pids and not in_backoff:
            wlog(f"deleter not running (left={left}) — relaunching")
            if not (boot_completed() and input_responsive()):
                restart_bluestacks()
            launch_deleter()
            last_progress = time.time()
            continue

        # freeze = stalled a while + adb timeouts piling up (and not a backoff)
        if no_progress > STALL_SECS and not in_backoff and (timeouts >= 2 or not input_responsive()):
            wlog(f"FREEZE suspected (left={left}, no_progress={int(no_progress)}s, "
                 f"timeouts={timeouts})")
            restart_bluestacks()
            launch_deleter()
            last_progress = time.time()


if __name__ == "__main__":
    main()
