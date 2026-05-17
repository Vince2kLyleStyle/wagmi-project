#!/usr/bin/env python3
"""
Face-based filter: reject videos where the mid-frame has a large
centered face (talking-head vlogs, reactions, selfies).

Keep only videos where:
  - No face detected, OR
  - Face is small (< 8% of frame area)

Samples 3 frames per video (25%, 50%, 75%) and counts the max face
coverage. If any frame has a large face → reject.
"""
import os, subprocess, glob, shutil, cv2
import numpy as np

MOTION_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")
REJECTS_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "rejects", "faces")
os.makedirs(REJECTS_DIR, exist_ok=True)

# Face classifier (ships with opencv)
cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
face_cascade = cv2.CascadeClassifier(cascade_path)

# Reject threshold: if face area > 8% of frame, likely vlog/selfie/reaction.
FACE_AREA_THRESHOLD = 0.08


def extract_frame(path: str, ts: float) -> np.ndarray | None:
    tmp = os.path.join(REJECTS_DIR, "_f.jpg")
    r = subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{ts}", "-i", path,
         "-frames:v", "1", "-vf", "scale=300:-1", "-q:v", "3", tmp],
        capture_output=True, timeout=15
    )
    if r.returncode != 0 or not os.path.exists(tmp):
        return None
    img = cv2.imread(tmp)
    try:
        os.remove(tmp)
    except OSError:
        pass
    return img


def max_face_coverage(path: str, dur: float) -> float:
    coverage = 0.0
    for pct in [0.25, 0.5, 0.75]:
        ts = max(1.0, dur * pct)
        img = extract_frame(path, ts)
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 4, minSize=(30, 30))
        frame_area = img.shape[0] * img.shape[1]
        for (x, y, w, h) in faces:
            face_area = w * h
            cov = face_area / frame_area
            if cov > coverage:
                coverage = cov
    return coverage


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


def main():
    videos = sorted(glob.glob(os.path.join(MOTION_DIR, "*.mp4")))
    print(f"Face-filtering {len(videos)} videos (threshold {FACE_AREA_THRESHOLD:.0%})")

    rejected = 0
    kept = 0
    for i, v in enumerate(videos):
        dur = get_duration(v)
        if dur < 0.5:
            continue
        cov = max_face_coverage(v, dur)
        if cov > FACE_AREA_THRESHOLD:
            name = os.path.basename(v)
            dst = os.path.join(REJECTS_DIR, name)
            try:
                shutil.move(v, dst)
                rejected += 1
            except OSError:
                pass
        else:
            kept += 1
        if (i + 1) % 30 == 0:
            print(f"  {i+1}/{len(videos)} — kept {kept}, rejected {rejected}")

    print(f"\nDone: {kept} kept, {rejected} rejected (face coverage > {FACE_AREA_THRESHOLD:.0%})")


if __name__ == "__main__":
    main()
