#!/usr/bin/env python3
"""Build DETAILED multi-frame previews per video to judge content quality."""
import os, subprocess, glob, sys, json
from PIL import Image, ImageDraw, ImageFont

MOTION_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")
PREVIEW_DIR = os.path.join(os.path.dirname(__file__), "previews")
DETAILED_DIR = os.path.join(PREVIEW_DIR, "detailed")
os.makedirs(DETAILED_DIR, exist_ok=True)

THUMB_W, THUMB_H = 270, 480  # bigger per-frame
FRAMES_PER_VIDEO = 4          # 0.2, 0.4, 0.6, 0.8 of duration
VIDEOS_PER_SHEET = 12         # 4 rows of 3 (each video shows 4 frames side-by-side)


def get_duration(path: str) -> float:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path],
            capture_output=True, text=True, timeout=10
        )
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def extract_frame(path: str, ts: float, out: str) -> bool:
    r = subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{ts}", "-i", path,
         "-frames:v", "1",
         "-vf", f"scale={THUMB_W}:{THUMB_H}:force_original_aspect_ratio=decrease,"
                f"pad={THUMB_W}:{THUMB_H}:(ow-iw)/2:(oh-ih)/2:color=black",
         "-q:v", "4", out],
        capture_output=True, timeout=30
    )
    return r.returncode == 0 and os.path.exists(out)


def build_video_strip(path: str, out: str) -> bool:
    """4 frames side-by-side for a single video."""
    dur = get_duration(path)
    if dur < 1.0:
        return False
    # Sample after the 0.4s prepend
    start = max(0.5, 0.5)
    end = dur - 1.5 if dur > 2 else dur - 0.1
    points = [start + (end - start) * f for f in [0.0, 0.33, 0.66, 1.0]]

    strip = Image.new("RGB", (THUMB_W * FRAMES_PER_VIDEO, THUMB_H), (0, 0, 0))
    tmp_dir = os.path.join(DETAILED_DIR, "_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    for i, ts in enumerate(points):
        f = os.path.join(tmp_dir, f"f{i}.jpg")
        if extract_frame(path, ts, f):
            im = Image.open(f)
            strip.paste(im, (i * THUMB_W, 0))
            im.close()
            try:
                os.remove(f)
            except OSError:
                pass
    strip.save(out, "JPEG", quality=82)
    return True


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else start + VIDEOS_PER_SHEET

    videos = sorted(glob.glob(os.path.join(MOTION_DIR, "*.mp4")))
    videos = videos[start:end]
    if not videos:
        print("no videos")
        return

    print(f"Building detailed sheets for #{start:03d}-#{start+len(videos)-1:03d}")

    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()

    # One big sheet: each video is one row, 4 frames wide
    row_h = THUMB_H + 30  # room for label
    sheet_h = len(videos) * row_h
    sheet_w = THUMB_W * FRAMES_PER_VIDEO
    sheet = Image.new("RGB", (sheet_w, sheet_h), (15, 15, 15))
    draw = ImageDraw.Draw(sheet)

    tmp_dir = os.path.join(DETAILED_DIR, "_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    for i, v in enumerate(videos):
        gidx = start + i
        name = os.path.basename(v)
        short = name[:50]
        y0 = i * row_h

        # Extract 4 frames directly into the sheet
        dur = get_duration(v)
        if dur >= 1.0:
            frame_points = [0.5, dur * 0.35, dur * 0.65, max(dur - 1.5, dur - 0.1)]
            for j, ts in enumerate(frame_points):
                tmp_f = os.path.join(tmp_dir, f"f{j}.jpg")
                if extract_frame(v, ts, tmp_f):
                    try:
                        im = Image.open(tmp_f)
                        sheet.paste(im, (j * THUMB_W, y0))
                        im.close()
                    except Exception:
                        pass
        # Label bar at bottom of the row
        draw.rectangle([0, y0 + THUMB_H, sheet_w, y0 + THUMB_H + 30], fill=(25, 25, 25))
        draw.text((6, y0 + THUMB_H + 6),
                  f"#{gidx:03d}  {short}  ({dur:.1f}s)",
                  fill=(220, 220, 220), font=font)

    out = os.path.join(DETAILED_DIR, f"detail_{start:03d}_{start+len(videos)-1:03d}.jpg")
    sheet.save(out, "JPEG", quality=80)
    print(f"  -> {out}")


if __name__ == "__main__":
    main()
