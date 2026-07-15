# Complete Migration Guide: Moving Everything to Old Laptop

## Executive Summary
You're moving TWO major automated systems from a portable laptop to a home machine:
1. **WAGMI Trading Bot** — autonomous crypto trading with Claude AI multi-agent decision making
2. **wagmi-project Instagram Automation** — posts Reels via BlueStacks using ADB+uiautomator tap commands

Both are currently running on the portable and need to move to the old laptop (C:\Projects\) to run 24/7. The portable will become a dev/control hub only.

---

## Part 1: Code Migration (Easy)

### 1.1 Clone Both Projects from GitHub

On the old laptop, in PowerShell:

```powershell
cd C:\Projects

# Clone trading bot
git clone https://github.com/Vince2kLyleStyle/WAGMI.git
cd WAGMI
git checkout main

# Clone Instagram automation
cd ..
git clone https://github.com/Vince2kLyleStyle/wagmi-project.git
cd wagmi-project
git checkout claude/tiktok-scraper-tool-hXD41

cd ..
```

Both repos are now on the old laptop at C:\Projects\WAGMI\ and C:\Projects\wagmi-project\.

### 1.2 Copy .env Files (Required — NOT in GitHub)

These contain API keys and secrets. Copy from the portable laptop to the old one:

**For WAGMI:**
```
From: C:\Users\vince\WAGMI PROJECT\WAGMI\.env
To:   C:\Projects\WAGMI\.env
```

**For wagmi-project:**
```
From: C:\Users\vince\wagmi-project\.env
To:   C:\Projects\wagmi-project\.env
```

---

## Part 2: WAGMI Trading Bot Setup

### 2.1 Python & Dependencies

```powershell
cd C:\Projects\WAGMI

# Check Python version (need 3.10+)
python --version

# Create virtual environment (if not already there)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2.2 Verify .env File

Open C:\Projects\WAGMI\.env and confirm:
- `ANTHROPIC_API_KEY` is set (Claude API key)
- `ENVIRONMENT=paper` (for paper trading, safe mode)
- `LLM_MULTI_AGENT=true` (enables the 9-agent specialist system)

### 2.3 Test It

```powershell
cd C:\Projects\WAGMI\bot
python run.py paper
```

Expected output:
- Bot starts, loads agents, begins signal generation
- Logs to C:\Projects\WAGMI\bot\data\
- Papers trades logged to trades.csv

Press Ctrl+C to stop. If it runs, you're good.

---

## Part 3: wagmi-project Instagram Automation Setup

### 3.1 System Requirements (Install These First)

#### A. ADB (Android Debug Bridge)
Android's command-line tool for controlling emulated devices. The Instagram automation uses ADB to:
- Connect to BlueStacks emulator
- Dump the Android UI hierarchy (uiautomator)
- Send tap commands to the emulated device

**Status on your portable**: Already installed at C:\platform-tools\platform-tools\adb.exe

**To install on old laptop:**
```powershell
# Option 1: Using winget (automatic)
winget install Google.PlatformTools

# Option 2: Manual
# Download from: https://developer.android.com/tools/releases/platform-tools
# Extract to: C:\platform-tools\
# Add to PATH: Control Panel → System → Environment Variables → Path → Add C:\platform-tools\
```

**Verify it works:**
```powershell
adb --version
```

Should output: "Android Debug Bridge version X.X.XX"

#### B. BlueStacks 5 (Android Emulator)
Runs a full Android OS on your PC, allowing Instagram to be installed and controlled via ADB.

**Download & Install:**
1. Go to https://www.bluestacks.com/
2. Download BlueStacks 5 (not Nougat or other versions)
3. Install (standard Windows installer — may prompt for Google account login, that's normal)
4. Launch BlueStacks and wait for full startup (~2 min first time)

**Inside BlueStacks, enable ADB:**
1. Click ⚙️ Settings (gear icon, top-right)
2. Go to "Advanced" tab
3. Find "Android Debug Bridge" toggle
4. Turn it ON
5. Close settings

**Install Instagram:**
1. Click Play Store icon in BlueStacks
2. Search for "Instagram"
3. Install official Instagram app
4. Log in with your bot account (must match accounts.json username/password)
5. Once logged in, LEAVE IT RUNNING in the background

### 3.2 Python & Dependencies

```powershell
cd C:\Projects\wagmi-project

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Key packages installed:
# - instagrapi (Instagram private API fallback)
# - pillow (image processing)
# - telethon (Telegram bot integration)
# - pygetwindow (window detection)
# - pynput (keyboard simulation for paste operations)
```

### 3.3 Configure accounts.json

This file tells the automation which accounts to post to and where videos are stored.

**Location:** C:\Projects\wagmi-project\accounts.json

**Format (multi-niche example):**
```json
{
  "niches": {
    "trading": {
      "username": "your_instagram_handle_1",
      "password": "your_password_1",
      "video_dir": "tiktok_videos/trading",
      "daily_cap": 12
    },
    "memecoin": {
      "username": "your_instagram_handle_2",
      "password": "your_password_2",
      "video_dir": "tiktok_videos/memecoin",
      "daily_cap": 8
    }
  }
}
```

**Key fields:**
- `username`: Instagram account handle (the account must be logged into BlueStacks)
- `password`: Instagram password (or app-specific password if 2FA enabled)
- `video_dir`: Folder where Reels videos are stored (relative to project root)
- `daily_cap`: Max posts per account per day

### 3.4 Prepare Video Directories

Create the folder structure for videos:

```powershell
cd C:\Projects\wagmi-project

# Create folders
mkdir tiktok_videos\trading
mkdir tiktok_videos\memecoin
# (or whatever niches you defined in accounts.json)

# Put .mp4 files in the appropriate folders
# Example: C:\Projects\wagmi-project\tiktok_videos\trading\video1.mp4
```

### 3.5 Test the Scraper

Before posting, test the scraper (it's safer):

```powershell
cd C:\Projects\wagmi-project
.\venv\Scripts\Activate.ps1

# Scrape 5 Reels from Instagram Explore
python bluestacks_scraper.py --amount 5 --skip-own

# Expected:
# - Opens Instagram Reels in BlueStacks
# - Taps to load each reel
# - Copies link to clipboard
# - Sends to Telegram bot (if configured)
# - Logs to ig_scraped.txt
```

### 3.6 Test the Poster

Test posting ONE video (dry-run first, no actual upload):

```powershell
cd C:\Projects\wagmi-project
.\venv\Scripts\Activate.ps1

# Dry-run: prepares everything but stops before Share tap
python bluestacks_poster.py --once --dry-run

# If that works, actually post one:
python bluestacks_poster.py --once
```

**Expected flow:**
1. Reads first video from tiktok_videos/[niche]/
2. Pushes to BlueStacks via ADB
3. Launches Instagram
4. Navigates: + button → Reels → Select video → Next
5. Dismisses popups (confirms selection, etc.)
6. Caption screen: types caption
7. Share button: posts
8. Logs success to file
9. Deletes local video

If you see: "Upload confirmed ✓" → it worked.

### 3.7 Run Continuously (For Production)

Once tested, run the poster in a loop:

```powershell
cd C:\Projects\wagmi-project
.\venv\Scripts\Activate.ps1

# Posts continuously (respects daily_cap, pauses between posts)
python bluestacks_poster.py
```

This will:
- Post videos on schedule (e.g., 3 posts every 30 minutes)
- Respect daily cap per account
- Log all posts to success.txt
- Handle errors gracefully (screenshots failures for debugging)

---

## Part 4: How the Code Actually Works (Understanding the Automation)

### Instagram Posting Flow (uiautomator + ADB)

The code doesn't use Windows mouse clicks or external browser APIs. Instead:

1. **Push video to BlueStacks** via ADB:
   ```
   adb push C:\Projects\wagmi-project\tiktok_videos\trading\video.mp4 /sdcard/DCIM/
   ```

2. **Trigger media scanner** so Instagram sees the new video:
   ```
   adb shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/DCIM/video.mp4
   ```

3. **Launch Instagram app**:
   ```
   adb shell am start -n com.instagram.android/com.instagram.android.activity.MainTabActivity
   ```

4. **Find UI elements dynamically** using uiautomator:
   - Dump the Android UI hierarchy: `adb shell uiautomator dump /sdcard/uidump.xml`
   - Parse the XML to find element coordinates by text or content-description
   - Example: Find "+ button" by looking for `content-desc="Create"`

5. **Tap elements** using ADB input command:
   ```
   adb shell input tap 500 1200    # tap at coordinates (500, 1200)
   ```

6. **Type text** (for captions):
   ```
   adb shell input text "Your caption here"
   # (with unicode/special char handling via clipboard paste via ADB)
   ```

7. **Wait intelligently**:
   - Screenshots before/after each action (for debugging)
   - Checks for popup dismissal
   - Polls for "Share succeeded" confirmation

**Why this approach?**
- **No detection risk**: Looks like a real Android device, not automation
- **Reliable**: Doesn't depend on Instagram API (which they block)
- **Observable**: Uiautomator finds elements by UI text, survives app updates
- **Debuggable**: Screenshots let you see exactly what it's doing

### Instagram Scraping Flow (Similar)

The scraper (`bluestacks_scraper.py`):
1. Swipes through Reels on Instagram Explore
2. For each reel, taps Share → Copy Link
3. Reads clipboard (via PowerShell `Get-Clipboard`)
4. Sends URL to Telegram bot for downloading (removes watermarks)
5. Saves clean video to tiktok_videos/
6. Repeats

---

## Part 5: Running Everything on Startup (Optional)

To make both run automatically when the old laptop starts:

### Create a launcher script

**File:** C:\Projects\start_all_automations.bat

```batch
@echo off
REM Start WAGMI Trading Bot in one window
start "WAGMI Trading Bot" /min cmd /k "cd C:\Projects\WAGMI\bot && python run.py paper"

REM Wait 5 seconds
timeout /t 5 /nobreak

REM Start Instagram Poster in another window
start "Instagram Poster" /min cmd /k "cd C:\Projects\wagmi-project && python bluestacks_poster.py"

echo.
echo Both automations launched. Check their windows for status.
pause
```

### Add to Windows Startup

1. Press Win+R, type `shell:startup`
2. Create shortcut to `C:\Projects\start_all_automations.bat`
3. On next boot, both will launch automatically

---

## Part 6: Monitoring & Troubleshooting

### Check WAGMI Status
```powershell
cd C:\Projects\WAGMI
tail -f bot/data/trades.csv            # Live trades
tail -f bot/data/bot.log               # Errors/decisions
cat bot/data/signal_outcomes.jsonl     # All signals generated
```

### Check Instagram Poster Status
```powershell
cd C:\Projects\wagmi-project
tail -f success.txt                    # Posted videos
tail -f bluestacks_poster_err.log      # Errors
ls -lrt debug_*.png | tail -5          # Latest debug screenshots
```

### Common Issues

| Issue | Fix |
|---|---|
| "adb: command not found" | ADB not on PATH. Reinstall platform-tools, add C:\platform-tools to PATH |
| "unable to connect to 127.0.0.1:5555" | BlueStacks not running or ADB disabled. Start BlueStacks, enable ADB in settings |
| "Instagram blank screen" | Account not logged in. Log in manually inside BlueStacks, stay on home screen |
| "timeout waiting for element" | UI changed or app crashed. Check screenshot, manually verify Instagram is still open |
| "Upload confirmed but no video on profile" | Account flagged for spam. Wait 24h or use different account |

---

## Part 7: Remote Control from Portable Laptop

From the portable (which becomes the dev hub):

```powershell
# SSH into old laptop (if configured)
ssh user@old-laptop-ip

# Or use Claude Code remote control feature:
# File → Connect to Remote → [old laptop IP]

# Then monitor/manage everything:
cd C:\Projects\WAGMI
git status                           # See latest trades
git log --oneline -5                 # Recent commits

cd ..\wagmi-project
tail -f success.txt                  # Watch posts happen in real-time
```

---

## Checklist Before Running

- [ ] Both repos cloned to C:\Projects\
- [ ] Both .env files copied
- [ ] Python 3.10+ installed
- [ ] ADB installed and on PATH (`adb --version` works)
- [ ] BlueStacks 5 installed and running
- [ ] Instagram app installed in BlueStacks
- [ ] Bot account logged into Instagram
- [ ] ADB enabled in BlueStacks settings (⚙️ → Advanced → Android Debug Bridge → ON)
- [ ] accounts.json configured with your niche(s)
- [ ] Video directories created with test .mp4 files
- [ ] Test run successful (at least one post or scrape)
- [ ] WAGMI paper trading tested
- [ ] Both systems running on schedule

---

## That's It

Everything on the old laptop, both systems automated, portable is now just a dev/control hub. Questions? Read the code docstrings or check the .claude/rules/ docs in each project.

Good luck.
