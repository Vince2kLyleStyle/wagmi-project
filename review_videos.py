#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║          REVIEW — Quick Video Quality Check                   ║
║          Watch each video, Y to keep, N to delete             ║
╚═══════════════════════════════════════════════════════════════╝

Usage:
    python review_videos.py                          # review motion folder
    python review_videos.py --dir tiktok_videos/memes
"""

import argparse
import os
import subprocess
import sys

import config


def main():
    parser = argparse.ArgumentParser(description="Review videos — keep or delete")
    parser.add_argument(
        "--dir", "-d", default=None,
        help="Directory to review (default: config.VIDEO_DIR)"
    )
    args = parser.parse_args()

    vid_dir = args.dir or config.VIDEO_DIR

    if not os.path.isdir(vid_dir):
        print(f"  Directory not found: {vid_dir}")
        sys.exit(1)

    vids = sorted([f for f in os.listdir(vid_dir) if f.lower().endswith(".mp4")])

    print(r"""
    ╔═══════════════════════════════════════════════╗
    ║     REVIEW — Video Quality Check              ║
    ║     Y = keep   N = delete   S = skip          ║
    ╚═══════════════════════════════════════════════╝
    """)
    print(f"  Folder:  {vid_dir}")
    print(f"  Videos:  {len(vids)}")
    print()

    if not vids:
        print("  No videos to review!")
        return

    kept = 0
    trashed = 0
    skipped = 0

    for i, v in enumerate(vids, 1):
        path = os.path.join(vid_dir, v)
        short_name = v[:50] + "..." if len(v) > 53 else v

        print(f"  [{i}/{len(vids)}] {short_name}")

        # Open video in default player
        try:
            if sys.platform == "win32":
                subprocess.Popen(["start", "", path], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            print(f"    Could not open video: {e}")

        # Get user input
        while True:
            choice = input("    (Y)keep  (N)delete  (S)skip  (Q)quit: ").strip().lower()
            if choice in ("y", "n", "s", "q", ""):
                break
            print("    Invalid — press Y, N, S, or Q")

        if choice == "n":
            os.remove(path)
            trashed += 1
            print("    ❌ DELETED\n")
        elif choice == "y" or choice == "":
            kept += 1
            print("    ✅ KEPT\n")
        elif choice == "q":
            print("\n  Quitting review.\n")
            break
        else:
            skipped += 1
            print("    ⏭  SKIPPED\n")

    remaining = len([f for f in os.listdir(vid_dir) if f.lower().endswith(".mp4")])

    print(f"  {'═' * 40}")
    print(f"  DONE!")
    print(f"  Kept:      {kept}")
    print(f"  Deleted:   {trashed}")
    print(f"  Skipped:   {skipped}")
    print(f"  Remaining: {remaining} videos in folder")
    print(f"  {'═' * 40}\n")


if __name__ == "__main__":
    main()
