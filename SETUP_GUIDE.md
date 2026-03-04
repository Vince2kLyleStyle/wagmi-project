# Fader v2 — Setup & Run Guide

## Quick Start (5 minutes)

### 1. Install Python Dependencies

```bash
pip install instagrapi Pillow
```

### 2. Install FFmpeg (optional but recommended)

FFmpeg lets the bot extract random thumbnail frames so each Reel looks unique.

**Windows:**
1. Download from https://ffmpeg.org/download.html (pick "Windows builds")
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system PATH
4. Verify: `ffmpeg -version`

If you skip this, set `USE_FFMPEG_THUMBNAIL = False` in `config.py`.

### 3. Prepare Videos

Put your `.mp4` files in the `tiktok_videos/` folder:

```
wagmi-project/
├── tiktok_videos/
│   ├── video (1200).mp4
│   ├── video (1201).mp4
│   └── ... (up to thousands)
├── fader_reels.py
├── config.py
└── ...
```

### 4. First Login (creates session.json)

```bash
# Set credentials via environment variables (recommended)
set IG_USERNAME=your_username
set IG_PASSWORD=your_password
python fader_reels.py

# OR pass username directly (will prompt if password is in config.py)
python fader_reels.py --username your_username
```

On first run the bot will:
1. Log in and save `sessions/your_username_session.json`
2. Run a 30-60 min warm-up (browsing, liking, viewing stories)
3. Start uploading

**If you hit a challenge/captcha on first login:**
- Log in manually on the real Instagram app first
- Complete any verification (SMS, email)
- Then run the bot again — it should work

### 5. Resume Later

The bot saves session state. Just run it again:

```bash
python fader_reels.py
```

It will resume from the existing session and skip already-uploaded videos
(because they were deleted after success).

---

## Multi-Account Setup

### 1. Create accounts.json

```json
[
    {
        "username": "account1",
        "password": "pass1",
        "video_dir": "tiktok_videos/account1",
        "daily_cap": 10
    },
    {
        "username": "account2",
        "password": "pass2",
        "video_dir": "tiktok_videos/account2",
        "daily_cap": 12
    },
    {
        "username": "account3",
        "password": "pass3",
        "video_dir": "tiktok_videos/account3",
        "daily_cap": 8
    }
]
```

### 2. Organize Videos Per Account

```
tiktok_videos/
├── account1/
│   ├── video1.mp4
│   └── ...
├── account2/
│   ├── video1.mp4
│   └── ...
└── account3/
    ├── video1.mp4
    └── ...
```

### 3. Run

```bash
python multi_account.py
```

The runner cycles through all accounts, runs a full daily session on each,
then sleeps until the next morning and repeats.

---

## Command-Line Options

```
python fader_reels.py [OPTIONS]

  --username, -u    Override IG username
  --session, -s     Path to a specific session.json
  --skip-warmup     Skip the 30-60 min warm-up phase
  --daily-cap N     Override daily upload limit
```

---

## Configuration (config.py)

All tunables live in `config.py`. Key settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `DAILY_MIN` / `DAILY_MAX` | 8 / 15 | Random daily cap range |
| `BATCH_SIZE` | 3 | Videos per mini-batch |
| `INTRA_BATCH_MIN/MAX` | 40s / 90s | Delay between videos in a batch |
| `INTER_BATCH_CENTER` | 3600s (60m) | Gaussian center for batch gaps |
| `REFRESH_EVERY_N_POSTS` | 25 | Re-login & rotate fingerprint every N |
| `DELETE_AFTER_UPLOAD` | True | Delete .mp4 after successful upload |
| `USE_FFMPEG_THUMBNAIL` | True | Extract random frame as thumbnail |

---

## Anti-Ban Manual Tips (Free)

These are things you should do **manually** alongside the bot to maximize survival:

### Account Warming (Before Starting the Bot)
1. **Use the account manually for 3-7 days** before any automation
2. Post 1-2 Reels manually per day during warm-up
3. Follow 10-20 accounts in your niche, like/comment on posts
4. Complete your profile: bio, profile pic, 6-9 grid posts, story highlights
5. Link a phone number and email for verification

### During Bot Operation
1. **Monitor reach daily** — if reach drops >50%, pause the bot for 24-48 hours
2. **Manually engage** for 10-15 min/day (like, comment, reply to DMs)
3. **Never run on public WiFi** — use your home IP consistently
4. **Don't run other automation tools** simultaneously
5. **Check for "Action Blocked" messages** in the app — if you see one, pause immediately

### Content Tips for Growth
1. **Use trending audio** — add popular sounds to your Reels before uploading
2. **First 3 seconds matter** — hook the viewer immediately
3. **Optimal length**: 7-15 seconds for highest completion rate
4. **Post at peak hours** (configure bot start time): 9 AM, 12 PM, 5 PM, 8 PM local
5. **Niche consistency** — don't mix random content; pick one theme

### If You Get Shadowbanned
1. Stop ALL automation immediately
2. Don't post for 48-72 hours
3. Use the account normally (browse, like, comment) for a week
4. Resume manual posting first, then bot at lower volume (5-8/day)

### IP & Network Tips (Free)
1. **Your home IP is fine** for 1-2 accounts
2. For 3+ accounts, consider cycling between home WiFi and mobile hotspot
3. Don't use VPNs — Instagram flags datacenter IPs
4. If your ISP gives you a dynamic IP, restart your router between account sessions

---

## Realistic Expectations & Warnings

### What to Expect
- **Single account, 10-12 Reels/day**: Can reach 5,000-10,000 followers in 1-3 weeks IF content is good and gets algorithmic pickup
- **Multi-account (3 accounts), 8-10/day each**: Higher total reach but shared IP risk
- **Account lifespan**: With full humanization, expect 1-3 weeks before Instagram starts restricting. This is dramatically better than the old Fader (which got banned in days)

### Hard Truths
1. **Single residential IP limits you** — Instagram tracks how many accounts operate from one IP. More than 2-3 accounts from one IP will eventually get flagged
2. **instagrapi is a cat-and-mouse game** — Instagram updates their private API regularly. Keep instagrapi updated (`pip install --upgrade instagrapi`)
3. **Shadowbans are real** — After 1-2 weeks at 10+/day, expect reduced reach. This is why the strategy is "sprint then stop"
4. **Challenges will happen** — You'll likely need to manually solve 1-2 challenges per week. Keep the Instagram app handy on your phone
5. **Content quality > volume** — 10 good Reels/day beats 60 bad ones. The algorithm rewards watch time and shares, not just post count
6. **No guarantees** — This is designed to survive as long as possible, but Instagram can and will ban automation accounts. Only use accounts you're prepared to lose

### The Sprint Strategy
The recommended approach:
1. **Week 0**: Warm account manually (3-7 days)
2. **Weeks 1-2**: Run bot at 8-12 Reels/day with full humanization
3. **If you hit 10K**: Stop automation, switch to manual posting
4. **If account gets restricted**: Pause 48h, lower volume, or switch to backup account
5. **After 2 weeks**: Disable bot regardless, switch to manual to preserve the account
