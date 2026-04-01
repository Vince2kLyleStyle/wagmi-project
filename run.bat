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
echo  How do you want to post today?
echo.
echo    [1] BlueStacks poster (recommended — real app taps, undetectable)
echo    [2] API poster (faster setup, instagrapi)
echo.
set /p MODE="  Enter 1 or 2: "
echo.

:: ── Step 1: Pull latest code ────────────────────────────────────
echo  [1/4] Pulling latest code...
git pull origin claude/tiktok-scraper-tool-hXD41
echo.

:: ── Step 2: Install/update packages ─────────────────────────────
echo  [2/4] Checking packages...
pip install -r requirements.txt -q
echo  Packages OK.
echo.

:: ── Step 3: Pre-flight check ─────────────────────────────────────
echo  [3/4] Running pre-flight check...
echo.
py check.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [!!] Pre-flight check failed. Fix the issues above and re-run.
    pause
    exit /b 1
)
echo.

:: ── Step 4: Scrape content ───────────────────────────────────────
echo  [4/4] Scraping fresh content...
echo.
py instagram_scraper.py --amount 200
echo.

:: ── Step 5: Post ─────────────────────────────────────────────────
if "%MODE%"=="1" (
    echo  Starting BlueStacks poster...
    echo  Make sure BlueStacks is open with Instagram logged in.
    echo.
    py bluestacks_poster.py
) else (
    echo  Starting API poster...
    echo.
    py extract_token.py
    if %ERRORLEVEL% NEQ 0 (
        echo  [~] No BlueStacks token — using instagrapi session.
        timeout /t 2 /nobreak >nul
    )
    py fader_reels.py
)

echo.
echo  Pipeline stopped.
pause
