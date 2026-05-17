#!/usr/bin/env python3
"""Build contact-sheet previews of every video in motion/ for review."""
import os, subprocess, glob, json
from PIL import Image, ImageDraw, ImageFont

MOTION_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")
PREVIEW_DIR = os.path.join(os.path.dirname(__file__), "previews")
THUMBS_DIR = os.path.join(PREVIEW_DIR, "thumbs")
SHEETS_PER_COL = 8
ROWS_PER_SHEET = 12
THUMB_W = 180
THUMB_H = 320
LABEL_H = 30

os.makedirs(THUMBS_DIR, exist_ok=True)


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


def extract_midframe(path: str, out: str) -> bool:
    """Extract a frame near the middle of the video, skipping the 0.4s
    thumbnail prepend. For short videos use 1s, for longer use 50%."""
    dur = get_duration(path)
    if dur < 0.6:
        return False
    ts = max(1.0, min(dur * 0.4, dur - 0.5))
    r = subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{ts}", "-i", path,
         "-frames:v", "1",
         "-vf", f"scale={THUMB_W}:{THUMB_H}:force_original_aspect_ratio=decrease,"
                f"pad={THUMB_W}:{THUMB_H}:(ow-iw)/2:(oh-ih)/2:color=black",
         "-q:v", "4",
         out],
        capture_output=True, timeout=30
    )
    return r.returncode == 0 and os.path.exists(out)


def build_sheet(video_idx_map: list[tuple[int, str, str]],
                sheet_num: int, out_path: str,
                cols: int = SHEETS_PER_COL, rows: int = ROWS_PER_SHEET) -> None:
    """video_idx_map: list of (global_idx, short_name, thumb_path)."""
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
    except Exception:
        font = ImageFont.load_default()

    sheet_w = cols * THUMB_W
    sheet_h = rows * (THUMB_H + LABEL_H)
    sheet = Image.new("RGB", (sheet_w, sheet_h), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)

    for i, (gidx, name, thumb) in enumerate(video_idx_map):
        row = i // cols
        col = i % cols
        x = col * THUMB_W
        y = row * (THUMB_H + LABEL_H)
        if thumb and os.path.exists(thumb):
            try:
                im = Image.open(thumb)
                sheet.paste(im, (x, y))
                im.close()
            except Exception:
                pass
        # Label: global index
        label = f"#{gidx:03d}"
        draw.rectangle([x, y + THUMB_H, x + THUMB_W, y + THUMB_H + LABEL_H],
                       fill=(30, 30, 30))
        draw.text((x + 4, y + THUMB_H + 6), label, fill=(220, 220, 220), font=font)

    sheet.save(out_path, "JPEG", quality=80)


def main():
    videos = sorted(glob.glob(os.path.join(MOTION_DIR, "*.mp4")))
    if not videos:
        print("no videos")
        return
    print(f"{len(videos)} videos -> building thumbnails...")

    # Also write an index file mapping global idx -> filename
    index_file = os.path.join(PREVIEW_DIR, "index.json")
    index = {}

    video_thumbs = []
    for gidx, v in enumerate(videos):
        name = os.path.basename(v)
        thumb_path = os.path.join(THUMBS_DIR, f"{gidx:03d}_{name[:30]}.jpg")
        if not os.path.exists(thumb_path):
            extract_midframe(v, thumb_path)
        index[str(gidx)] = name
        video_thumbs.append((gidx, name, thumb_path))
        if (gidx + 1) % 50 == 0:
            print(f"  {gidx+1}/{len(videos)} thumbnails extracted")

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    per_sheet = SHEETS_PER_COL * ROWS_PER_SHEET
    num_sheets = (len(videos) + per_sheet - 1) // per_sheet
    print(f"\nBuilding {num_sheets} contact sheets ({per_sheet} per sheet)...")

    for s in range(num_sheets):
        chunk = video_thumbs[s * per_sheet:(s + 1) * per_sheet]
        rows = (len(chunk) + SHEETS_PER_COL - 1) // SHEETS_PER_COL
        out = os.path.join(PREVIEW_DIR, f"sheet_{s:02d}.jpg")
        build_sheet(chunk, s, out, cols=SHEETS_PER_COL, rows=max(rows, 1))
        print(f"  sheet_{s:02d}.jpg -> {len(chunk)} videos")


if __name__ == "__main__":
    main()
