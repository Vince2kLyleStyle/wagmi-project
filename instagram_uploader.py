"""
InstagramReelsUploader
======================
Raw HTTP uploader using Instagram's private API with iOS fingerprint.
Mirrors the fingerprint of a real iPhone running Instagram 261.x,
which avoids the per-post suppression instagrapi triggers.

Credentials are extracted from an instagrapi Client after login —
no Burp Suite or patched IPA required for initial setup.
"""

import json
import os
import random
import subprocess
import time
import uuid as uuid_lib

import requests


# ─── iPhone fingerprint constants ─────────────────────────────────
IG_APP_ID    = "124024574287414"   # Instagram iOS app ID (constant)
IG_VERSION   = "261.1.0.56"
IOS_DEVICE   = "iPhone13,2"        # iPhone 12
IOS_VERSION  = "16_6"
SCALE        = "3.00"
RESOLUTION   = "1170x2532"
BUILD_NUMBER = "422787551"

USER_AGENT = (
    f"Instagram {IG_VERSION} "
    f"({IOS_DEVICE}; iOS {IOS_VERSION}; en_US; en-US; "
    f"scale={SCALE}; {RESOLUTION}; {BUILD_NUMBER})"
)

# Delays (seconds) between configure retries while transcoder is running
TRANSCODER_RETRY_DELAYS = [30, 90, 270]


class InstagramReelsUploader:
    """
    Uploads a Reel via Instagram's private rupload + configure API
    using a real iOS fingerprint and Bearer auth token.
    """

    def __init__(
        self,
        auth_token: str,
        user_id: str,
        device_id: str,             # phone_id UUID → X-Ig-Family-Device-Id
        session_id: str = None,
        bloks_version_id: str = "",
        timezone_offset: int = -18000,
        proxy: str = None,
    ):
        self.user_id          = user_id
        self.device_id        = device_id
        self.session_id       = session_id or str(uuid_lib.uuid4())
        self.bloks_version_id = bloks_version_id
        self.timezone_offset  = timezone_offset

        self._session = requests.Session()
        self.base_url = "https://i.instagram.com"

        bearer = (
            auth_token
            if auth_token.startswith("Bearer ")
            else f"Bearer {auth_token}"
        )

        self._session.headers.update({
            "Authorization":                bearer,
            "User-Agent":                   USER_AGENT,
            "Accept-Language":              "en-US",
            "Accept-Encoding":              "gzip, deflate",
            "X-Ig-App-Id":                 IG_APP_ID,
            "X-Ig-Family-Device-Id":       device_id,
            "X-Ig-Device-Id":              device_id,
            "X-Ig-Connection-Type":        "WiFi",
            "X-Ig-App-Locale":             "en_US",
            "X-Ig-Device-Locale":          "en_US",
            "X-Ig-Mapped-Locale":          "en_US",
            "X-Bloks-Version-Id":          bloks_version_id,
            "X-Adpushup-Session-Id":       self.session_id,
            "X-Ig-Bandwidth-Speed-Kbps":   "-1.000",
            "X-Ig-Bandwidth-TotalBytes-B": "0",
            "X-Ig-Bandwidth-TotalTime-MS": "0",
            "X-FB-Connection-Type":        "WIFI",
            "X-FB-Http-Engine":            "Liger",
            "X-Fb-Server-Cluster":         "true",
        })

        if proxy:
            self._session.proxies = {"http": proxy, "https": proxy}

    # ── helpers ──────────────────────────────────────────────────

    @staticmethod
    def _new_upload_id() -> str:
        """Millisecond timestamp — matches Instagram app format."""
        return str(int(time.time() * 1000))

    @staticmethod
    def _video_info(video_path: str) -> dict:
        """Return width, height, duration via ffprobe."""
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-select_streams", "v:0",
                 "-show_entries", "stream=width,height,duration",
                 "-of", "json", video_path],
                capture_output=True, text=True, timeout=15,
            )
            data   = json.loads(probe.stdout)
            stream = data["streams"][0]
            return {
                "width":    int(stream.get("width",    720)),
                "height":   int(stream.get("height",  1280)),
                "duration": float(stream.get("duration", 15.0)),
            }
        except Exception:
            return {"width": 720, "height": 1280, "duration": 15.0}

    # ── upload steps ─────────────────────────────────────────────

    def _upload_video(self, video_path: str, upload_id: str, video_info: dict) -> bool:
        """
        Two-step rupload:
          1. GET  → tells Instagram we're about to upload (init slot)
          2. POST → send the actual video bytes
        """
        with open(video_path, "rb") as fh:
            video_data = fh.read()

        size         = len(video_data)
        rand         = random.randint(1000000000, 9999999999)
        upload_name  = f"{upload_id}_0_{rand}"
        waterfall_id = str(uuid_lib.uuid4())

        rupload_params = json.dumps({
            "is_clips_video":            "1",
            "retry_context":             '{"num_reupload":0,"num_step_auto_retry":0,"num_step_manual_retry":0}',
            "media_type":                "2",
            "xsharing_user_ids":         json.dumps([self.user_id]),
            "upload_id":                 upload_id,
            "upload_media_duration_ms":  str(int(video_info["duration"] * 1000)),
            "upload_media_width":        str(video_info["width"]),
            "upload_media_height":       str(video_info["height"]),
        })

        url = f"{self.base_url}/rupload_igvideo/{upload_name}"

        # Headers shared between GET init and POST upload
        rupload_headers = {
            "Accept-Encoding":            "gzip",
            "X-Instagram-Rupload-Params": rupload_params,
            "X_FB_VIDEO_WATERFALL_ID":    waterfall_id,
            "X-Entity-Type":              "video/mp4",
        }

        # Step 1: GET — init the upload slot
        try:
            self._session.get(url, headers=rupload_headers, timeout=30)
        except Exception as e:
            print(f"  [uploader] Rupload init warning (non-fatal): {e}")

        # Step 2: POST — send video bytes
        resp = self._session.post(
            url,
            data=video_data,
            headers={
                **rupload_headers,
                "Offset":          "0",
                "X-Entity-Name":   upload_name,
                "X-Entity-Length": str(size),
                "Content-Type":    "application/octet-stream",
                "Content-Length":  str(size),
            },
            timeout=300,
        )

        if resp.status_code != 200:
            print(f"  [uploader] Video rupload failed {resp.status_code}: {resp.text[:300]}")
            return False

        return True

    def _upload_thumbnail(self, thumb_path: str, upload_id: str) -> bool:
        """Upload cover image via photo rupload using same upload_id as video."""
        with open(thumb_path, "rb") as fh:
            thumb_data = fh.read()

        size        = len(thumb_data)
        rand        = random.randint(1000000000, 9999999999)
        entity_name = f"{upload_id}_0_{rand}"
        url         = f"{self.base_url}/rupload_igphoto/{entity_name}"

        rupload_params = json.dumps({
            "retry_context":     '{"num_reupload":0,"num_step_auto_retry":0,"num_step_manual_retry":0}',
            "media_type":        "1",
            "upload_id":         upload_id,
            "image_compression": json.dumps({
                "lib_name": "moz", "lib_version": "3.1.m", "quality": "80"
            }),
        })

        resp = self._session.post(
            url,
            data=thumb_data,
            headers={
                "X-Entity-Type":              "image/jpeg",
                "Offset":                     "0",
                "X-Entity-Name":              entity_name,
                "X-Entity-Length":            str(size),
                "Content-Type":               "application/octet-stream",
                "Content-Length":             str(size),
                "X-Instagram-Rupload-Params": rupload_params,
            },
            timeout=60,
        )

        if resp.status_code != 200:
            print(f"  [uploader] Thumbnail rupload failed {resp.status_code}: {resp.text[:200]}")
            return False

        return True

    def _configure_reel(
        self,
        upload_id: str,
        caption: str,
        video_info: dict,
    ) -> dict:
        """
        POST to configure_to_clips to publish the uploaded video as a Reel.
        Payload matches instagrapi's clip_configure exactly.
        """
        duration = round(video_info["duration"], 3)
        width    = video_info["width"]
        height   = video_info["height"]

        # Device block (matches what the real Instagram iOS app sends)
        device = {
            "manufacturer":    "Apple",
            "model":           IOS_DEVICE,
            "android_version": 26,
            "android_release": "8.0.0",
        }

        payload = {
            "filter_type":                 "0",
            "timezone_offset":             str(self.timezone_offset),
            "media_folder":                "ScreenRecorder",
            "source_type":                 "4",
            "caption":                     caption,
            "usertags":                    json.dumps({"in": []}),
            "date_time_original":          time.strftime("%Y%m%dT%H%M%S.000Z"),
            "clips_share_preview_to_feed": "1",
            "upload_id":                   upload_id,
            "device":                      json.dumps(device),
            "length":                      str(duration),
            "clips":                       json.dumps([{
                "length":      duration,
                "source_type": "4",
            }]),
            "extra":                       json.dumps({
                "source_width":  width,
                "source_height": height,
            }),
            "audio_muted":                 "0",
            "poster_frame_index":          "70",
        }

        resp = self._session.post(
            f"{self.base_url}/api/v1/media/configure_to_clips/",
            params={"video": "1"},
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=60,
        )

        try:
            result = resp.json()
        except Exception:
            result = {"status": "error", "message": resp.text[:300]}

        # Map HTTP error codes to named statuses the main loop can act on
        if resp.status_code == 429:
            result["status"] = "THROTTLED"
        elif resp.status_code in (401, 403):
            result["status"] = "LOGIN_EXPIRED"
        elif resp.status_code != 200:
            # Check body for challenge / login signals
            body_str = json.dumps(result).lower()
            if "challenge" in body_str:
                result["status"] = "CHALLENGE"
            elif "login_required" in body_str or "not authorized" in body_str:
                result["status"] = "LOGIN_EXPIRED"
            else:
                print(f"  [uploader] Configure failed {resp.status_code}: {result}")

        return result

    # ── public API ───────────────────────────────────────────────

    def upload_reel(
        self,
        video_path: str,
        caption: str = "",
        thumbnail_path: str = None,
    ) -> dict:
        """
        Full Reel upload flow:
          1. Upload video via rupload_igvideo  (GET init → POST data)
          2. Upload thumbnail via rupload_igphoto (if provided)
          3. Configure / publish — retries with TRANSCODER_RETRY_DELAYS
             if Instagram hasn't finished transcoding yet

        Returns the raw API response dict.
        {'status': 'ok', 'media': {...}} on success.
        """
        upload_id  = self._new_upload_id()
        video_info = self._video_info(video_path)

        print(f"  [uploader] Video upload — ID: {upload_id} "
              f"({video_info['width']}x{video_info['height']}, "
              f"{video_info['duration']:.1f}s)")

        if not self._upload_video(video_path, upload_id, video_info):
            return {"status": "error", "message": "video rupload failed"}

        if thumbnail_path and os.path.exists(thumbnail_path):
            print(f"  [uploader] Thumbnail upload...")
            self._upload_thumbnail(thumbnail_path, upload_id)

        # Configure with retries — Instagram may still be transcoding
        result = {}
        for attempt, delay in enumerate(TRANSCODER_RETRY_DELAYS):
            if attempt > 0:
                print(f"  [uploader] Waiting {delay}s before retry (transcoding)...", flush=True)
                time.sleep(delay)

            print(f"  [uploader] Configuring reel (attempt {attempt + 1}/{len(TRANSCODER_RETRY_DELAYS)})...")
            result = self._configure_reel(upload_id, caption, video_info)

            if result.get("status") == "ok":
                return result

            # Only retry on transcoding-related errors
            msg = str(result.get("message", "") or result.get("error_title", "")).lower()
            if not any(w in msg for w in ("transcode", "processing", "not ready", "upload not found")):
                # Definitive failure — no point retrying
                print(f"  [uploader] Configure error (non-transient): {result}")
                break

        return result


# ─── Credential extraction from instagrapi ───────────────────────

def from_instagrapi_client(cl, proxy: str = None) -> InstagramReelsUploader:
    """
    Pull all needed credentials out of an already-logged-in instagrapi
    Client and return a ready InstagramReelsUploader.

    Call once after cl.login() — reuse the returned uploader for every
    upload in the session.
    """
    # The exact Authorization header instagrapi is currently sending
    auth_token = cl.private.headers.get("Authorization", "")
    if not auth_token:
        # Fallback: reconstruct from session data
        import base64
        settings  = cl.get_settings()
        auth_data = settings.get("authorization_data", {})
        raw = json.dumps({
            "ds_user_id": auth_data.get("ds_user_id", str(cl.user_id)),
            "sessionid":  auth_data.get("sessionid", ""),
        })
        auth_token = f"Bearer IGT:2:{base64.b64encode(raw.encode()).decode()}"

    settings = cl.get_settings()
    uuids    = settings.get("uuids", {})

    device_id     = uuids.get("phone_id", str(uuid_lib.uuid4()))
    session_id    = uuids.get("client_session_id", str(uuid_lib.uuid4()))
    bloks_version = settings.get("bloks_versioning_id", "")
    user_id       = str(cl.user_id)
    tz_offset     = getattr(cl, "timezone_offset", -18000)

    uploader = InstagramReelsUploader(
        auth_token       = auth_token,
        user_id          = user_id,
        device_id        = device_id,
        session_id       = session_id,
        bloks_version_id = bloks_version,
        timezone_offset  = tz_offset,
        proxy            = proxy,
    )

    # Copy session cookies — sessionid cookie is critical for auth
    try:
        saved_cookies = settings.get("cookies", {})
        if saved_cookies:
            uploader._session.cookies.update(saved_cookies)
        # Also copy live cookies directly from instagrapi's requests.Session
        for cookie in cl.private.cookies:
            uploader._session.cookies.set(
                cookie.name, cookie.value, domain=cookie.domain
            )
    except Exception as e:
        print(f"  [uploader] Cookie copy warning (non-fatal): {e}")

    print(
        f"  [uploader] Ready — "
        f"user={user_id[:5]}*** "
        f"device={device_id[:8]}*** "
        f"bloks={bloks_version[:12] if bloks_version else 'none'}..."
    )
    return uploader
