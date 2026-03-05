@echo off
title Instagram Poster — @dumbmoneyonsolana
cd /d "%~dp0"
echo.
echo   Starting Instagram Poster (@dumbmoneyonsolana)...
echo   Videos from: tiktok_videos\trading\
echo   Press Ctrl+C to stop.
echo.
py fader_reels.py
pause
