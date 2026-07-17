"""
Talking-head filter — topcats online.

Nunu's rule (2026-07-16): do NOT post videos of other people talking into the
camera. The page is cats, not human commentary. This scans the banked videos and
quarantines any clip dominated by a human face addressing the camera.

Method (fully local, zero API cost):
  * sample N frames evenly across the clip with ffmpeg
  * run OpenCV's frontal-face Haar cascade on each frame
  * a clip is a TALKING HEAD if a LARGE human face (>= FACE_AREA_PCT of the
    frame) appears in at least FRAME_FRAC of the sampled frames

A big, persistent, front-facing head is the signature of talk-to-camera
content. A human who merely appears in frame (holding a cat, hand in shot)
produces small or intermittent faces and is left alone.

Quarantine MOVES files to tiktok_videos/_quarantine_talking/<tier>/ — nothing
is deleted, so any misclassification is reversible.

Usage:
  python filter_talking_heads.py                 # report only (safe, default)
  python filter_talking_heads.py --apply         # move flagged clips out
  python filter_talking_heads.py --tier popgak   # limit to one tier
  python filter_talking_heads.py --restore       # undo a quarantine
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys

import cv2

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiktok_videos")
TIERS = ["hellokitty", "popgak", "catsother"]
QUARANTINE = os.path.join(BASE, "_quarantine_talking")

# ─── Tuning ─────────────────────────────────────────────────────────
SAMPLE_FRAMES = 8      # frames sampled per clip
FACE_AREA_PCT = 4.0    # a face this % of the frame or larger counts as "large"
FRAME_FRAC    = 0.35   # large face in >= this fraction of frames -> talking head

_cascade = cv2.CascadeClassifier(
    os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
)
_cat_cascade = cv2.CascadeClassifier(
    os.path.join(cv2.data.haarcascades, "haarcascade_frontalcatface.xml")
)


def video_duration(path: str) -> float:
    """Seconds, or 0.0 if ffprobe can't read it."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30,
        )
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def sample_frames(path: str, n: int = SAMPLE_FRAMES):
    """Yield n frames spread across the clip, using OpenCV's own seeking."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return
    try:
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total <= 0:
            return
        # Skip the first/last 10% — intros and outros are unrepresentative.
        lo, hi = int(total * 0.10), int(total * 0.90)
        if hi <= lo:
            lo, hi = 0, max(total - 1, 0)
        step = max((hi - lo) // max(n - 1, 1), 1)
        for i in range(n):
            idx = min(lo + i * step, total - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if ok and frame is not None:
                yield frame
    finally:
        cap.release()


def analyze(path: str) -> dict:
    """Return talking-head metrics for one clip."""
    frames = 0
    large_face_frames = 0
    biggest_pct = 0.0
    cat_face_frames = 0

    for frame in sample_frames(path):
        frames += 1
        h, w = frame.shape[:2]
        area = float(h * w)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = _cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6,
                                          minSize=(40, 40))
        cats = _cat_cascade.detectMultiScale(gray, scaleFactor=1.1,
                                             minNeighbors=6, minSize=(40, 40))
        if len(cats):
            cat_face_frames += 1

        best = 0.0
        for (_x, _y, fw, fh) in faces:
            pct = (fw * fh) / area * 100.0
            best = max(best, pct)
        biggest_pct = max(biggest_pct, best)
        if best >= FACE_AREA_PCT:
            large_face_frames += 1

    frac = (large_face_frames / frames) if frames else 0.0
    return {
        "frames": frames,
        "large_face_frames": large_face_frames,
        "frac": frac,
        "biggest_pct": biggest_pct,
        "cat_face_frames": cat_face_frames,
        "talking_head": frames > 0 and frac >= FRAME_FRAC,
    }


def iter_videos(tiers):
    for tier in tiers:
        for path in sorted(glob.glob(os.path.join(BASE, tier, "*.mp4"))):
            yield tier, path


def restore():
    moved = 0
    for tier in TIERS:
        src_dir = os.path.join(QUARANTINE, tier)
        if not os.path.isdir(src_dir):
            continue
        for path in glob.glob(os.path.join(src_dir, "*.mp4")):
            dest = os.path.join(BASE, tier, os.path.basename(path))
            shutil.move(path, dest)
            moved += 1
    print(f"[restore] moved {moved} clips back into the active pool")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="move flagged clips to quarantine (default: report only)")
    ap.add_argument("--tier", choices=TIERS, help="limit to one tier")
    ap.add_argument("--restore", action="store_true",
                    help="move quarantined clips back and exit")
    ap.add_argument("--limit", type=int, default=0, help="scan at most N clips")
    args = ap.parse_args()

    if args.restore:
        restore()
        return

    tiers = [args.tier] if args.tier else TIERS
    videos = list(iter_videos(tiers))
    if args.limit:
        videos = videos[: args.limit]

    if not videos:
        print("[!] no videos found")
        return

    print(f"[*] scanning {len(videos)} clips "
          f"(face >= {FACE_AREA_PCT}% of frame in >= {FRAME_FRAC:.0%} of frames)")
    print(f"[*] mode: {'APPLY (will move files)' if args.apply else 'REPORT ONLY'}\n")

    flagged, clean, unreadable = [], [], []
    for i, (tier, path) in enumerate(videos, 1):
        m = analyze(path)
        name = os.path.basename(path)
        if m["frames"] == 0:
            unreadable.append((tier, path))
            print(f"  [{i}/{len(videos)}] ?? UNREADABLE {tier}/{name}")
            continue
        if m["talking_head"]:
            flagged.append((tier, path, m))
            print(f"  [{i}/{len(videos)}] XX TALKING HEAD {tier}/{name}  "
                  f"face in {m['frac']:.0%} of frames, biggest {m['biggest_pct']:.1f}%")
        else:
            clean.append((tier, path, m))

    print(f"\n{'='*58}")
    print(f"  clean      : {len(clean)}")
    print(f"  talking    : {len(flagged)}")
    print(f"  unreadable : {len(unreadable)}")
    print(f"{'='*58}")

    if not args.apply:
        print("\n[i] report only — nothing moved. Re-run with --apply to quarantine.")
        return

    for tier, path, _m in flagged:
        dest_dir = os.path.join(QUARANTINE, tier)
        os.makedirs(dest_dir, exist_ok=True)
        shutil.move(path, os.path.join(dest_dir, os.path.basename(path)))
    print(f"\n[+] quarantined {len(flagged)} clips -> {QUARANTINE}")
    print("[i] reversible: python filter_talking_heads.py --restore")


if __name__ == "__main__":
    main()
