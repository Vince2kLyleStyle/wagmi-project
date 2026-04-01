@echo off
title Motion Bot — Full Pipeline
cd /d "%~dp0"
color 0A

echo.
echo  ============================================================
echo   MOTION BOT — Full Pipeline
echo   Scrape Instagram ^| Download via Telegram ^| Post Reels
echo  ============================================================
echo.

:: ── Step 1: Pull latest code ────────────────────────────────────
echo  [1/4] Pulling latest code...
git pull origin claude/tiktok-scraper-tool-hXD41
echo.

:: ── Step 2: Extract BlueStacks token ────────────────────────────
echo  [2/4] Extracting BlueStacks token (Instagram real device auth)...
echo        Make sure BlueStacks is open + Instagram is logged in.
echo.
py extract_token.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [!] BlueStacks token extraction failed.
    echo  [!] Continuing without it — will use instagrapi session instead.
    echo      To fix: open BlueStacks, log into Instagram, enable ADB, re-run.
    echo.
    timeout /t 3 /nobreak >nul
)
echo.

:: ── Step 3: Scrape content ───────────────────────────────────────
echo  [3/4] Scraping Instagram Reels via Telegram bot...
echo        This downloads 200 videos to tiktok_videos\motion\
echo        Press Ctrl+C to skip scraping and go straight to posting.
echo.
py instagram_scraper.py --amount 200
echo.
echo  [3/4] Scrape complete.
echo.

:: ── Step 4: Run the poster ───────────────────────────────────────
echo  [4/4] Starting Fader v2 poster (@dumbmoneyonsolana)...
echo        Posting from tiktok_videos\motion\
echo        Press Ctrl+C to stop at any time.
echo.
py fader_reels.py

echo.
echo  Pipeline stopped.
pause
