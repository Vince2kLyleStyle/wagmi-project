#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║            NSFW FILTER — Video Content Moderator              ║
║   Scans videos for NSFW content and quarantines flagged ones  ║
╚═══════════════════════════════════════════════════════════════╝

Extracts frames from each video, runs them through NudeNet classifier,
and moves anything flagged to a quarantine folder.

Usage:
    python nsfw_filter.py                         # scan default VIDEO_DIR
    python nsfw_filter.py --dir tiktok_videos/memes
    python nsfw_filter.py --threshold 0.6         # stricter (default 0.45)
    python nsfw_filter.py --dry-run               # preview without moving
    python nsfw_filter.py --delete                # delete instead of quarantine

Requires: pip install nudenet opencv-python-headless
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

# ─── NSFW Labels that should trigger quarantine ──────────────────────
# NudeNet v3 detection labels — these are the problematic ones.
# We flag on exposed body parts that indicate porn/nudity.
FLAGGED_LABELS = {
    "FEMALE_BREAST_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "ANUS_EXPOSED",
    "FEMALE_BREAST_COVERED",   # bikini/lingerie content — still not safe for IG repost
    "BELLY_EXPOSED",           # alone not flagged, but counted at lower weight
}

# Labels that are always fine
SAFE_LABELS = {
    "FACE_FEMALE",
    "FACE_MALE",
    "FEET_EXPOSED",
    "ARMPITS_EXPOSED",
    "BELLY_COVERED",
}

# Higher-severity labels — if ANY of these appear above threshold, instant flag
INSTANT_FLAG_LABELS = {
    "FEMALE_BREAST_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "ANUS_EXPOSED",
}

DEFAULT_THRESHOLD = 0.45
FRAMES_TO_CHECK = 8  # sample this many frames per video


def extract_frames(video_path: str, num_frames: int = FRAMES_TO_CHECK) -> list[str]:
    """Extract evenly-spaced frames from a video using ffmpeg."""
    frames = []
    tmp_dir = tempfile.mkdtemp(prefix="nsfw_filter_")

    try:
        # Get duration
        probe = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1",
             video_path],
            capture_output=True, text=True, timeout=15,
        )
        duration = float(probe.stdout.strip())
        if duration < 0.5:
            return []

        # Calculate frame timestamps (skip first/last 5%)
        start = duration * 0.05
        end = duration * 0.95
        interval = (end - start) / max(num_frames - 1, 1)

        for i in range(num_frames):
            ts = start + (i * interval)
            frame_path = os.path.join(tmp_dir, f"frame_{i:03d}.jpg")
            subprocess.run(
                ["ffmpeg", "-ss", str(ts),
                 "-i", video_path,
                 "-vframes", "1",
                 "-q:v", "2",
                 "-y", frame_path],
                capture_output=True, timeout=15,
            )
            if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
                frames.append(frame_path)

    except Exception as e:
        print(f"  [!!] Frame extraction error: {e}")

    return frames


def check_frames_nsfw(detector, frames: list[str], threshold: float) -> dict:
    """
    Run NudeNet on extracted frames.
    Returns dict with is_nsfw, max_score, flagged_labels, details.
    """
    result = {
        "is_nsfw": False,
        "max_score": 0.0,
        "flagged_labels": set(),
        "instant_flag": False,
        "details": [],
    }

    for frame_path in frames:
        try:
            detections = detector.detect(frame_path)
        except Exception:
            continue

        for det in detections:
            label = det["class"]
            score = det["score"]

            if label in SAFE_LABELS:
                continue

            if label in FLAGGED_LABELS and score >= threshold:
                result["flagged_labels"].add(label)
                result["max_score"] = max(result["max_score"], score)
                result["details"].append(f"{label}={score:.2f}")

                if label in INSTANT_FLAG_LABELS:
                    result["instant_flag"] = True
                    result["is_nsfw"] = True

    # Flag if 2+ different problematic labels detected, or any instant-flag
    if result["instant_flag"] or len(result["flagged_labels"]) >= 2:
        result["is_nsfw"] = True

    return result


def cleanup_frames(frames: list[str]):
    """Remove extracted frame files and their temp directory."""
    for f in frames:
        try:
            os.remove(f)
        except OSError:
            pass
    # Remove temp dirs
    dirs_seen = set()
    for f in frames:
        d = os.path.dirname(f)
        if d not in dirs_seen:
            dirs_seen.add(d)
            try:
                os.rmdir(d)
            except OSError:
                pass


def scan_directory(video_dir: str, threshold: float = DEFAULT_THRESHOLD,
                   dry_run: bool = False, delete_flagged: bool = False) -> tuple[int, int, int]:
    """
    Scan all .mp4 files in a directory for NSFW content.
    Returns (total, clean, flagged) counts.
    """
    try:
        from nudenet import NudeDetector
    except ImportError:
        print("  [!!] nudenet not installed. Run: pip install nudenet")
        sys.exit(1)

    print("  Loading NudeNet detector...")
    detector = NudeDetector()

    # Find all videos
    videos = sorted([
        os.path.join(video_dir, f)
        for f in os.listdir(video_dir)
        if f.lower().endswith(".mp4")
    ])

    if not videos:
        print(f"  No .mp4 files found in {video_dir}")
        return 0, 0, 0

    # Quarantine folder
    quarantine_dir = os.path.join(video_dir, "_quarantine_nsfw")
    if not dry_run and not delete_flagged:
        os.makedirs(quarantine_dir, exist_ok=True)

    total = len(videos)
    clean = 0
    flagged = 0

    print(f"  Scanning {total} videos (threshold={threshold})...\n")

    for idx, vpath in enumerate(videos, 1):
        filename = os.path.basename(vpath)
        short_name = filename[:45] + "..." if len(filename) > 48 else filename

        print(f"  [{idx}/{total}] {short_name}", end="", flush=True)

        # Extract frames
        frames = extract_frames(vpath)
        if not frames:
            print(f" — skipped (no frames)")
            clean += 1
            continue

        # Check for NSFW
        result = check_frames_nsfw(detector, frames, threshold)
        cleanup_frames(frames)

        if result["is_nsfw"]:
            flagged += 1
            labels = ", ".join(result["flagged_labels"])
            print(f" — FLAGGED [{result['max_score']:.0%}] {labels}")

            if not dry_run:
                if delete_flagged:
                    os.remove(vpath)
                    print(f"           DELETED")
                else:
                    dest = os.path.join(quarantine_dir, filename)
                    shutil.move(vpath, dest)
                    print(f"           → quarantine")
        else:
            clean += 1
            print(f" — clean")

    return total, clean, flagged


def main():
    parser = argparse.ArgumentParser(description="NSFW Video Filter")
    parser.add_argument(
        "--dir", "-d", default=None,
        help="Directory to scan (default: config.VIDEO_DIR)"
    )
    parser.add_argument(
        "--threshold", "-t", type=float, default=DEFAULT_THRESHOLD,
        help=f"Detection confidence threshold (default: {DEFAULT_THRESHOLD})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be flagged without moving/deleting"
    )
    parser.add_argument(
        "--delete", action="store_true",
        help="Delete flagged videos instead of quarantining"
    )
    parser.add_argument(
        "--all-niches", action="store_true",
        help="Scan all niche folders under tiktok_videos/"
    )
    args = parser.parse_args()

    print(r"""
    ╔═══════════════════════════════════════════════╗
    ║       NSFW FILTER — Content Moderator         ║
    ║       Quarantine inappropriate videos          ║
    ╚═══════════════════════════════════════════════╝
    """)

    if args.all_niches:
        import scraper_config as cfg
        base = cfg.DOWNLOAD_DIR
        niches = [d for d in os.listdir(base)
                  if os.path.isdir(os.path.join(base, d)) and not d.startswith("_")]

        grand_total = grand_clean = grand_flagged = 0
        for niche in sorted(niches):
            niche_dir = os.path.join(base, niche)
            print(f"\n{'═' * 54}")
            print(f"  NICHE: {niche}")
            print(f"{'═' * 54}")
            t, c, f = scan_directory(niche_dir, args.threshold, args.dry_run, args.delete)
            grand_total += t
            grand_clean += c
            grand_flagged += f

        print(f"\n{'═' * 54}")
        print(f"  ALL NICHES COMPLETE")
        print(f"  Total: {grand_total} | Clean: {grand_clean} | Flagged: {grand_flagged}")
        print(f"{'═' * 54}\n")
    else:
        if args.dir:
            video_dir = args.dir
        else:
            import config
            video_dir = config.VIDEO_DIR

        if not os.path.isdir(video_dir):
            print(f"  [!!] Directory not found: {video_dir}")
            sys.exit(1)

        print(f"  Directory:  {video_dir}")
        print(f"  Threshold:  {args.threshold}")
        print(f"  Mode:       {'DRY RUN' if args.dry_run else 'DELETE' if args.delete else 'QUARANTINE'}")
        print()

        total, clean, flagged = scan_directory(
            video_dir, args.threshold, args.dry_run, args.delete
        )

        print(f"\n{'═' * 54}")
        print(f"  DONE!")
        print(f"  Total: {total} | Clean: {clean} | Flagged: {flagged}")
        if flagged and not args.dry_run and not args.delete:
            quarantine = os.path.join(video_dir, "_quarantine_nsfw")
            print(f"  Quarantined in: {quarantine}")
        print(f"{'═' * 54}\n")


if __name__ == "__main__":
    main()
