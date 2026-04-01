@echo off
title Motion Bot — First Time Setup
cd /d "%~dp0"
color 0E

echo.
echo  ============================================================
echo   MOTION BOT — First Time Setup
echo   Run this ONCE before using run.bat for the first time
echo  ============================================================
echo.
echo  This will log you into Telegram so the scraper can
echo  send Instagram URLs to your download bot.
echo.
echo  You'll need:
echo    - Your Telegram phone number
echo    - The auth code Telegram sends you
echo.
pause

py tiktok_scraper.py --telegram-login

echo.
echo  ============================================================
echo   Setup complete! You can now run run.bat
echo  ============================================================
echo.
pause
