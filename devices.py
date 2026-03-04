"""
Fader v2 — Device / Fingerprint Management
Generates realistic random iPhone & Android device profiles.
Picks ONE device per day and sticks with it (rotating mid-session is a red flag).
"""

import hashlib
import json
import os
import random
from datetime import date
from pathlib import Path

# ─── iPhone Models ──────────────────────────────────────────────────
# (model_name, device_id, ios_version, screen_dpi, screen_resolution)
IPHONE_MODELS = [
    ("iPhone14,5",  "iPhone 13",         "17.4.1", "460dpi", "1170x2532"),
    ("iPhone14,2",  "iPhone 13 Pro",     "17.3",   "460dpi", "1170x2532"),
    ("iPhone14,3",  "iPhone 13 Pro Max", "17.5",   "458dpi", "1284x2778"),
    ("iPhone15,2",  "iPhone 14 Pro",     "17.4",   "460dpi", "1179x2556"),
    ("iPhone15,3",  "iPhone 14 Pro Max", "17.4.1", "460dpi", "1290x2796"),
    ("iPhone15,4",  "iPhone 15",         "18.0",   "460dpi", "1179x2556"),
    ("iPhone15,5",  "iPhone 15 Plus",    "18.0.1", "460dpi", "1290x2796"),
    ("iPhone16,1",  "iPhone 15 Pro",     "18.1",   "460dpi", "1179x2556"),
    ("iPhone16,2",  "iPhone 15 Pro Max", "18.1",   "460dpi", "1290x2796"),
    ("iPhone17,1",  "iPhone 16 Pro",     "18.2",   "460dpi", "1206x2622"),
    ("iPhone17,2",  "iPhone 16 Pro Max", "18.2",   "460dpi", "1320x2868"),
]

# ─── Android Models ─────────────────────────────────────────────────
# (manufacturer, model, device, android_version, android_release, dpi, resolution)
ANDROID_MODELS = [
    ("samsung",  "SM-S928B",  "e3q",       33, "14", "640dpi", "1440x3120"),
    ("samsung",  "SM-S926B",  "e2q",       33, "14", "480dpi", "1080x2340"),
    ("samsung",  "SM-S921B",  "e1q",       33, "14", "480dpi", "1080x2340"),
    ("samsung",  "SM-A556B",  "a55xq",     34, "14", "480dpi", "1080x2340"),
    ("Google",   "Pixel 8 Pro", "husky",   34, "14", "480dpi", "1344x2992"),
    ("Google",   "Pixel 9 Pro", "caiman",  35, "15", "480dpi", "1280x2856"),
    ("OnePlus",  "CPH2551",   "OP5913L1",  34, "14", "480dpi", "1080x2412"),
    ("Xiaomi",   "2312DRA50G","aurora",    34, "14", "440dpi", "1220x2712"),
]

# ─── Locales ────────────────────────────────────────────────────────
LOCALES = [
    ("en_US", "GMT-5"),
    ("en_US", "GMT-8"),
    ("en_US", "GMT-6"),
    ("en_GB", "GMT+0"),
    ("en_CA", "GMT-5"),
    ("en_AU", "GMT+10"),
]

# ─── IG App Versions (keep updated) ────────────────────────────────
IG_VERSIONS = [
    "345.0.0.0.93",
    "344.0.0.0.91",
    "343.0.0.0.88",
    "342.0.0.0.90",
    "341.0.0.0.85",
]

# ─── Device cache file ─────────────────────────────────────────────
_DEVICE_CACHE = os.path.join(os.path.dirname(__file__), "sessions", ".device_today.json")


def _make_iphone_settings() -> dict:
    """Return an instagrapi-compatible device settings dict for a random iPhone."""
    model_id, name, ios_ver, dpi, res = random.choice(IPHONE_MODELS)
    ig_ver = random.choice(IG_VERSIONS)

    return {
        "app_version":   ig_ver,
        "android_version": 0,
        "android_release": "",
        "dpi":           dpi,
        "resolution":    res,
        "manufacturer":  "Apple",
        "device":        model_id,
        "model":         name,
        "cpu":           "0",
        "version_code":  "",
    }


def _make_android_settings() -> dict:
    """Return an instagrapi-compatible device settings dict for a random Android."""
    mfr, model, device, api, release, dpi, res = random.choice(ANDROID_MODELS)
    ig_ver = random.choice(IG_VERSIONS)

    return {
        "app_version":     ig_ver,
        "android_version": api,
        "android_release": release,
        "dpi":             dpi,
        "resolution":      res,
        "manufacturer":    mfr,
        "device":          device,
        "model":           model,
        "cpu":             "qcom",
        "version_code":    "",
    }


def _generate_random_device() -> dict:
    """Pick a random iPhone or Android profile (70/30 split favoring Android)."""
    # Android is the safer bet for private API — most real instagrapi traffic is Android
    if random.random() < 0.7:
        return _make_android_settings()
    return _make_iphone_settings()


def get_device_for_today() -> dict:
    """
    Return a consistent device profile for today.
    Generates one per day and caches it. A real user doesn't switch phones
    mid-session, so neither should we.
    """
    today = date.today().isoformat()

    # Try loading today's cached device
    try:
        if os.path.exists(_DEVICE_CACHE):
            with open(_DEVICE_CACHE, "r") as f:
                cached = json.load(f)
            if cached.get("date") == today:
                print(f"  [device] Reusing today's device: {cached['device'].get('model', '?')}")
                return cached["device"]
    except (json.JSONDecodeError, KeyError):
        pass

    # Generate fresh device for today
    device = _generate_random_device()

    # Cache it
    try:
        os.makedirs(os.path.dirname(_DEVICE_CACHE), exist_ok=True)
        with open(_DEVICE_CACHE, "w") as f:
            json.dump({"date": today, "device": device}, f, indent=2)
    except OSError:
        pass  # Non-fatal — worst case we regenerate next run

    print(f"  [device] New device for today: {device.get('manufacturer')} {device.get('model')}")
    return device
