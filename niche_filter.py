#!/usr/bin/env python3
"""
Niche filter using YOLO object detection.

Vince's niche: memes + funny dog/animal videos.
Reject: ads, fashion, personal content, lifestyle, talking-heads,
reactions, products, cars, indoor scenes with people, etc.

Per video: sample 3 frames (25%, 50%, 75%), run YOLO, take max-confidence
classifications. Decision:
  KEEP if any frame contains a confident ANIMAL detection
  KEEP if frames consistently have no detected objects (likely text-meme)
  REJECT if any frame has a confident HUMAN/PRODUCT/VEHICLE detection
"""
import os, subprocess, glob, shutil, tempfile, sys
from ultralytics import YOLO

MOTION_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")
KEEP_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion_niche")
REJECTS_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "rejects", "niche_filter")
os.makedirs(KEEP_DIR, exist_ok=True)
os.makedirs(REJECTS_DIR, exist_ok=True)

# COCO classes
ANIMAL_CLASSES = {"dog", "cat", "bird", "horse", "sheep", "cow", "elephant",
                  "bear", "zebra", "giraffe"}
REJECT_CLASSES = {"person", "bicycle", "car", "motorcycle", "airplane", "bus",
                  "train", "truck", "boat", "traffic light", "bottle",
                  "wine glass", "cup", "fork", "knife", "spoon", "bowl",
                  "banana", "apple", "sandwich", "orange", "broccoli",
                  "carrot", "hot dog", "pizza", "donut", "cake", "chair",
                  "couch", "potted plant", "bed", "dining table", "toilet",
                  "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
                  "microwave", "oven", "toaster", "sink", "refrigerator",
                  "book", "clock", "vase", "scissors", "teddy bear",
                  "hair drier", "toothbrush", "handbag", "tie", "suitcase"}
# "person" gets special treatment: small person OK (in meme), dominant person REJECT
PERSON_REJECT_AREA = 0.22  # if any person takes > 22% of frame, reject

CONF_THRESHOLD = 0.35


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
         "-frames:v", "1", "-vf", "scale=480:-1", "-q:v", "3", out],
        capture_output=True, timeout=20
    )
    return r.returncode == 0 and os.path.exists(out)


def classify(model: YOLO, path: str, dur: float) -> tuple[str, str]:
    """Return (decision, reason). decision: 'keep' | 'reject'."""
    tmp_dir = tempfile.mkdtemp(prefix="niche_")
    try:
        frames = []
        for pct in [0.25, 0.5, 0.75]:
            ts = max(1.0, dur * pct)
            f = os.path.join(tmp_dir, f"{pct}.jpg")
            if extract_frame(path, ts, f):
                frames.append(f)
        if not frames:
            return ("reject", "no frames extracted")

        # Single YOLO inference on all frames (batched)
        results = model(frames, verbose=False, conf=CONF_THRESHOLD)
        animals_found = []
        rejects_found = []
        person_max_area = 0.0
        total_detections = 0

        for r in results:
            frame_area = r.orig_shape[0] * r.orig_shape[1]
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls = model.names[cls_id]
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                area_frac = ((x2 - x1) * (y2 - y1)) / frame_area
                total_detections += 1
                if cls in ANIMAL_CLASSES:
                    animals_found.append((cls, conf, area_frac))
                elif cls == "person":
                    if area_frac > person_max_area:
                        person_max_area = area_frac
                elif cls in REJECT_CLASSES:
                    rejects_found.append((cls, conf, area_frac))

        # Decision logic
        if animals_found:
            best = max(animals_found, key=lambda x: x[2])  # biggest animal
            # Animal must not be tiny (background)
            if best[2] > 0.04:
                return ("keep", f"animal: {best[0]} {best[2]*100:.0f}%")
            # otherwise fall through — tiny animal not enough

        if person_max_area > PERSON_REJECT_AREA:
            return ("reject", f"person {person_max_area*100:.0f}%")

        if rejects_found:
            biggest = max(rejects_found, key=lambda x: x[2])
            if biggest[2] > 0.08:
                return ("reject", f"{biggest[0]} {biggest[2]*100:.0f}%")

        # No dominant objects at all → could be a text-only meme or abstract
        if total_detections == 0:
            return ("keep", "no objects (possible meme)")

        # Has small non-dominant objects — ambiguous, lean reject
        return ("reject", f"{total_detections} objects, none dominant")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main():
    videos = sorted(glob.glob(os.path.join(MOTION_DIR, "*.mp4")))
    print(f"Niche-filtering {len(videos)} videos with YOLO...")
    # Use the small, fast model
    model = YOLO("yolov8n.pt")  # auto-downloads on first run
    print("Model loaded")

    keeps = []
    rejects = []
    for i, v in enumerate(videos):
        dur = get_duration(v)
        if dur < 0.5:
            rejects.append((v, "too short"))
            continue
        decision, reason = classify(model, v, dur)
        name = os.path.basename(v)
        if decision == "keep":
            keeps.append((v, reason))
        else:
            rejects.append((v, reason))

        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(videos)} - keep {len(keeps)}, reject {len(rejects)}")

    # Move rejects
    for v, reason in rejects:
        dst = os.path.join(REJECTS_DIR, os.path.basename(v))
        try:
            shutil.move(v, dst)
        except OSError:
            pass

    # Write summary
    with open(os.path.join(os.path.dirname(__file__), "niche_filter_results.txt"),
              "w", encoding="utf-8") as f:
        f.write(f"KEEP: {len(keeps)}\n")
        f.write(f"REJECT: {len(rejects)}\n\n")
        f.write("== KEPT ==\n")
        for v, r in keeps:
            f.write(f"  {os.path.basename(v)}: {r}\n")
        f.write("\n== REJECTED ==\n")
        for v, r in rejects:
            f.write(f"  {os.path.basename(v)}: {r}\n")

    print(f"\nDone: {len(keeps)} kept, {len(rejects)} rejected")
    print("Details: niche_filter_results.txt")


if __name__ == "__main__":
    main()
