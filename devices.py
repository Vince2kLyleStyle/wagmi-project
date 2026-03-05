"""
Fader v2 — Device Settings
Provides a realistic Android device profile for instagrapi.
"""

import random

# Samsung Galaxy S24 Ultra — common, looks normal
_DEVICE = {
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
}


def get_device() -> dict:
    """Return a fixed, realistic device profile."""
    return dict(_DEVICE)
