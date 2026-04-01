@echo off
title Instagram Scraper — Motion Niche
cd /d "%~dp0"
echo.
echo   Starting Instagram Reel Scraper (motion niche)...
echo   Downloads via Telegram bot — no watermarks
echo   Press Ctrl+C to stop.
echo.
py instagram_scraper.py --amount 200
pause
