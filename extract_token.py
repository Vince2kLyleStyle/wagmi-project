"""
BlueStacks Token Extractor
==========================
Run this AFTER logging into Instagram inside BlueStacks.
Pulls your real auth credentials directly from the Instagram app via ADB.

Usage:
    python extract_token.py

Requirements:
    - BlueStacks running with ADB enabled (Settings > Advanced > Android Debug Bridge ON)
    - Instagram logged in inside BlueStacks
"""

import subprocess
import json
import re
import os
import sys


def run_adb(cmd: list) -> str:
    try:
        result = subprocess.run(
            ["adb"] + cmd,
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip()
    except FileNotFoundError:
        print("[!!] ADB not found. Make sure BlueStacks ADB is enabled and")
        print("     Android Platform Tools are installed or BlueStacks ADB path is in PATH.")
        print("     BlueStacks ADB is usually at:")
        print("     C:\\Program Files\\BlueStacks_nxt\\HD-Adb.exe")
        sys.exit(1)
    except Exception as e:
        print(f"[!!] ADB error: {e}")
        return ""


def check_device():
    out = run_adb(["devices"])
    lines = [l for l in out.splitlines() if "\tdevice" in l]
    if not lines:
        print("[!!] No BlueStacks device found via ADB.")
        print("     1. Open BlueStacks")
        print("     2. Go to Settings > Advanced > Turn ON Android Debug Bridge")
        print("     3. Re-run this script")
        sys.exit(1)
    print(f"[+] Device found: {lines[0].split()[0]}")


def get_root():
    out = run_adb(["root"])
    if "adbd is already running as root" in out or "restarting adbd as root" in out:
        print("[+] Root access confirmed")
        return True
    # BlueStacks may need a different approach
    print("[~] Root via 'adb root' failed, trying su shell...")
    return False


def extract_instagram_prefs(use_su: bool) -> str:
    """Pull Instagram shared preferences — contains session tokens."""
    prefs_path = "/data/data/com.instagram.android/shared_prefs/"

    if use_su:
        cmd = ["shell", "su", "-c", f"ls {prefs_path}"]
    else:
        cmd = ["shell", f"ls {prefs_path}"]

    files = run_adb(cmd)
    if not files:
        print("[!!] Could not list Instagram prefs. Is Instagram installed and logged in?")
        sys.exit(1)

    # Find the main prefs file
    target = None
    for line in files.splitlines():
        if "instagram.android_preferences" in line or "sessionid" in line.lower():
            target = line.strip()
            break
    if not target:
        # Just grab the first xml
        for line in files.splitlines():
            if line.strip().endswith(".xml"):
                target = line.strip()
                break

    if not target:
        print("[!!] No Instagram preferences file found.")
        sys.exit(1)

    print(f"[+] Reading: {target}")

    if use_su:
        cmd = ["shell", "su", "-c", f"cat {prefs_path}{target}"]
    else:
        cmd = ["shell", f"cat {prefs_path}{target}"]

    return run_adb(cmd)


def extract_from_db(use_su: bool) -> dict:
    """Try to get session from the accounts database."""
    db_path = "/data/data/com.instagram.android/databases/"

    if use_su:
        ls_cmd = ["shell", "su", "-c", f"ls {db_path}"]
    else:
        ls_cmd = ["shell", f"ls {db_path}"]

    files = run_adb(ls_cmd)
    results = {}

    for line in files.splitlines():
        fname = line.strip()
        if "direct" in fname.lower() or "instacrypt" in fname.lower():
            continue
        if fname.endswith(".db"):
            if use_su:
                q = f"su -c \"sqlite3 {db_path}{fname} 'SELECT * FROM accounts LIMIT 5'\""
                out = run_adb(["shell", q])
            else:
                out = run_adb(["shell", f"sqlite3 {db_path}{fname} 'SELECT * FROM accounts LIMIT 5'"])
            if out and "|" in out:
                results[fname] = out

    return results


def parse_credentials(prefs_xml: str) -> dict:
    creds = {}

    # Session ID
    m = re.search(r'name="sessionid[^"]*"[^>]*>([^<]+)<', prefs_xml, re.IGNORECASE)
    if m:
        creds["sessionid"] = m.group(1).strip()

    # DS User ID (numeric user ID)
    m = re.search(r'name="ds_user_id"[^>]*>([^<]+)<', prefs_xml, re.IGNORECASE)
    if m:
        creds["ds_user_id"] = m.group(1).strip()

    # Username
    m = re.search(r'name="[^"]*username[^"]*"[^>]*>([^<]+)<', prefs_xml, re.IGNORECASE)
    if m:
        creds["username"] = m.group(1).strip()

    # Device ID
    m = re.search(r'name="device_id"[^>]*>([^<]+)<', prefs_xml, re.IGNORECASE)
    if m:
        creds["device_id"] = m.group(1).strip()

    # Phone ID / Family Device ID
    m = re.search(r'name="(phone_id|family_device_id)"[^>]*>([^<]+)<', prefs_xml, re.IGNORECASE)
    if m:
        creds["phone_id"] = m.group(2).strip()

    # Authorization token (IGT:2:...)
    m = re.search(r'name="[^"]*auth[^"]*token[^"]*"[^>]*>([^<]+)<', prefs_xml, re.IGNORECASE)
    if not m:
        m = re.search(r'(IGT:2:[A-Za-z0-9+/=]+)', prefs_xml)
    if m:
        creds["auth_token"] = m.group(1).strip()

    return creds


def main():
    print("\n=== BlueStacks Instagram Token Extractor ===\n")

    check_device()
    has_root = get_root()

    # Give adb root time to restart
    import time
    time.sleep(2)

    print("\n[*] Extracting Instagram credentials...")
    prefs = extract_instagram_prefs(not has_root)

    if not prefs:
        print("[!!] Could not read Instagram preferences.")
        sys.exit(1)

    creds = parse_credentials(prefs)

    if not creds.get("sessionid") and not creds.get("auth_token"):
        print("\n[!!] Could not parse session token from prefs.")
        print("     Dumping raw content for manual inspection:\n")
        print(prefs[:3000])
        sys.exit(1)

    print("\n[+] Credentials extracted successfully!\n")
    print("=" * 50)
    for k, v in creds.items():
        masked = v[:8] + "***" if len(v) > 8 else v
        print(f"  {k}: {masked}")
    print("=" * 50)

    # Write to token.json
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bluestacks_token.json")
    with open(out_path, "w") as f:
        json.dump(creds, f, indent=2)

    print(f"\n[+] Saved to: {out_path}")
    print("\n[*] Now run: python fader_reels.py")
    print("    The bot will automatically use your real BlueStacks credentials.\n")


if __name__ == "__main__":
    main()
