"""
Video Processor — Watermark + Thumbnail First Frame
====================================================
Processes videos before posting:
  1. Creates a "MOTION 🥀" watermark PNG (cached at watermark.png)
  2. Prepends thumbnail.jpg as a 0.5s freeze frame
  3. Overlays the watermark on all frames

Uses Pillow for watermark creation (emoji support via Segoe UI Emoji on Win11)
and ffmpeg for video compositing.
"""

import os
import subprocess
import shutil
import tempfile

# ─── Paths ────────────────────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
WATERMARK_PATH = os.path.join(PROJECT_DIR, "watermark.png")
THUMBNAIL_PATH = os.path.join(PROJECT_DIR, "thumbnail.jpg")


EMOJI_POOL = [
    "🔥", "💯", "😂", "🤯", "👀", "💀", "✨", "⚡", "🎯",
    "😤", "🙌", "💪", "😍", "🥶", "📈", "🎬",
    "💎", "🚀", "😈", "🧠", "❤️", "👑", "🫡",
]


def _pick_emojis(n: int = 3) -> str:
    """Pick n random emojis from the pool (may repeat)."""
    import random
    return "".join(random.choices(EMOJI_POOL, k=n))


def _create_emoji_overlay_png(output_path: str, text: str | None = None,
                              fontsize: int = 44, opacity: float = 0.95) -> bool:
    """
    Create a transparent PNG with "MOTION" text + 2 random emojis.

    Rendered with Segoe UI Emoji so emojis have full color. Sized like
    a caption sticker — visible but not overwhelming. If `text` is None,
    picks 2 random emojis and prefixes them with "MOTION ".
    Returns True on success.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[!!] Pillow not installed — pip install Pillow")
        return False

    if text is None:
        text = f"MOTION {_pick_emojis(2)}"

    font = None
    font_names = [
        "C:/Windows/Fonts/seguiemj.ttf",   # Segoe UI Emoji (Win11)
        "C:/Windows/Fonts/segoeui.ttf",     # Segoe UI (fallback, no color)
        "C:/Windows/Fonts/arial.ttf",
    ]
    for fpath in font_names:
        if os.path.exists(fpath):
            try:
                # embedded_color keeps the COLRv1/CBDT color tables so
                # emojis render in full color (Pillow ≥9.4 supports this).
                font = ImageFont.truetype(fpath, fontsize, encoding="unic")
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()

    # Measure
    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)
    try:
        bbox = draw.textbbox((0, 0), text, font=font, embedded_color=True)
    except TypeError:
        bbox = draw.textbbox((0, 0), text, font=font)
    pad = 20
    text_w = max(bbox[2] - bbox[0] + pad * 2, 200)
    text_h = max(bbox[3] - bbox[1] + pad * 2, 200)

    img = Image.new("RGBA", (text_w, text_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    tx = pad - bbox[0]
    ty = pad - bbox[1]
    # Black stroke for readability on bright backgrounds.
    try:
        draw.text((tx, ty), text, font=font, embedded_color=True,
                  fill=(255, 255, 255, 255),
                  stroke_width=4, stroke_fill=(0, 0, 0, 255))
    except TypeError:
        alpha_val = int(255 * opacity)
        draw.text((tx, ty), text, font=font,
                  fill=(255, 255, 255, alpha_val),
                  stroke_width=4, stroke_fill=(0, 0, 0, 255))
    img.save(output_path, "PNG")
    # Avoid printing the emoji text itself — Windows cp1252 console chokes
    # on Unicode. Log char count instead.
    print(f"[+] Emoji overlay: {output_path} ({text_w}x{text_h}, {len(text)} chars)")
    return True


# Keep the old name as an alias so existing callers don't break — the new
# overlay replaces the watermark entirely, so this is the same file.
def _create_watermark_png(output_path: str, text: str = None,
                          fontsize: int = 160, opacity: float = 0.95) -> bool:
    return _create_emoji_overlay_png(output_path, text=text,
                                     fontsize=fontsize, opacity=opacity)


def _get_video_resolution(video_path: str) -> tuple[int, int] | None:
    """Get video width and height using ffprobe."""
    try:
        env = os.environ.copy()
        env["MSYS_NO_PATHCONV"] = "1"
        result = subprocess.run(
            ["ffprobe", "-v", "error",
             "-select_streams", "v:0",
             "-show_entries", "stream=width,height",
             "-of", "csv=p=0:s=x",
             video_path],
            capture_output=True, text=True, timeout=15, env=env
        )
        parts = result.stdout.strip().split("x")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except Exception as e:
        print(f"[!!] ffprobe error: {e}")
    return None


def _get_video_duration(video_path: str) -> float | None:
    """Get duration in seconds via ffprobe."""
    try:
        env = os.environ.copy()
        env["MSYS_NO_PATHCONV"] = "1"
        result = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1",
             video_path],
            capture_output=True, text=True, timeout=15, env=env
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"[!!] ffprobe duration error: {e}")
    return None


def process_video(input_path: str, output_path: str) -> bool:
    """
    Prepend our thumbnail as a 0.4s freeze frame (becomes the reel's
    cover since IG auto-picks the first frame) and burn random MOTION
    + emojis on top of the whole thing. Returns True on success.
    """
    # Always regenerate the overlay so each video gets fresh random emojis.
    try:
        if os.path.exists(WATERMARK_PATH):
            os.remove(WATERMARK_PATH)
    except OSError:
        pass
    if not _create_emoji_overlay_png(WATERMARK_PATH):
        print("[!!] Failed to create emoji overlay — skipping processing")
        return False

    has_thumbnail = os.path.exists(THUMBNAIL_PATH)
    has_watermark = os.path.exists(WATERMARK_PATH)

    # Get video resolution and duration
    resolution = _get_video_resolution(input_path)
    if not resolution:
        print("[!!] Could not detect video resolution — skipping processing")
        return False

    vid_w, vid_h = resolution
    vid_duration = _get_video_duration(input_path) or 0.0
    print(f"  [proc] Video: {vid_w}x{vid_h}, {vid_duration:.1f}s")

    # Build ffmpeg command
    env = os.environ.copy()
    env["MSYS_NO_PATHCONV"] = "1"

    # Use a temp file in the same directory as output
    out_dir = os.path.dirname(output_path) or "."
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4", dir=out_dir)
    os.close(tmp_fd)

    try:
        if has_thumbnail and has_watermark:
            # Flow per output frame:
            #   1. 0.4s thumbnail (still frame) — this becomes the reel cover
            #   2. main video
            #   3. last 0.8s of the video crossfades into a 1.5s thumbnail outro
            # Audio: main video audio + 0.4s silence prepend + 1.5s silence append.
            # The xfade offset = (prepend_duration + main_duration) - fade_duration.
            pre_dur = 0.4
            post_dur = 1.5
            fade_dur = 0.8
            xfade_offset = pre_dur + vid_duration - fade_dur
            if xfade_offset < 0:
                xfade_offset = 0
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-t", str(pre_dur), "-i", THUMBNAIL_PATH,
                "-i", input_path,
                "-loop", "1", "-t", str(post_dur), "-i", THUMBNAIL_PATH,
                "-i", WATERMARK_PATH,
                "-filter_complex",
                (
                    # Scale thumbnails (pre + post) with letterboxing so the
                    # aspect ratio of the cover image is preserved.
                    f"[0:v]scale={vid_w}:{vid_h}:force_original_aspect_ratio=decrease,"
                    f"pad={vid_w}:{vid_h}:(ow-iw)/2:(oh-ih)/2:color=black,"
                    f"setsar=1,format=yuv420p,fps=30[thumb_pre];"
                    f"[2:v]scale={vid_w}:{vid_h}:force_original_aspect_ratio=decrease,"
                    f"pad={vid_w}:{vid_h}:(ow-iw)/2:(oh-ih)/2:color=black,"
                    f"setsar=1,format=yuv420p,fps=30[thumb_post];"
                    # Normalize main video for concat/xfade.
                    f"[1:v]scale={vid_w}:{vid_h},setsar=1,format=yuv420p,fps=30[vid];"
                    # Prepend: 0.4s thumbnail + main video (video only).
                    f"[thumb_pre][vid]concat=n=2:v=1:a=0,settb=1/30000,fps=30[catv];"
                    # Outro: crossfade the tail of the prepended stream into
                    # the post-thumbnail clip over 0.8s. Both inputs must
                    # share a timebase or xfade fails with
                    # "timebase do not match" (concat uses 1/1000000, the
                    # image input uses 1/30 — force both to 1/30000).
                    f"[thumb_post]settb=1/30000,fps=30[thumb_post_tb];"
                    f"[catv][thumb_post_tb]xfade=transition=fade:duration={fade_dur}:"
                    f"offset={xfade_offset:.3f}[xfv];"
                    # Audio: shift main audio by pre_dur + pad by (post_dur - fade_dur).
                    # Total audio length = pre_dur + main_dur + (post_dur - fade_dur)
                    # = pre_dur + main_dur + post_dur - fade_dur, which matches the
                    # output video length. Static pad_dur avoids -shortest needing
                    # an infinite audio stream (which breaks aac encode).
                    f"[1:a]aresample=44100,adelay={int(pre_dur*1000)}|{int(pre_dur*1000)},"
                    f"apad=pad_dur={post_dur - fade_dur:.3f}[aud];"
                    # Emoji overlay on the final video.
                    f"[xfv][3:v]overlay=(W-w)/2:H*0.15,format=yuv420p[outv]"
                ),
                "-map", "[outv]", "-map", "[aud]",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                "-profile:v", "high", "-level", "4.0",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                "-movflags", "+faststart",
                tmp_path
            ]
        elif has_watermark:
            # Fallback (no thumbnail): just overlay emojis.
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-i", WATERMARK_PATH,
                "-filter_complex",
                f"[0:v][1:v]overlay=(W-w)/2:H*0.15,format=yuv420p[outv]",
                "-map", "[outv]", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                "-profile:v", "high", "-level", "4.0",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                "-movflags", "+faststart",
                tmp_path
            ]
        else:
            print("[~] No watermark — skipping processing")
            return False

        print(f"  [proc] Running ffmpeg...")
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, env=env
        )

        if result.returncode != 0:
            print(f"  [!!] ffmpeg failed (exit {result.returncode})")
            # Print last few lines of stderr for debugging
            stderr_lines = result.stderr.strip().split("\n")
            for line in stderr_lines[-5:]:
                print(f"  [ffmpeg] {line}")
            # Clean up temp file
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            return False

        # Move temp file to output path
        # If input_path == output_path, we replace in-place
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
            shutil.move(tmp_path, output_path)
        except Exception as e:
            print(f"  [!!] Failed to move processed video: {e}")
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            return False

        print(f"  [proc] Done — processed video saved")
        return True

    except subprocess.TimeoutExpired:
        print("[!!] ffmpeg timed out (120s)")
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        return False
    except Exception as e:
        print(f"[!!] Video processing error: {e}")
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        return False
