"""
InstagramReelsUploader
======================
Raw HTTP uploader using Instagram's private iOS API.
Mirrors the fingerprint of a real iPhone running Instagram 261.x,
which avoids the per-post suppression instagrapi triggers.

Credentials are extracted from an instagrapi Client after login —
no Burp Suite or patched IPA required for initial setup.
"""

import json
import os
import subprocess
import time
import uuid as uuid_lib

import requests


# ─── iPhone fingerprint ───────────────────────────────────────────
IG_APP_ID        = "124024574287414"   # Instagram iOS app ID (constant)
IG_VERSION       = "261.1.0.56"
IOS_DEVICE       = "iPhone13,2"        # iPhone 12
IOS_VERSION      = "16_6"
SCALE            = "3.00"
RESOLUTION       = "1170x2532"
BUILD_NUMBER     = "422787551"

USER_AGENT = (
    f"Instagram {IG_VERSION} "
    f"({IOS_DEVICE}; iOS {IOS_VERSION}; en_US; en-US; "
    f"scale={SCALE}; {RESOLUTION}; {BUILD_NUMBER})"
)

# How long to wait between transcoder status checks (seconds)
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
        device_id: str,            # phone UUID  →  X-Ig-Family-Device-Id
        session_id: str = None,
        bloks_version_id: str = "",
        proxy: str = None,
    ):
        self.auth_token       = auth_token
        self.user_id          = user_id
        self.device_id        = device_id
        self.session_id       = session_id or str(uuid_lib.uuid4())
        self.bloks_version_id = bloks_version_id

        self._session = requests.Session()
        self.base_url = "https://i.instagram.com"

        # Ensure token has proper prefix
        bearer = (
            auth_token
            if auth_token.startswith("Bearer ")
            else f"Bearer {auth_token}"
        )

        self._session.headers.update({
            "Authorization":              bearer,
            "User-Agent":                 USER_AGENT,
            "Accept-Language":            "en-US",
            "Accept-Encoding":            "gzip, deflate",
            "X-Ig-App-Id":               IG_APP_ID,
            "X-Ig-Family-Device-Id":     device_id,
            "X-Ig-Device-Id":            device_id,
            "X-Ig-Connection-Type":      "WiFi",
            "X-Ig-App-Locale":           "en_US",
            "X-Ig-Device-Locale":        "en_US",
            "X-Ig-Mapped-Locale":        "en_US",
            "X-Bloks-Version-Id":        bloks_version_id,
            "X-Adpushup-Session-Id":     self.session_id,
            "X-Ig-Bandwidth-Speed-Kbps": "-1.000",
            "X-Ig-Bandwidth-TotalBytes-B": "0",
            "X-Ig-Bandwidth-TotalTime-MS": "0",
            "X-FB-Connection-Type":      "WIFI",
            "X-FB-Http-Engine":          "Liger",
            "X-Fb-Server-Cluster":       "true",
        })

        if proxy:
            self._session.proxies = {"http": proxy, "https": proxy}

    # ── helpers ──────────────────────────────────────────────────

    @staticmethod
    def _new_upload_id() -> str:
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

    def _upload_video(self, video_path: str, upload_id: str) -> bool:
        with open(video_path, "rb") as fh:
            data = fh.read()

        size        = len(data)
        entity_name = f"{upload_id}_0_{size}"
        url         = f"{self.base_url}/rupload/instagram_video/{entity_name}"

        resp = self._session.post(
            url,
            data=data,
            headers={
                "X-Entity-Type":   "video/mp4",
                "Offset":          "0",
                "X-Entity-Name":   entity_name,
                "X-Entity-Length": str(size),
                "Content-Type":    "application/octet-stream",
                "Content-Length":  str(size),
            },
            timeout=300,
        )
        if resp.status_code != 200:
            print(f"  [uploader] Video rupload failed: {resp.status_code} — {resp.text[:200]}")
            return False
        return True

    def _upload_thumbnail(self, thumb_path: str, upload_id: str) -> bool:
        with open(thumb_path, "rb") as fh:
            data = fh.read()

        size        = len(data)
        entity_name = f"{upload_id}_0_{size}_cover"
        url         = f"{self.base_url}/rupload/instagram_photo/{entity_name}"

        resp = self._session.post(
            url,
            data=data,
            headers={
                "X-Entity-Type":   "image/jpeg",
                "Offset":          "0",
                "X-Entity-Name":   entity_name,
                "X-Entity-Length": str(size),
                "Content-Type":    "application/octet-stream",
                "Content-Length":  str(size),
            },
            timeout=60,
        )
        if resp.status_code != 200:
            print(f"  [uploader] Thumbnail rupload failed: {resp.status_code}")
            return False
        return True

    def _poll_transcoder(self, upload_id: str) -> bool:
        """
        Poll until Instagram finishes transcoding the video.
        Mirrors the TRANSCODER_RETRY_DELAYS pattern from reference code.
        """
        for delay in TRANSCODER_RETRY_DELAYS:
            print(f"  [uploader] Transcoder check in {delay}s...", flush=True)
            time.sleep(delay)

            try:
                resp = self._session.get(
                    f"{self.base_url}/api/v1/media/{upload_id}/upload_finish/",
                    params={"video": "1"},
                    timeout=30,
                )
                if resp.status_code == 200:
                    body = resp.json()
                    status = body.get("status", "")
                    video_status = body.get("video_status", "")
                    if status == "ok" or video_status in ("transcoded", "ready", "finished"):
                        print(f"  [uploader] Transcoder ready!")
                        return True
            except Exception as e:
                print(f"  [uploader] Transcoder poll error (non-fatal): {e}")

        print(f"  [uploader] Transcoder timeout — proceeding anyway")
        return True  # try configure regardless

    def _configure_reel(
        self,
        upload_id: str,
        caption: str,
        video_info: dict,
        has_cover: bool = False,
    ) -> dict:
        """POST to configure_to_clips_v2 to publish the Reel."""
        clips = json.dumps([{
            "length":        video_info["duration"],
            "source_type":   "4",
            "camera_position": "back",
        }])

        payload = {
            "_uuid":                     self.device_id,
            "_uid":                      self.user_id,
            "device_id":                 f"android-{self.device_id[:16]}",
            "upload_id":                 upload_id,
            "source_type":               "4",
            "caption":                   caption,
            "usertags":                  json.dumps({"in": []}),
            "configure_mode":            "1",
            "camera_position":           "unknown",
            "clips_share_preview_to_feed": "1",
            "video_result":              "",
            "clips":                     clips,
            "poster_frame_index":        "0",
            "length":                    str(round(video_info["duration"], 2)),
            "extra":                     json.dumps({
                "source_width":  video_info["width"],
                "source_height": video_info["height"],
            }),
            "audio_muted":               "0",
            "clips_tab_pinned_user_ids": "[]",
            "scene_capture_type":        "",
            "timezone_offset":           "-18000",
            "date_time_original":        time.strftime("%Y%m%dT%H%M%S.000Z"),
            "clips_creative_tools":      "{}",
        }

        if has_cover:
            payload["cover_frame_timestamp"] = "0.0"

        resp = self._session.post(
            f"{self.base_url}/api/v1/media/configure_to_clips_v2/",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=60,
        )

        try:
            result = resp.json()
        except Exception:
            result = {"status": "error", "message": resp.text[:300]}

        if resp.status_code != 200:
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
          1. Upload video via rupload
          2. Upload thumbnail via rupload (if provided)
          3. Poll transcoder
          4. Configure / publish

        Returns the raw API response dict.
        {'status': 'ok', 'media': {...}}  on success.
        """
        upload_id  = self._new_upload_id()
        video_info = self._video_info(video_path)

        print(f"  [uploader] Video upload — ID: {upload_id}")
        if not self._upload_video(video_path, upload_id):
            return {"status": "error", "message": "video rupload failed"}

        has_cover = False
        if thumbnail_path and os.path.exists(thumbnail_path):
            print(f"  [uploader] Thumbnail upload...")
            has_cover = self._upload_thumbnail(thumbnail_path, upload_id)

        self._poll_transcoder(upload_id)

        print(f"  [uploader] Configuring reel...")
        return self._configure_reel(upload_id, caption, video_info, has_cover)


# ─── Credential extraction from instagrapi ───────────────────────

def from_instagrapi_client(cl, proxy: str = None) -> InstagramReelsUploader:
    """
    Pull all needed credentials out of an already-logged-in
    instagrapi Client and return a ready InstagramReelsUploader.

    Call this once after cl.login() — reuse the returned uploader
    for all uploads in the session.
    """
    # Grab the exact Authorization header instagrapi is currently sending
    auth_token = cl.private.headers.get("Authorization", "")
    if not auth_token:
        # Fallback: reconstruct from session data
        settings  = cl.get_settings()
        auth_data = settings.get("authorization_data", {})
        import base64
        raw = json.dumps({
            "ds_user_id": auth_data.get("ds_user_id", str(cl.user_id)),
            "sessionid":  auth_data.get("sessionid", ""),
        })
        auth_token = f"Bearer IGT:2:{base64.b64encode(raw.encode()).decode()}"

    settings = cl.get_settings()
    uuids    = settings.get("uuids", {})

    device_id        = uuids.get("phone_id", str(uuid_lib.uuid4()))
    client_session   = uuids.get("client_session_id", str(uuid_lib.uuid4()))
    bloks_version    = settings.get("bloks_versioning_id", "")
    user_id          = str(cl.user_id)

    print(f"  [uploader] Credentials extracted — user_id={user_id[:6]}*** device={device_id[:8]}***")

    return InstagramReelsUploader(
        auth_token       = auth_token,
        user_id          = user_id,
        device_id        = device_id,
        session_id       = client_session,
        bloks_version_id = bloks_version,
        proxy            = proxy,
    )
