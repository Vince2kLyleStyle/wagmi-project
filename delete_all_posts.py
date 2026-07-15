#!/usr/bin/env python3
"""
Paced Instagram post deleter (BlueStacks + ADB, uiautomator-driven).

Deletes posts one at a time from the CURRENTLY LOGGED-IN account's profile,
finding buttons by text / content-desc (not hardcoded coordinates) so it
survives layout shifts. Human-paced with jitter + action-block detection so
Instagram doesn't flag the account. Resumable: it always deletes the first
grid post, so re-running just continues.

Usage:
    python delete_all_posts.py --max 1        # test: delete a single post
    python delete_all_posts.py                # delete until empty (paced)
    python delete_all_posts.py --min-delay 25 --max-delay 50
"""
import argparse
import random
import re
import subprocess
import sys
import time

SERIAL = "127.0.0.1:5555"


def adb(*args, timeout=30):
    # encoding/errors are REQUIRED on Windows: without them text=True decodes
    # adb's stdout as cp1252 and the uiautomator XML (box-chars / emoji in
    # content-desc) throws UnicodeDecodeError in the subprocess reader thread,
    # which killed the deleter mid-run at 512 posts. utf-8 + replace is safe.
    try:
        return subprocess.run(["adb", "-s", SERIAL, *args],
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        # adb can hang >timeout when the emulator is CPU-starved (e.g. heavy
        # concurrent load) — this crashed the wipe at ~#87. Don't let one hung
        # call kill the run: return an empty result so callers treat it as a
        # failed read and recover/retry via the existing dump()/read_profile
        # retry loops.
        print(f"[warn] adb timed out ({timeout}s): {' '.join(args)[:50]}", flush=True)
        return subprocess.CompletedProcess(args, returncode=-1, stdout="", stderr="")


def tap(x, y):
    adb("shell", "input", "tap", str(x), str(y))


def back():
    adb("shell", "input", "keyevent", "KEYCODE_BACK")


def dump():
    """Return the current UI hierarchy XML, retrying on empty/partial dumps
    (uiautomator can fail under system load and return nothing — that was
    causing false 'profile unreadable' recover loops)."""
    xml = ""
    for _ in range(4):
        adb("shell", "uiautomator", "dump", "/sdcard/_ui.xml")
        xml = adb("exec-out", "cat", "/sdcard/_ui.xml").stdout or ""
        if len(xml) > 2000 and "<node" in xml:
            return xml
        time.sleep(2)
    return xml


def _center(bounds):
    m = re.search(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
    if not m:
        return None
    x1, y1, x2, y2 = map(int, m.groups())
    return (x1 + x2) // 2, (y1 + y2) // 2


def nodes(xml):
    return re.findall(r'<node[^>]*>', xml)


def attr(node, name):
    m = re.search(rf'{name}="([^"]*)"', node)
    return m.group(1) if m else ""


def find(xml, *, text=None, desc=None, desc_contains=None,
         rid_contains=None, clickable=None):
    """Return (x, y) center of the first node matching all given filters."""
    for n in nodes(xml):
        if text is not None and attr(n, "text") != text:
            continue
        if desc is not None and attr(n, "content-desc") != desc:
            continue
        if desc_contains is not None and desc_contains.lower() not in attr(n, "content-desc").lower():
            continue
        if rid_contains is not None and rid_contains not in attr(n, "resource-id"):
            continue
        if clickable is not None and attr(n, "clickable") != ("true" if clickable else "false"):
            continue
        c = _center(attr(n, "bounds"))
        if c:
            return c
    return None


def post_count(xml):
    for n in nodes(xml):
        if "post_count_value" in attr(n, "resource-id"):
            t = attr(n, "text").replace(",", "")
            try:
                return int(t)
            except ValueError:
                return None
    return None


def active_handle(xml):
    for n in nodes(xml):
        if attr(n, "resource-id").endswith("action_bar_title"):
            return attr(n, "text")
    return "?"


def action_blocked(xml):
    low = xml.lower()
    return any(s in low for s in (
        "action blocked", "try again later", "we restrict",
        "temporarily blocked", "couldn't delete", "something went wrong",
    ))


def relaunch_ig():
    """Force-stop + relaunch Instagram to clear stuck popups/interstitials.
    Generous wait — IG is slow to boot when the machine is under sourcing load."""
    adb("shell", "am", "force-stop", "com.instagram.android")
    time.sleep(3)
    adb("shell", "monkey", "-p", "com.instagram.android",
        "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(14)


def goto_profile():
    """Ensure we're on the profile grid (Profile tab is bottom-right)."""
    tap(972, 1876)
    time.sleep(5)


def read_profile(expect_handle):
    """Robustly land on the profile and return (handle, post_count).
    Under load a single profile-tab tap can miss (IG mid-load) or fail to exit
    an opened post — so we double-tap, then fall back to a full IG relaunch.
    Returns (handle, count) where count may be None only if all retries fail."""
    for attempt in range(5):
        goto_profile()
        xml = dump()
        cnt = post_count(xml)
        if cnt is not None:
            return active_handle(xml), cnt, xml
        # second tap in case IG was still rendering / on a nested view
        time.sleep(3)
        tap(972, 1876)
        time.sleep(4)
        xml = dump()
        cnt = post_count(xml)
        if cnt is not None:
            return active_handle(xml), cnt, xml
        print(f"[recover] profile unreadable (try {attempt+1}/5) — relaunching IG",
              flush=True)
        back(); time.sleep(1); back(); time.sleep(1)
        relaunch_ig()
    return active_handle(dump()), None, None


def open_first_post(xml):
    """Tap the first grid item (row 1, column 1)."""
    c = find(xml, desc_contains="row 1, column 1")
    if not c:
        # fallback: first content-desc that looks like a grid media item
        for n in nodes(xml):
            d = attr(n, "content-desc").lower()
            if ("reel by" in d or "post by" in d or "photo by" in d) and "at row" in d:
                c = _center(attr(n, "bounds"))
                if c:
                    break
    if not c:
        return False
    tap(*c)
    time.sleep(3)
    return True


def delete_open_post():
    """From an opened post/reel: ⋮ -> (scroll) Delete -> confirm. Returns status."""
    # The opened post can lag under system load — retry finding the ⋮ button
    # a few times before giving up (this was the false 'no_options' failure).
    opts = None
    for _ in range(5):
        xml = dump()
        opts = find(xml, desc_contains="more actions") \
            or find(xml, rid_contains="media_option_button")
        if opts:
            break
        time.sleep(2.5)
    if not opts:
        return "no_options"
    tap(*opts)
    time.sleep(2.5)

    # The options sheet is long & scrollable; Delete is the last item.
    dele = None
    for _ in range(4):
        xml = dump()
        dele = find(xml, text="Delete") or find(xml, desc="Delete")
        if dele:
            break
        adb("shell", "input", "swipe", "540", "1500", "540", "600", "400")
        time.sleep(1.5)
    if not dele:
        back()
        return "no_delete_item"
    tap(*dele)
    time.sleep(2)

    xml = dump()
    if action_blocked(xml):
        return "blocked"
    # confirm dialog ("Delete reel?") — the clickable Delete button
    confirm = find(xml, text="Delete", clickable=True) or find(xml, text="Delete")
    if confirm:
        tap(*confirm)
        time.sleep(4)
    xml = dump()
    if action_blocked(xml):
        return "blocked"
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=0, help="max deletions (0 = until empty)")
    ap.add_argument("--min-delay", type=float, default=22.0)
    ap.add_argument("--max-delay", type=float, default=48.0)
    ap.add_argument("--block-backoff", type=float, default=1800.0,
                    help="seconds to wait when Instagram action-blocks deletions")
    ap.add_argument("--expect-handle", default="godforbidyougot_motion",
                    help="safety: refuse to run unless this account is active")
    args = ap.parse_args()

    goto_profile()
    xml = dump()
    handle = active_handle(xml)
    start = post_count(xml)
    print(f"[safety] active account = {handle} | posts = {start}", flush=True)
    if args.expect_handle and handle != args.expect_handle:
        print(f"[ABORT] active account '{handle}' != expected '{args.expect_handle}'. "
              f"Switch accounts first. Nothing deleted.", flush=True)
        sys.exit(2)

    deleted = 0
    consecutive_blocks = 0
    while True:
        if args.max and deleted >= args.max:
            print(f"[done] reached --max {args.max}", flush=True)
            break

        handle, cnt, xml = read_profile(args.expect_handle)
        if args.expect_handle and handle != args.expect_handle:
            print(f"[ABORT] active account became '{handle}' — stopping.", flush=True)
            break
        if cnt is None:
            print("[stop] profile unreadable after 4 relaunch retries. Manual check needed.", flush=True)
            break
        if cnt == 0:
            print("[done] 0 posts remaining — profile cleared.", flush=True)
            break
        if not open_first_post(xml):
            print(f"[recover] no grid post found (count={cnt}) — relaunching IG and retrying.", flush=True)
            relaunch_ig()
            continue

        status = delete_open_post()
        if status == "ok":
            deleted += 1
            consecutive_blocks = 0
            print(f"[del] #{deleted}  (~{(start - deleted) if start else '?'} left)", flush=True)
        elif status == "blocked":
            consecutive_blocks += 1
            if consecutive_blocks >= 3:
                print("[STOP] blocked 3x in a row — Instagram is hard-limiting. "
                      "Stopping so we don't risk the account. Re-run tomorrow; it resumes.", flush=True)
                break
            mins = args.block_backoff / 60
            print(f"[BLOCKED] action-block #{consecutive_blocks}. Backing off {mins:.0f} min "
                  f"then continuing (resumable).", flush=True)
            back(); time.sleep(2)
            time.sleep(args.block_backoff)
            continue
        else:
            print(f"[warn] delete flow returned '{status}' — going back and retrying.", flush=True)
            back(); time.sleep(2); back(); time.sleep(2)
            continue

        delay = random.uniform(args.min_delay, args.max_delay)
        print(f"[pace] sleeping {delay:.0f}s", flush=True)
        time.sleep(delay)

    goto_profile()
    xml = dump()
    print(f"[final] active={active_handle(xml)}  posts_remaining={post_count(xml)}  deleted_this_run={deleted}",
          flush=True)


if __name__ == "__main__":
    main()
