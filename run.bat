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
echo  [1/5] Pulling latest code...
git pull origin claude/tiktok-scraper-tool-hXD41
echo.

:: ── Step 2: Install/update packages ─────────────────────────────
echo  [2/5] Checking packages...
pip install -r requirements.txt -q
echo  Packages OK.
echo.

:: ── Step 3: Pre-flight check ─────────────────────────────────────
echo  [3/5] Running pre-flight check...
echo.
py check.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [!!] Pre-flight check failed. Fix the issues above and re-run.
    pause
    exit /b 1
)
echo.

:: ── Step 4: Extract BlueStacks token (optional) ──────────────────
echo  [4/5] Trying BlueStacks token extraction...
echo        (Skip this step with Ctrl+C if BlueStacks is not set up yet)
echo.
py extract_token.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [~] No BlueStacks token — continuing with instagrapi session.
    echo.
    timeout /t 2 /nobreak >nul
)
echo.

:: ── Step 5: Scrape + Post ────────────────────────────────────────
echo  [5/5] Starting scraper + poster...
echo.
echo  --- SCRAPING (accounts + hashtags) ---
py instagram_scraper.py --amount 200
echo.
echo  --- POSTING ---
py fader_reels.py

echo.
echo  Pipeline stopped.
pause
