"""
Fader v2 — Device / Fingerprint Rotation
Generates realistic random iPhone & Android device profiles for each session.
instagrapi uses these to build its User-Agent and X-headers.
"""

import random

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


def random_iphone_settings() -> dict:
    """Return an instagrapi-compatible device settings dict for a random iPhone."""
    model_id, name, ios_ver, dpi, res = random.choice(IPHONE_MODELS)
    locale, tz = random.choice(LOCALES)
    ig_ver = random.choice(IG_VERSIONS)
    w, h = res.split("x")

    return {
        "app_version":   ig_ver,
        "android_version": 0,   # ignored for iPhone but instagrapi may need it
        "android_release": "",
        "dpi":           dpi,
        "resolution":    res,
        "manufacturer":  "Apple",
        "device":        model_id,
        "model":         name,
        "cpu":           "0",
        "version_code":  "",
    }


def random_android_settings() -> dict:
    """Return an instagrapi-compatible device settings dict for a random Android."""
    mfr, model, device, api, release, dpi, res = random.choice(ANDROID_MODELS)
    locale, tz = random.choice(LOCALES)
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


def random_device_settings() -> dict:
    """Pick a random iPhone or Android profile (70/30 split favoring iPhone)."""
    if random.random() < 0.7:
        return random_iphone_settings()
    return random_android_settings()
