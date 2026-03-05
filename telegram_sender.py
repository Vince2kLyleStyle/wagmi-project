"""
TikTok Scraper — Telegram Sender Module
Sends scraped TikTok URLs to a Telegram download bot via Telethon.

First run:  python tiktok_scraper.py --telegram-login
            (authenticates with Telegram, saves session)
After that: python tiktok_scraper.py -k trading
            (uses saved session, no login needed)
"""

import os
import asyncio
import random
from telethon import TelegramClient
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


async def send_urls_to_bot(urls, bot_username=None):
    """
    Send each URL as a message to the Telegram download bot.
    Returns (sent_count, failed_count).
    """
    bot_username = bot_username or cfg.TELEGRAM_BOT_USERNAME

    client = await create_client()
    if not client:
        return 0, len(urls)

    try:
        # Resolve the bot
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

                # Random delay between messages
                if i < len(urls):
                    delay = random.uniform(
                        cfg.TELEGRAM_SEND_DELAY_MIN,
                        cfg.TELEGRAM_SEND_DELAY_MAX,
                    )
                    await asyncio.sleep(delay)

            except FloodWaitError as e:
                print(f"   ⏳  Telegram flood wait: {e.seconds}s — pausing...")
                await asyncio.sleep(e.seconds + 1)
                # Retry once
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


def send_urls_sync(urls, bot_username=None):
    """Synchronous wrapper for send_urls_to_bot."""
    return asyncio.run(send_urls_to_bot(urls, bot_username))


if __name__ == "__main__":
    # Quick test — send a single URL
    test_url = "https://www.tiktok.com/@test/video/1234567890"
    sent, failed = send_urls_sync([test_url])
    print(f"\nDone: {sent} sent, {failed} failed")
