@echo off
title TikTok Scraper — Trading Niche
cd /d "%~dp0"
echo.
echo   Starting TikTok Scraper (trading niche)...
echo   Press Ctrl+C to stop.
echo.
py tiktok_scraper.py --niche trading --no-headless
pause
