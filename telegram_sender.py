"""
TikTok Scraper — Telegram Sender + Downloader Module
Sends scraped TikTok URLs to a Telegram download bot via Telethon,
then waits for the bot's video reply and saves it locally.

First run:  python tiktok_scraper.py --telegram-login
After that: python tiktok_scraper.py -k trading
"""

import os
import re
import asyncio
import random
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

import scraper_config as cfg


async def telegram_login():
    """
    First-time Telegram login. Prompts for phone + auth code, saves session.
    Run this once before using the scraper with Telegram enabled.
    """
    api_id = cfg.TELEGRAM_API_ID
    api_hash = cfg.TELEGRAM_API_HASH

    if not api_id or not api_hash:
        print("\n❌  Telegram API credentials not set!")
        print("   1. Go to https://my.telegram.org/apps")
        print("   2. Create an app and get your API ID + API Hash")
        print("   3. Set them as environment variables:")
        print('      $env:TELEGRAM_API_ID = "your_id"')
        print('      $env:TELEGRAM_API_HASH = "your_hash"')
        print("   Or edit scraper_config.py directly.\n")
        return False

    os.makedirs(cfg.TELEGRAM_SESSION_DIR, exist_ok=True)
    session_path = os.path.join(cfg.TELEGRAM_SESSION_DIR, cfg.TELEGRAM_SESSION_NAME)

    print("\n📱  Telegram Login — One-Time Setup")
    print("   You'll be asked for your phone number and an auth code.\n")

    client = TelegramClient(session_path, int(api_id), api_hash)
    phone = cfg.TELEGRAM_PHONE or None
    await client.start(phone=phone)

    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"\n   ✅  Logged in as: {me.first_name} (@{me.username or 'N/A'})")
        print("   Session saved! Future runs won't need login.\n")
        await client.disconnect()
        return True
    else:
        print("\n   ❌  Login failed. Try again.\n")
        await client.disconnect()
        return False


def telegram_login_sync():
    """Synchronous wrapper for telegram_login."""
    return asyncio.run(telegram_login())


async def create_client():
    """Load existing Telegram session. Returns None if no session exists."""
    api_id = cfg.TELEGRAM_API_ID
    api_hash = cfg.TELEGRAM_API_HASH

    if not api_id or not api_hash:
        print("\n❌  Telegram API credentials not set!")
        print('   Set: $env:TELEGRAM_API_ID = "your_id"')
        print('   Set: $env:TELEGRAM_API_HASH = "your_hash"')
        return None

    os.makedirs(cfg.TELEGRAM_SESSION_DIR, exist_ok=True)
    session_path = os.path.join(cfg.TELEGRAM_SESSION_DIR, cfg.TELEGRAM_SESSION_NAME)
    session_file = session_path + ".session"

    if not os.path.exists(session_file):
        print("\n❌  No Telegram session found!")
        print("   Run first:  py tiktok_scraper.py --telegram-login\n")
        return None

    client = TelegramClient(session_path, int(api_id), api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        print("\n❌  Telegram session expired!")
        print("   Re-run:  py tiktok_scraper.py --telegram-login\n")
        await client.disconnect()
        return None

    return client


def _sanitize_filename(url):
    """Extract a clean filename from a TikTok or Instagram URL."""
    # TikTok: @user/video/12345
    match = re.search(r"@([^/]+)/video/(\d+)", url)
    if match:
        return f"{match.group(1)}_{match.group(2)}.mp4"
    match = re.search(r"/video/(\d+)", url)
    if match:
        return f"tiktok_{match.group(1)}.mp4"
    # Instagram: /reel/SHORTCODE/ or /p/SHORTCODE/
    match = re.search(r"instagram\.com/(?:reel|p)/([A-Za-z0-9_-]+)", url)
    if match:
        return f"ig_{match.group(1)}.mp4"
    return f"video_{hash(url) & 0xFFFFFFFF:08x}.mp4"


async def _wait_for_video(client, bot_entity, timeout):
    """Wait for the bot to send back a video/document message."""
    video_event = asyncio.Event()
    result = {"message": None}

    @client.on(events.NewMessage(from_users=bot_entity))
    async def handler(event):
        msg = event.message
        # Bot replied with a video or document (video file)
        if msg.video or msg.document:
            result["message"] = msg
            video_event.set()
        # Some bots send a "processing" text first, ignore those
        # But if bot sends an error text, capture it
        elif msg.text and any(w in msg.text.lower() for w in ["error", "fail", "can't", "unable", "sorry"]):
            result["message"] = msg
            video_event.set()

    try:
        await asyncio.wait_for(video_event.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        pass
    finally:
        client.remove_event_handler(handler)

    return result["message"]


async def send_and_download(urls, bot_username=None, download_dir=None):
    """
    Send each URL to the bot, wait for video reply, download to local folder.
    Returns (sent_count, downloaded_count, failed_count).
    """
    bot_username = bot_username or cfg.TELEGRAM_BOT_USERNAME
    download_dir = download_dir or cfg.DOWNLOAD_DIR
    timeout = cfg.TELEGRAM_DOWNLOAD_TIMEOUT

    os.makedirs(download_dir, exist_ok=True)

    client = await create_client()
    if not client:
        return 0, 0, len(urls)

    try:
        try:
            bot_entity = await client.get_entity(bot_username)
            print(f"\n📱  Connected to Telegram bot: @{bot_username}")
            print(f"📂  Download folder: {download_dir}")
        except Exception as e:
            print(f"\n❌  Could not find bot @{bot_username}: {e}")
            return 0, 0, len(urls)

        sent = 0
        downloaded = 0
        failed = 0

        for i, url in enumerate(urls, 1):
            try:
                # Send URL to bot
                await client.send_message(bot_entity, url)
                sent += 1
                print(f"\n   📤  [{i}/{len(urls)}] Sent: {url}")

                # Wait for bot to reply with video
                print(f"   ⏳  Waiting for download (up to {timeout}s)...")
                reply = await _wait_for_video(client, bot_entity, timeout)

                if reply and (reply.video or reply.document):
                    # Download the video file
                    filename = _sanitize_filename(url)
                    filepath = os.path.join(download_dir, filename)

                    # Avoid overwriting existing files
                    if os.path.exists(filepath):
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(filepath):
                            filepath = os.path.join(download_dir, f"{base}_{counter}{ext}")
                            counter += 1

                    await client.download_media(reply, file=filepath)
                    downloaded += 1
                    size_mb = os.path.getsize(filepath) / (1024 * 1024)
                    print(f"   💾  Downloaded: {os.path.basename(filepath)} ({size_mb:.1f} MB)")

                elif reply and reply.text:
                    # Bot replied with an error message
                    failed += 1
                    print(f"   ❌  Bot error: {reply.text[:100]}")
                else:
                    # Timeout — no reply
                    failed += 1
                    print(f"   ⚠️  No video received (timeout)")

                # Delay between messages
                if i < len(urls):
                    delay = random.uniform(
                        cfg.TELEGRAM_SEND_DELAY_MIN,
                        cfg.TELEGRAM_SEND_DELAY_MAX,
                    )
                    await asyncio.sleep(delay)

            except FloodWaitError as e:
                print(f"   ⏳  Telegram flood wait: {e.seconds}s — pausing...")
                await asyncio.sleep(e.seconds + 1)
                try:
                    await client.send_message(bot_entity, url)
                    sent += 1
                    print(f"   📤  [{i}/{len(urls)}] Sent (retry): {url}")
                    reply = await _wait_for_video(client, bot_entity, timeout)
                    if reply and (reply.video or reply.document):
                        filename = _sanitize_filename(url)
                        filepath = os.path.join(download_dir, filename)
                        await client.download_media(reply, file=filepath)
                        downloaded += 1
                        print(f"   💾  Downloaded: {os.path.basename(filepath)}")
                    else:
                        failed += 1
                except Exception:
                    failed += 1
                    print(f"   ❌  [{i}/{len(urls)}] Failed: {url}")

            except Exception as e:
                failed += 1
                print(f"   ❌  [{i}/{len(urls)}] Failed: {url} — {e}")

        return sent, downloaded, failed

    finally:
        await client.disconnect()


async def send_urls_to_bot(urls, bot_username=None):
    """
    Send each URL as a message to the Telegram download bot (no auto-download).
    Returns (sent_count, failed_count).
    """
    bot_username = bot_username or cfg.TELEGRAM_BOT_USERNAME

    client = await create_client()
    if not client:
        return 0, len(urls)

    try:
        try:
            bot_entity = await client.get_entity(bot_username)
            print(f"\n📱  Connected to Telegram bot: @{bot_username}")
        except Exception as e:
            print(f"\n❌  Could not find bot @{bot_username}: {e}")
            return 0, len(urls)

        sent = 0
        failed = 0

        for i, url in enumerate(urls, 1):
            try:
                await client.send_message(bot_entity, url)
                sent += 1
                print(f"   📤  [{i}/{len(urls)}] Sent: {url}")

                if i < len(urls):
                    delay = random.uniform(
                        cfg.TELEGRAM_SEND_DELAY_MIN,
                        cfg.TELEGRAM_SEND_DELAY_MAX,
                    )
                    await asyncio.sleep(delay)

            except FloodWaitError as e:
                print(f"   ⏳  Telegram flood wait: {e.seconds}s — pausing...")
                await asyncio.sleep(e.seconds + 1)
                try:
                    await client.send_message(bot_entity, url)
                    sent += 1
                    print(f"   📤  [{i}/{len(urls)}] Sent (retry): {url}")
                except Exception:
                    failed += 1
                    print(f"   ❌  [{i}/{len(urls)}] Failed: {url}")

            except Exception as e:
                failed += 1
                print(f"   ❌  [{i}/{len(urls)}] Failed: {url} — {e}")

        return sent, failed

    finally:
        await client.disconnect()


def _run_coroutine(coro):
    """Run a coroutine safely regardless of whether an event loop is running."""
    try:
        asyncio.get_running_loop()
        # An event loop is already running — run in a new thread to avoid conflict
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No running loop — safe to call asyncio.run() directly
        return asyncio.run(coro)


def send_urls_sync(urls, bot_username=None):
    """Synchronous wrapper for send_urls_to_bot."""
    return _run_coroutine(send_urls_to_bot(urls, bot_username))


def send_and_download_sync(urls, bot_username=None, download_dir=None):
    """Synchronous wrapper for send_and_download."""
    return _run_coroutine(send_and_download(urls, bot_username, download_dir))


if __name__ == "__main__":
    test_url = "https://www.tiktok.com/@test/video/1234567890"
    sent, downloaded, failed = send_and_download_sync([test_url])
    print(f"\nDone: {sent} sent, {downloaded} downloaded, {failed} failed")
