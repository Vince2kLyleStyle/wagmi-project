#!/usr/bin/env python3
"""
Overnight nest-egg builder for "topcats online".

Sources cats toward the 50/35/15 content mix by running tiktok_scraper.py
sequentially per tier (ONE scraper at a time => no Telegram session clash),
biased so hellokitty gets the most volume. Self-logging, time-boxed, and
resilient: a hung/failed pass is timed out and the build moves on.

Run:  PYTHONUTF8=1 python overnight_build.py   (launch in background)
"""
import glob
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.join(BASE, "tiktok_videos")

# Target library size per tier (~50/35/15 so tiers last proportionally at posting)
TARGETS = {"hellokitty": 220, "popgak": 150, "catsother": 70}
PERMAX = {"hellokitty": 15, "popgak": 15, "catsother": 10}
ORDER = ["hellokitty", "popgak", "catsother"]

TIME_BUDGET_S = 6 * 3600        # stop after ~6h regardless
PASS_TIMEOUT_S = 45 * 60        # per niche-pass hard timeout
MAX_ROUNDS = 10

ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
t0 = time.time()


def count(t):
    return len(glob.glob(os.path.join(VID, t, "*.mp4")))


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def scrape(niche, mx):
    # fresh progress each round so re-runs scrape deeper instead of skipping
    p = os.path.join(BASE, f"{niche}_progress.txt")
    if os.path.exists(p):
        try:
            os.remove(p)
        except OSError:
            pass
    try:
        subprocess.run(
            [sys.executable, "tiktok_scraper.py", "--niche", niche,
             "--max", str(mx), "--scrolls", "8"],
            cwd=BASE, env=ENV, timeout=PASS_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        log(f"  {niche} pass hit {PASS_TIMEOUT_S // 60}min timeout — moving on")
    except Exception as e:  # noqa: BLE001
        log(f"  {niche} pass error: {e}")


def main():
    log("=== overnight build start ===")
    log("targets: " + ", ".join(f"{t}={TARGETS[t]}" for t in ORDER))
    for rnd in range(1, MAX_ROUNDS + 1):
        if time.time() - t0 > TIME_BUDGET_S:
            log("time budget reached — stopping")
            break
        cur = {t: count(t) for t in ORDER}
        log(f"round {rnd} | " + ", ".join(f"{t} {cur[t]}/{TARGETS[t]}" for t in ORDER))
        if all(cur[t] >= TARGETS[t] for t in ORDER):
            log("ALL TARGETS MET")
            break
        for t in ORDER:
            if time.time() - t0 > TIME_BUDGET_S:
                break
            if count(t) >= TARGETS[t]:
                log(f"  {t} target met ({count(t)}) — skip")
                continue
            log(f"  scraping {t} (have {count(t)}, want {TARGETS[t]})")
            scrape(t, PERMAX[t])
            log(f"  {t} now {count(t)}")
    log("=== DONE === final: " + ", ".join(f"{t}={count(t)}" for t in ORDER))


if __name__ == "__main__":
    main()
