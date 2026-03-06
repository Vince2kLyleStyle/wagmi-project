"""
Fader v2 — Device Fingerprint Pool
Provides realistic Android device profiles for instagrapi.

Each account gets ONE consistent device (assigned on first use and persisted).
Mid-session device rotation is a major red flag for Instagram.
"""

import hashlib
import json
import os
import random

# ─── Device Pool ─────────────────────────────────────────────────────
# Multiple realistic, popular Android devices.
# Instagram sees thousands of real users on each of these.

DEVICE_POOL = [
    {
        "app_version":     "345.0.0.0.93",
        "android_version": 34,
        "android_release": "14",
        "dpi":             "640dpi",
        "resolution":      "1440x3120",
        "manufacturer":    "samsung",
        "device":          "e3q",
        "model":           "SM-S928B",
        "cpu":             "qcom",
        "version_code":    "",
    },
    {
        "app_version":     "345.0.0.0.93",
        "android_version": 34,
        "android_release": "14",
        "dpi":             "560dpi",
        "resolution":      "1440x3088",
        "manufacturer":    "samsung",
        "device":          "dm3q",
        "model":           "SM-S911B",
        "cpu":             "qcom",
        "version_code":    "",
    },
    {
        "app_version":     "345.0.0.0.93",
        "android_version": 34,
        "android_release": "14",
        "dpi":             "420dpi",
        "resolution":      "1080x2400",
        "manufacturer":    "Google",
        "device":          "husky",
        "model":           "Pixel 8 Pro",
        "cpu":             "tensor",
        "version_code":    "",
    },
    {
        "app_version":     "345.0.0.0.93",
        "android_version": 33,
        "android_release": "13",
        "dpi":             "440dpi",
        "resolution":      "1080x2340",
        "manufacturer":    "OnePlus",
        "device":          "OP5913L1",
        "model":           "CPH2449",
        "cpu":             "qcom",
        "version_code":    "",
    },
    {
        "app_version":     "345.0.0.0.93",
        "android_version": 34,
        "android_release": "14",
        "dpi":             "480dpi",
        "resolution":      "1284x2778",
        "manufacturer":    "Xiaomi",
        "device":          "marble",
        "model":           "23049PCD8G",
        "cpu":             "qcom",
        "version_code":    "",
    },
    {
        "app_version":     "345.0.0.0.93",
        "android_version": 33,
        "android_release": "13",
        "dpi":             "420dpi",
        "resolution":      "1080x2400",
        "manufacturer":    "samsung",
        "device":          "a54x",
        "model":           "SM-A546B",
        "cpu":             "exynos",
        "version_code":    "",
    },
]

# ─── Persistent Device Assignment ────────────────────────────────────
DEVICE_MAP_DIR = os.path.join(os.path.dirname(__file__), "sessions", "devices")


def _device_map_path() -> str:
    os.makedirs(DEVICE_MAP_DIR, exist_ok=True)
    return os.path.join(DEVICE_MAP_DIR, "device_assignments.json")


def _load_device_map() -> dict:
    path = _device_map_path()
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def _save_device_map(mapping: dict) -> None:
    with open(_device_map_path(), "w") as f:
        json.dump(mapping, f, indent=2)


def get_device(username: str | None = None) -> dict:
    """
    Return a realistic device profile.

    If username is provided, returns the same device every time for that
    account (persistent assignment). This prevents mid-session rotation
    which Instagram flags as suspicious.

    If no username, returns a deterministic device based on the current
    date (backwards compatible with old behavior).
    """
    if username:
        mapping = _load_device_map()
        if username in mapping:
            idx = mapping[username]
            return dict(DEVICE_POOL[idx % len(DEVICE_POOL)])
        else:
            # Assign a device deterministically based on username hash
            # so even if the map file is lost, we get a consistent result
            h = int(hashlib.md5(username.encode()).hexdigest(), 16)
            idx = h % len(DEVICE_POOL)
            mapping[username] = idx
            _save_device_map(mapping)
            return dict(DEVICE_POOL[idx])

    # Fallback: date-based (legacy behavior)
    from datetime import date
    day_seed = date.today().toordinal()
    idx = day_seed % len(DEVICE_POOL)
    return dict(DEVICE_POOL[idx])
