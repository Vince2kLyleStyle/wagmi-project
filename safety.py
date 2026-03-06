"""
Fader v2 — Anti-Ban Safety Module
Rate limiting, progressive ramp-up, session cooling, and action tracking
to prevent Instagram from flagging accounts.

The #1 reason for phone verification / action blocks is posting too much
too fast on a fresh or lightly-used account. This module enforces sane
limits that scale up gradually as the account matures.
"""

import json
import os
import random
import time
from datetime import datetime, timedelta


# ─── Account Age Tiers ──────────────────────────────────────────────
# How many days old is the account's *automation history* (not creation date)?
# We track when we first started posting from each account.
# Limits ramp up over weeks, not hours.

RAMP_UP_SCHEDULE = [
    # (days_automated, max_daily_posts, min_gap_minutes, max_gap_minutes)
    (0,   3,   90, 180),    # Day 0-2:   3 posts/day, 1.5-3hr gaps
    (3,   5,   60, 120),    # Day 3-6:   5 posts/day, 1-2hr gaps
    (7,   8,   45,  90),    # Week 1-2:  8 posts/day, 45-90min gaps
    (14, 12,   35,  75),    # Week 2-3: 12 posts/day, 35-75min gaps
    (21, 15,   25,  60),    # Week 3-4: 15 posts/day, 25-60min gaps
    (30, 20,   20,  50),    # Month 1+: 20 posts/day, 20-50min gaps
    (60, 25,   15,  40),    # Month 2+: 25 posts/day, 15-40min gaps
]

# Hard ceiling — never exceed this regardless of account age
ABSOLUTE_MAX_DAILY = 25
ABSOLUTE_MIN_GAP_MINUTES = 12

# ─── Action Cooldowns ───────────────────────────────────────────────
# After certain events, enforce mandatory cooldowns

COOLDOWNS = {
    "rate_limited":      (120, 240),   # 2-4 hours after rate limit
    "challenge":         (360, 720),   # 6-12 hours after challenge
    "feedback_required": (240, 480),   # 4-8 hours after feedback
    "login_failed":      (60, 120),    # 1-2 hours after login failure
    "upload_failed":     (10, 30),     # 10-30 min after upload failure
    "consecutive_fails": (60, 180),    # 1-3 hours after 3+ consecutive failures
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


def _get_tier(days: int) -> tuple:
    """Return the ramp-up tier for the given number of days automated."""
    tier = RAMP_UP_SCHEDULE[0]
    for threshold, *params in RAMP_UP_SCHEDULE:
        if days >= threshold:
            tier = (threshold, *params)
    return tier


# ─── Public API ──────────────────────────────────────────────────────

def get_daily_limit(username: str) -> int:
    """Get the safe daily post limit for this account based on automation age."""
    state = _load_state(username)
    days = _days_automated(state)
    _, max_daily, _, _ = _get_tier(days)
    # Add slight randomness (±1-2) so it's not always the exact same number
    jitter = random.randint(-1, 1)
    limit = max(1, min(max_daily + jitter, ABSOLUTE_MAX_DAILY))
    return limit


def get_post_gap(username: str) -> int:
    """Get the minimum gap (seconds) between posts for this account."""
    state = _load_state(username)
    days = _days_automated(state)
    _, _, min_gap_min, max_gap_min = _get_tier(days)
    # Gaussian distribution centered between min and max
    center = (min_gap_min + max_gap_min) / 2
    spread = (max_gap_min - min_gap_min) / 4
    gap_minutes = random.gauss(center, spread)
    gap_minutes = max(max(min_gap_min, ABSOLUTE_MIN_GAP_MINUTES),
                      min(max_gap_min, gap_minutes))
    return int(gap_minutes * 60)


def can_upload(username: str) -> tuple[bool, str]:
    """
    Check if it's safe to upload right now.
    Returns (can_upload, reason_if_not).
    """
    state = _load_state(username)
    today = datetime.now().strftime("%Y-%m-%d")

    # Reset daily counter if it's a new day
    if state.get("today_date") != today:
        state["uploads_today"] = 0
        state["today_date"] = today
        state["consecutive_failures"] = 0
        _save_state(username, state)

    # Check cooldown
    if state.get("cooldown_until"):
        cooldown_end = datetime.fromisoformat(state["cooldown_until"])
        if datetime.now() < cooldown_end:
            remaining = (cooldown_end - datetime.now()).total_seconds()
            return False, f"Cooling down — {remaining/60:.0f}min remaining"

    # Check daily limit
    days = _days_automated(state)
    _, max_daily, _, _ = _get_tier(days)
    limit = min(max_daily, ABSOLUTE_MAX_DAILY)

    if state["uploads_today"] >= limit:
        return False, f"Daily limit reached ({state['uploads_today']}/{limit})"

    # Check minimum gap since last upload
    if state.get("last_upload_time"):
        last = datetime.fromisoformat(state["last_upload_time"])
        elapsed = (datetime.now() - last).total_seconds()
        min_gap = ABSOLUTE_MIN_GAP_MINUTES * 60
        if elapsed < min_gap:
            wait = min_gap - elapsed
            return False, f"Too soon since last upload — wait {wait/60:.0f}min"

    # Check consecutive failures
    if state["consecutive_failures"] >= 3:
        return False, "3+ consecutive failures — session may be flagged"

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
    """Record a failed upload or error event."""
    state = _load_state(username)
    state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1

    # Log the event
    events = state.get("events", [])
    events.append({
        "type": failure_type,
        "time": datetime.now().isoformat(),
    })
    # Keep only last 50 events
    state["events"] = events[-50:]

    # Apply cooldown based on failure type
    if failure_type in COOLDOWNS:
        min_cd, max_cd = COOLDOWNS[failure_type]
        cooldown_min = random.randint(min_cd, max_cd)
        state["cooldown_until"] = (
            datetime.now() + timedelta(minutes=cooldown_min)
        ).isoformat()
        print(f"  [safety] Cooldown applied: {cooldown_min}min ({failure_type})")

    # Extra cooldown for consecutive failures
    if state["consecutive_failures"] >= 3 and failure_type != "consecutive_fails":
        min_cd, max_cd = COOLDOWNS["consecutive_fails"]
        cooldown_min = random.randint(min_cd, max_cd)
        state["cooldown_until"] = (
            datetime.now() + timedelta(minutes=cooldown_min)
        ).isoformat()
        print(f"  [safety] Extended cooldown: {cooldown_min}min (consecutive failures)")

    _save_state(username, state)


def get_account_status(username: str) -> dict:
    """Get a human-readable status summary for an account."""
    state = _load_state(username)
    days = _days_automated(state)
    _, max_daily, min_gap, max_gap = _get_tier(days)

    return {
        "username": username,
        "days_automated": days,
        "tier": f"Day {days} — max {max_daily}/day, {min_gap}-{max_gap}min gaps",
        "uploads_today": state.get("uploads_today", 0),
        "daily_limit": min(max_daily, ABSOLUTE_MAX_DAILY),
        "total_uploads": state.get("total_uploads", 0),
        "consecutive_failures": state.get("consecutive_failures", 0),
        "cooldown_until": state.get("cooldown_until"),
        "can_upload": can_upload(username),
    }


def print_account_status(username: str) -> None:
    """Print a formatted account safety status."""
    s = get_account_status(username)
    print(f"\n  {'─'*50}")
    print(f"  Safety Status: @{s['username']}")
    print(f"  {'─'*50}")
    print(f"  Automation age: {s['days_automated']} days")
    print(f"  Tier:           {s['tier']}")
    print(f"  Today:          {s['uploads_today']}/{s['daily_limit']} uploads")
    print(f"  All-time:       {s['total_uploads']} uploads")
    can, reason = s["can_upload"]
    status = "READY" if can else f"BLOCKED — {reason}"
    print(f"  Status:         {status}")
    if s["cooldown_until"]:
        print(f"  Cooldown until: {s['cooldown_until']}")
    print(f"  {'─'*50}\n")
