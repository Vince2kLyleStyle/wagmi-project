#!/usr/bin/env python3
"""
Transform godforbidyougot_motion -> "topcats online" via IG Edit Profile
(BlueStacks + ADB, uiautomator-driven). Sets display name, username, and bio.
Reuses the proven find-by-text/desc approach from delete_all_posts.py so it
survives layout shifts. Safety-guarded to the expected handle.

The Edit Profile field resource-ids differ across IG versions, so the flow is
selector-driven with an --inspect mode to map the live screen first.

Usage:
    # 1) after the wipe, map the Edit Profile screen:
    python transform_account.py --inspect
    # 2) dry-run: read current name/username/bio without changing anything:
    python transform_account.py --dry-run
    # 3) apply (only fields you pass are changed):
    python transform_account.py --name "topcats online" \
        --username "topcats.online" \
        --bio "your daily dose of funny cats hello kitty & friends\n#kitty"

Pfp is NOT handled here (image picker is fragile) — set it manually or with a
dedicated helper once an image file exists.
"""
import argparse
import re
import subprocess
import sys
import time

SERIAL = "127.0.0.1:5555"


def adb(*args, timeout=30):
    try:
        return subprocess.run(["adb", "-s", SERIAL, *args],
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"[warn] adb timed out ({timeout}s): {' '.join(args)[:50]}", flush=True)
        return subprocess.CompletedProcess(args, returncode=-1, stdout="", stderr="")


def tap(x, y):
    adb("shell", "input", "tap", str(x), str(y))
    time.sleep(1)


def back():
    adb("shell", "input", "keyevent", "KEYCODE_BACK")
    time.sleep(1)


def dump():
    xml = ""
    for _ in range(4):
        adb("shell", "uiautomator", "dump", "/sdcard/_tx.xml")
        xml = adb("exec-out", "cat", "/sdcard/_tx.xml").stdout or ""
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


def find(xml, *, text=None, text_contains=None, desc=None, desc_contains=None,
         rid_contains=None, clazz=None):
    for n in nodes(xml):
        if text is not None and attr(n, "text") != text:
            continue
        if text_contains is not None and text_contains.lower() not in attr(n, "text").lower():
            continue
        if desc is not None and attr(n, "content-desc") != desc:
            continue
        if desc_contains is not None and desc_contains.lower() not in attr(n, "content-desc").lower():
            continue
        if rid_contains is not None and rid_contains not in attr(n, "resource-id"):
            continue
        if clazz is not None and attr(n, "class") != clazz:
            continue
        c = _center(attr(n, "bounds"))
        if c:
            return c
    return None


def active_handle(xml):
    for n in nodes(xml):
        if attr(n, "resource-id").endswith("action_bar_title"):
            return attr(n, "text")
    return "?"


def goto_profile():
    tap(972, 1876)
    time.sleep(4)


def open_edit_profile():
    """Profile grid -> 'Edit profile' button."""
    xml = dump()
    c = (find(xml, text="Edit profile")
         or find(xml, desc="Edit profile")
         or find(xml, text_contains="edit profile"))
    if not c:
        return False, xml
    tap(*c)
    time.sleep(3)
    return True, dump()


def set_text_field(label_regexes, value):
    """Find an EditText/row by nearby label, focus it, clear, type `value`.
    label_regexes: substrings that identify the field (e.g. 'name','username').
    Returns True on a best-effort apply. Refine selectors via --inspect."""
    xml = dump()
    target = None
    # Strategy 1: an EditText whose text/hint mentions the label.
    for lbl in label_regexes:
        target = find(xml, rid_contains=lbl, clazz="android.widget.EditText")
        if target:
            break
    # Strategy 2: a row with the label text -> tap it (opens a sub-editor).
    if not target:
        for lbl in label_regexes:
            target = find(xml, text_contains=lbl)
            if target:
                break
    if not target:
        print(f"  [miss] could not locate field for {label_regexes}")
        return False
    tap(*target)
    time.sleep(1)
    # clear existing text: select all + delete
    adb("shell", "input", "keyevent", "KEYCODE_MOVE_END")
    for _ in range(120):
        adb("shell", "input", "keyevent", "KEYCODE_DEL")
    # type new value (spaces need %s for adb input text)
    adb("shell", "input", "text", value.replace(" ", "%s"))
    time.sleep(1)
    print(f"  [set] {label_regexes[0]} -> {value[:40]}")
    return True


def read_profile_fields(xml):
    """Best-effort read of current editable field values on Edit Profile."""
    out = {}
    for n in nodes(xml):
        rid = attr(n, "resource-id")
        txt = attr(n, "text")
        for key in ("name", "username", "bio"):
            if key in rid.lower() and txt:
                out[key] = txt
    return out


def inspect():
    """Dump every interactive element on the Edit Profile screen so the field
    selectors can be verified against this IG version."""
    goto_profile()
    ok, xml = open_edit_profile()
    if not ok:
        print("[inspect] could not open Edit profile (are we on the profile tab?)")
        return
    print("[inspect] Edit Profile interactive elements:")
    for n in nodes(xml):
        rid = attr(n, "resource-id")
        txt = attr(n, "text")
        desc = attr(n, "content-desc")
        clazz = attr(n, "class")
        if clazz in ("android.widget.EditText", "android.widget.Button") or txt or desc:
            short_rid = rid.split("/")[-1] if rid else ""
            if short_rid or txt or desc:
                print(f"  {clazz.split('.')[-1]:10} id={short_rid:28} "
                      f"text={txt!r:30} desc={desc!r}")


def save_profile():
    """Tap the checkmark / Done to persist changes."""
    xml = dump()
    c = (find(xml, desc="Done") or find(xml, text="Done")
         or find(xml, desc_contains="check") or find(xml, rid_contains="action_bar_button_action"))
    if c:
        tap(*c)
        time.sleep(2)
        return True
    print("  [warn] Save/Done button not found — verify manually")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-handle", default="godforbidyougot_motion")
    ap.add_argument("--name", default=None)
    ap.add_argument("--username", default=None)
    ap.add_argument("--bio", default=None)
    ap.add_argument("--inspect", action="store_true",
                    help="dump the Edit Profile screen and exit (map selectors)")
    ap.add_argument("--dry-run", action="store_true",
                    help="read current fields, change nothing")
    args = ap.parse_args()

    goto_profile()
    xml = dump()
    handle = active_handle(xml)
    print(f"[safety] active account = {handle}", flush=True)
    if args.expect_handle and handle != args.expect_handle:
        print(f"[ABORT] active '{handle}' != expected '{args.expect_handle}'. Nothing changed.")
        sys.exit(2)

    if args.inspect:
        inspect()
        return

    ok, xml = open_edit_profile()
    if not ok:
        print("[stop] could not open Edit profile.")
        sys.exit(1)

    if args.dry_run:
        print("[dry-run] current fields:", read_profile_fields(xml))
        return

    changed = False
    if args.name is not None:
        changed |= set_text_field(["full_name", "name"], args.name)
        back()  # leave any sub-editor
    if args.username is not None:
        changed |= set_text_field(["username"], args.username)
        back()
    if args.bio is not None:
        changed |= set_text_field(["bio", "biography"], args.bio.replace("\\n", "\n"))
        back()

    if changed:
        save_profile()
        print("[done] profile updates submitted. Verify in-app (username may need"
              " to be unique; IG will reject a taken handle).")
    else:
        print("[noop] no fields changed.")


if __name__ == "__main__":
    main()
