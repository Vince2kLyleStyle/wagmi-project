#!/usr/bin/env python3
"""
Auto-QA pass: reject videos that are almost certainly not worth posting.

Reject criteria (all measurable from the file, no ML needed):
  - Duration > 22s (IG rewards short; long clips = lower retention)
  - Avg brightness of mid-frame < 25/255 (broken or pure-black frame)
  - File size < 150 KB (corrupted)
  - Aspect ratio too square (< 1.3:1) — should be 9:16-ish

Everything surviving is dumped to `queue_stats.txt` with its stats so
you (or a human) can spot-check outliers.
"""
import os, subprocess, glob, json, shutil
from PIL import Image

MOTION_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")
REJECTS_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "rejects", "auto_qa")
STATS_FILE = os.path.join(os.path.dirname(__file__), "queue_stats.txt")
os.makedirs(REJECTS_DIR, exist_ok=True)


def probe(path: str) -> dict:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error",
             "-select_streams", "v:0",
             "-show_entries", "stream=width,height,duration",
             "-of", "default=nw=1:nk=1:nokey=1",
             path],
            capture_output=True, text=True, timeout=10
        )
        parts = r.stdout.strip().split("\n")
        if len(parts) < 3:
            return {}
        return {
            "w": int(parts[0]),
            "h": int(parts[1]),
            "dur": float(parts[2]),
            "size": os.path.getsize(path),
        }
    except Exception:
        return {}


def mid_brightness(path: str, dur: float) -> float:
    """Avg brightness of mid-frame (0-255)."""
    ts = max(1.0, min(dur * 0.5, dur - 0.3))
    tmp = os.path.join(REJECTS_DIR, "_b.jpg")
    r = subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{ts}", "-i", path,
         "-frames:v", "1", "-vf", "scale=64:64", "-q:v", "5", tmp],
        capture_output=True, timeout=15
    )
    if r.returncode != 0 or not os.path.exists(tmp):
        return 128.0  # neutral — don't reject on ffmpeg fail
    try:
        im = Image.open(tmp).convert("RGB")
        px = list(im.getdata())
        total = sum(sum(p) for p in px)
        avg = total / (len(px) * 3)
        im.close()
        try:
            os.remove(tmp)
        except OSError:
            pass
        return avg
    except Exception:
        return 128.0


def main():
    videos = sorted(glob.glob(os.path.join(MOTION_DIR, "*.mp4")))
    print(f"Checking {len(videos)} videos")

    stats_lines = []
    rejected = []
    kept = 0

    for i, v in enumerate(videos):
        name = os.path.basename(v)
        info = probe(v)
        if not info:
            rejected.append((name, "ffprobe failed"))
            continue
        dur = info["dur"]
        w, h = info["w"], info["h"]
        size = info["size"]
        aspect = h / w if w > 0 else 0

        reasons = []
        if dur > 22:
            reasons.append(f"long {dur:.1f}s")
        if size < 150_000:
            reasons.append(f"small {size//1024}KB")
        if aspect < 1.3:
            reasons.append(f"aspect {w}x{h}")

        if not reasons:
            bright = mid_brightness(v, dur)
            if bright < 25:
                reasons.append(f"dim {bright:.0f}")
        else:
            bright = -1

        if reasons:
            rejected.append((name, "/".join(reasons)))
        else:
            kept += 1
            stats_lines.append(
                f"{i:03d} {name[:50]:<50} {dur:5.1f}s  "
                f"{w}x{h}  {size//1024:5d}KB  bright={bright:.0f}"
            )

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(videos)} — kept {kept}, rejected {len(rejected)}")

    # Move rejected to rejects folder
    for name, reason in rejected:
        src = os.path.join(MOTION_DIR, name)
        dst = os.path.join(REJECTS_DIR, name)
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
            except OSError:
                pass

    # Write stats for kept videos
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        f.write(f"Auto-QA results: {kept} kept, {len(rejected)} rejected\n")
        f.write("=" * 80 + "\n\n")
        f.write("REJECTED:\n")
        for name, reason in rejected:
            f.write(f"  {name[:60]:<60} {reason}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("KEPT (spot-check candidates, sorted by index):\n")
        for line in stats_lines:
            f.write(line + "\n")

    print(f"\nDone: {kept} kept, {len(rejected)} rejected -> rejects/auto_qa/")
    print(f"See {STATS_FILE}")


if __name__ == "__main__":
    main()
