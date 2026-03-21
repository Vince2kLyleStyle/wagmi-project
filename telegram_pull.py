#!/usr/bin/env python3
"""
Telegram Video Puller — Download videos from a Telegram chat.

Pull curated meme videos from a friend's DM, group, or channel
straight into your niche folder for Instagram posting.

Usage:
    py telegram_pull.py "Friend Name"                    # download from DM
    py telegram_pull.py "Friend Name" --limit 50         # last 50 messages
    py telegram_pull.py "Friend Name" --niche memes      # save to memes folder
    py telegram_pull.py --list-chats                     # find the right chat name
"""

import argparse
import asyncio
import os
import sys

from telethon import TelegramClient

import scraper_config as cfg


async def list_recent_chats(client, count=30):
    """List recent dialogs so the user can find the right chat name."""
    print(f"\n  Recent chats (last {count}):\n")
    async for dialog in client.iter_dialogs(limit=count):
        chat_type = "user" if dialog.is_user else ("group" if dialog.is_group else "channel")
        unread = f" ({dialog.unread_count} unread)" if dialog.unread_count else ""
        print(f"    [{chat_type:7s}]  {dialog.name}{unread}")
    print()


async def pull_videos(client, chat_name, download_dir, limit=100, min_size_mb=0.5):
    """
    Download all video/document media from a chat.
    Returns count of downloaded files.
    """
    # Find the chat
    entity = None
    async for dialog in client.iter_dialogs(limit=100):
        if chat_name.lower() in dialog.name.lower():
            entity = dialog.entity
            print(f"\n  Found chat: {dialog.name}")
            break

    if not entity:
        print(f"\n  Could not find chat matching '{chat_name}'")
        print("  Run with --list-chats to see available chats")
        return 0

    os.makedirs(download_dir, exist_ok=True)

    # Count existing files to avoid re-downloading
    existing = set(os.listdir(download_dir))

    downloaded = 0
    skipped = 0
    checked = 0

    print(f"  Scanning last {limit} messages for videos...")
    print(f"  Saving to: {download_dir}\n")

    async for message in client.iter_messages(entity, limit=limit):
        checked += 1

        # Only want video files
        if not (message.video or (message.document and message.document.mime_type
                                  and message.document.mime_type.startswith("video/"))):
            continue

        # Build filename from message ID + date
        date_str = message.date.strftime("%Y%m%d")
        filename = f"tg_{date_str}_{message.id}.mp4"

        if filename in existing:
            skipped += 1
            continue

        filepath = os.path.join(download_dir, filename)

        # Download
        try:
            await client.download_media(message, file=filepath)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)

            # Skip tiny files (likely errors or thumbnails)
            if size_mb < min_size_mb:
                os.remove(filepath)
                continue

            downloaded += 1
            print(f"  [{downloaded:3d}] {filename} ({size_mb:.1f} MB)")

        except Exception as e:
            print(f"  Failed: {filename} — {e}")

    print(f"\n  Done! {downloaded} downloaded, {skipped} already had, {checked} messages checked")
    return downloaded


async def main_async(args):
    api_id = cfg.TELEGRAM_API_ID
    api_hash = cfg.TELEGRAM_API_HASH

    if not api_id or not api_hash:
        print("\n  Telegram API credentials not set!")
        print("  Run: py tiktok_scraper.py --telegram-login")
        sys.exit(1)

    session_path = os.path.join(cfg.TELEGRAM_SESSION_DIR, cfg.TELEGRAM_SESSION_NAME)
    client = TelegramClient(session_path, int(api_id), api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        print("\n  Telegram session expired! Run: py tiktok_scraper.py --telegram-login")
        await client.disconnect()
        sys.exit(1)

    try:
        if args.list_chats:
            await list_recent_chats(client)
        else:
            download_dir = os.path.join(cfg.DOWNLOAD_DIR, args.niche)
            await pull_videos(client, args.chat, download_dir, limit=args.limit)
    finally:
        await client.disconnect()


def main():
    parser = argparse.ArgumentParser(description="Pull videos from a Telegram chat")
    parser.add_argument("chat", nargs="?", default=None, help="Chat name to pull from (partial match)")
    parser.add_argument("--limit", type=int, default=200, help="Max messages to scan (default: 200)")
    parser.add_argument("--niche", default="memes", help="Niche folder name (default: memes)")
    parser.add_argument("--list-chats", action="store_true", help="List recent chats to find the right name")

    args = parser.parse_args()

    if not args.list_chats and not args.chat:
        parser.print_help()
        print('\n  Example: py telegram_pull.py "John" --niche memes')
        sys.exit(1)

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
