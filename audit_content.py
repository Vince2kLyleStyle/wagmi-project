#!/usr/bin/env python3
"""Audit the banked nest-egg: map each saved video back to the search keyword
that pulled it (via scraped_urls.txt) and classify meme vs 'tough' (off-brand
lifestyle) content. Read-only — reports counts + writes a cull list of the
tough videos so they can be reviewed/removed. Nothing is deleted here."""
import os
import re
import glob
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
URLS = os.path.join(BASE, "scraped_urls.txt")
FOLDERS = ["hellokitty", "popgak", "catsother"]

# keyword -> bucket classification (substring match, lowercased)
MEME = ("meme", "funny", "relatable", "mood", "pov", "be like", "me when",
        "reaction", "cursed", "shitpost", "slander", "derp", "rage",
        "crying", "capcut", "trend", "comic", "joke", "humor", "viral",
        "silly", "vibing", " jam", "spinning", "popcat", "pop cat", "gak",
        "maxwell", "oiia", "banana", "chipi", "nyan", "bingus", "michi",
        "when")
TOUGH = ("haul", "grwm", "skincare", "perfume", "makeup", "nail", "ootd",
         "fit check", "outfit", "room", "decor", "bedroom", "apartment",
         "cafe", "boba", "bakery", "bento", "cookie", "lunch", "starbucks",
         "mcdonald", "drink", "unbox", "shopping", "store", "temu", "shein",
         "amazon", "squishmallow", "build a bear", "keychain", "phone case",
         "crochet", "amigurumi", "painting", "perler", "clay", "custom",
         "tattoo", "journal", "stationary", "sticker", "wallpaper",
         "collection", "coquette", "cake", "birthday", "drawing", "cosplay",
         "transformation", "jeep", "blind box", "diy", "setup", "keyboard",
         "routine", "jewelry", " bag", "purse", "accessor", "croc", "shoe",
         "halloween", "christmas", "valentine", "asmr", "aesthetic",
         "island", "desk", "plush", "character", " car", " art", " pfp",
         " pc")


def bucket(kw):
    k = kw.lower()
    if any(t in k for t in MEME):
        return "MEME"
    if any(t in k for t in TOUGH):
        return "TOUGH"
    return "NEUTRAL"


def load_map():
    """video_id -> keyword from scraped_urls.txt"""
    vid2kw = {}
    with open(URLS, encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 6:
                continue
            kw = parts[1]
            m = re.search(r"/video/(\d+)", parts[-1])
            if m:
                vid2kw[m.group(1)] = kw
    return vid2kw


def main():
    vid2kw = load_map()
    print(f"scraped_urls.txt: {len(vid2kw)} video->keyword mappings\n")
    cull = []
    for folder in FOLDERS:
        files = glob.glob(os.path.join(BASE, "tiktok_videos", folder, "*.mp4"))
        buckets = Counter()
        kw_tough = Counter()
        unmapped = 0
        for fp in files:
            name = os.path.basename(fp)
            m = re.search(r"(\d{15,})\.mp4$", name)
            vid = m.group(1) if m else None
            kw = vid2kw.get(vid) if vid else None
            if not kw:
                unmapped += 1
                buckets["UNMAPPED"] += 1
                continue
            b = bucket(kw)
            buckets[b] += 1
            if b == "TOUGH":
                kw_tough[kw] += 1
                cull.append(fp)
        total = len(files)
        print(f"=== {folder}: {total} videos ===")
        for b in ("MEME", "NEUTRAL", "TOUGH", "UNMAPPED"):
            if buckets[b]:
                pct = 100 * buckets[b] / total if total else 0
                print(f"  {b:8} {buckets[b]:4}  ({pct:.0f}%)")
        if kw_tough:
            print("  top TOUGH keywords:",
                  ", ".join(f"{k}({c})" for k, c in kw_tough.most_common(8)))
        print()
    # write cull list
    out = os.path.join(BASE, "tough_content_cull_list.txt")
    with open(out, "w", encoding="utf-8") as f:
        for fp in cull:
            f.write(fp + "\n")
    print(f"TOUGH cull list: {len(cull)} videos -> {os.path.basename(out)}")
    print("(review before deleting; nothing removed by this script)")


if __name__ == "__main__":
    main()
