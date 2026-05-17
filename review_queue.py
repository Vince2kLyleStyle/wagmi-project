"""
Queue Review Tool
==================
Opens each video in the queue, lets you approve or reject it.

  python review_queue.py              # review all videos in motion/
  python review_queue.py --folder review   # review a different folder

Controls:
  Enter or Y  = keep (stays in queue)
  X or N      = reject (deleted)
  S           = skip (decide later)
  Q           = quit review
"""

import glob
import os
import subprocess
import sys

VIDEO_DIR = os.path.join(os.path.dirname(__file__), "tiktok_videos", "motion")


def play_video(path: str):
    """Open video in default Windows player."""
    try:
        os.startfile(path)
    except Exception:
        subprocess.Popen(["cmd", "/c", "start", "", path], shell=True)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Review video queue")
    parser.add_argument("--folder", default=None,
                        help="Subfolder under tiktok_videos/ to review (default: motion)")
    args = parser.parse_args()

    folder = VIDEO_DIR
    if args.folder:
        folder = os.path.join(os.path.dirname(__file__), "tiktok_videos", args.folder)

    videos = sorted(glob.glob(os.path.join(folder, "*.mp4")))
    if not videos:
        print("No videos to review.")
        return

    print()
    print("=" * 50)
    print(f"  Queue Review — {len(videos)} videos")
    print(f"  Folder: {folder}")
    print("=" * 50)
    print()
    print("  Enter/Y = keep    X/N = reject    S = skip    Q = quit")
    print()

    kept = 0
    rejected = 0
    skipped = 0

    for i, path in enumerate(videos):
        name = os.path.basename(path)
        size_mb = os.path.getsize(path) / 1024 / 1024
        print(f"[{i+1}/{len(videos)}] {name} ({size_mb:.1f} MB)")

        play_video(path)

        while True:
            choice = input("  Keep? (Y/n/s/q): ").strip().lower()
            if choice in ("", "y", "yes"):
                kept += 1
                print("  -> kept")
                break
            elif choice in ("x", "n", "no"):
                try:
                    os.remove(path)
                    rejected += 1
                    print("  -> REJECTED (deleted)")
                except OSError as e:
                    print(f"  -> delete failed: {e}")
                break
            elif choice == "s":
                skipped += 1
                print("  -> skipped")
                break
            elif choice == "q":
                print("\nQuitting review.")
                print(f"  Kept: {kept}  Rejected: {rejected}  Skipped: {skipped}")
                return
            else:
                print("  Enter/Y=keep  X/N=reject  S=skip  Q=quit")

        print()

    print("=" * 50)
    print(f"  Review complete!")
    print(f"  Kept: {kept}  Rejected: {rejected}  Skipped: {skipped}")
    remaining = len(glob.glob(os.path.join(folder, "*.mp4")))
    print(f"  Videos remaining in queue: {remaining}")
    print("=" * 50)


if __name__ == "__main__":
    main()
