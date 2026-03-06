"""
Fader v2 — Session Tracker
Tracks uploads per account for visibility. Does NOT gate or block uploads.
The strategy is aggressive burst posting (3 reels every 30 min) to hit
the FYP fast. If IG flags something, handle it manually.

This module provides:
  - Per-account upload counting and stats
  - Event logging (rate limits, challenges) for diagnostics
  - Cooldowns ONLY for actual Instagram errors (rate limits, challenges)
    NOT for normal posting cadence
"""

import json
import os
import random
from datetime import datetime, timedelta


# ─── Cooldowns (only for actual IG errors, not posting cadence) ─────
COOLDOWNS = {
    "rate_limited":      (30, 60),     # 30-60 min after rate limit
    "challenge":         (120, 240),   # 2-4 hours after challenge
    "feedback_required": (60, 120),    # 1-2 hours after feedback
    "login_failed":      (15, 30),     # 15-30 min after login failure
}

# ─── Session State File ─────────────────────────────────────────────
SAFETY_DIR = os.path.join(os.path.dirname(__file__), "sessions", "safety")


def _state_path(username: str) -> str:
    os.makedirs(SAFETY_DIR, exist_ok=True)
    return os.path.join(SAFETY_DIR, f"{username}_safety.json")


def _load_state(username: str) -> dict:
    path = _state_path(username)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {
        "username": username,
        "first_automated": None,
        "uploads_today": 0,
        "today_date": None,
        "last_upload_time": None,
        "consecutive_failures": 0,
        "cooldown_until": None,
        "total_uploads": 0,
        "events": [],
    }


def _save_state(username: str, state: dict) -> None:
    path = _state_path(username)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def _days_automated(state: dict) -> int:
    if not state.get("first_automated"):
        return 0
    first = datetime.fromisoformat(state["first_automated"])
    return (datetime.now() - first).days


# ─── Public API ──────────────────────────────────────────────────────

def get_daily_limit(username: str) -> int:
    """
    Return the daily post target. This is NOT a hard block — it's just
    the target the bot aims for. Config drives it.
    """
    # Import here to avoid circular imports
    import config
    return random.randint(config.DAILY_MIN, config.DAILY_MAX)


def get_post_gap(username: str) -> int:
    """
    Return the gap between bursts (seconds).
    Driven by config INTER_BATCH settings — the 30-min burst cadence.
    """
    import config
    center = config.INTER_BATCH_CENTER
    spread = config.INTER_BATCH_SPREAD
    floor = config.INTER_BATCH_FLOOR
    ceil = config.INTER_BATCH_CEIL
    gap = random.gauss(center, spread)
    gap = max(floor, min(ceil, gap))
    return int(gap)


def can_upload(username: str) -> tuple[bool, str]:
    """
    Check if there's an active cooldown from an Instagram error.
    Normal posting cadence is NOT gated — only actual IG errors trigger blocks.
    """
    state = _load_state(username)
    today = datetime.now().strftime("%Y-%m-%d")

    # Reset daily counter if it's a new day
    if state.get("today_date") != today:
        state["uploads_today"] = 0
        state["today_date"] = today
        state["consecutive_failures"] = 0
        state["cooldown_until"] = None
        _save_state(username, state)

    # Only check cooldown from actual IG errors
    if state.get("cooldown_until"):
        cooldown_end = datetime.fromisoformat(state["cooldown_until"])
        if datetime.now() < cooldown_end:
            remaining = (cooldown_end - datetime.now()).total_seconds()
            return False, f"Cooling down — {remaining/60:.0f}min remaining (IG error)"

    return True, "OK"


def record_upload(username: str) -> None:
    """Record a successful upload."""
    state = _load_state(username)
    today = datetime.now().strftime("%Y-%m-%d")

    if state.get("today_date") != today:
        state["uploads_today"] = 0
        state["today_date"] = today

    if not state.get("first_automated"):
        state["first_automated"] = datetime.now().isoformat()

    state["uploads_today"] += 1
    state["total_uploads"] = state.get("total_uploads", 0) + 1
    state["last_upload_time"] = datetime.now().isoformat()
    state["consecutive_failures"] = 0
    _save_state(username, state)


def record_failure(username: str, failure_type: str = "upload_failed") -> None:
    """Record a failed upload or IG error. Only applies cooldown for real IG errors."""
    state = _load_state(username)
    state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1

    # Log the event
    events = state.get("events", [])
    events.append({
        "type": failure_type,
        "time": datetime.now().isoformat(),
    })
    state["events"] = events[-50:]

    # Apply cooldown ONLY for actual IG errors (not generic upload failures)
    if failure_type in COOLDOWNS:
        min_cd, max_cd = COOLDOWNS[failure_type]
        cooldown_min = random.randint(min_cd, max_cd)
        state["cooldown_until"] = (
            datetime.now() + timedelta(minutes=cooldown_min)
        ).isoformat()
        print(f"  [safety] Cooldown: {cooldown_min}min ({failure_type})")

    _save_state(username, state)


def get_account_status(username: str) -> dict:
    """Get a status summary for an account."""
    state = _load_state(username)
    days = _days_automated(state)

    import config
    daily_limit = random.randint(config.DAILY_MIN, config.DAILY_MAX)

    return {
        "username": username,
        "days_automated": days,
        "tier": f"Burst mode — {config.BATCH_SIZE} reels every ~{config.INTER_BATCH_CENTER//60}min",
        "uploads_today": state.get("uploads_today", 0),
        "daily_limit": daily_limit,
        "total_uploads": state.get("total_uploads", 0),
        "consecutive_failures": state.get("consecutive_failures", 0),
        "cooldown_until": state.get("cooldown_until"),
        "can_upload": can_upload(username),
    }


def print_account_status(username: str) -> None:
    """Print a formatted account status."""
    s = get_account_status(username)
    print(f"\n  {'─'*50}")
    print(f"  Status: @{s['username']}")
    print(f"  {'─'*50}")
    print(f"  Running for:    {s['days_automated']} days")
    print(f"  Mode:           {s['tier']}")
    print(f"  Today:          {s['uploads_today']} uploads")
    print(f"  All-time:       {s['total_uploads']} uploads")
    can, reason = s["can_upload"]
    status = "READY" if can else f"PAUSED — {reason}"
    print(f"  Status:         {status}")
    if s["cooldown_until"]:
        print(f"  Cooldown until: {s['cooldown_until']}")
    print(f"  {'─'*50}\n")
