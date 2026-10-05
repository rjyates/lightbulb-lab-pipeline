# Lightbulb Lab pipeline

Every Sunday morning your server takes the next script in `episodes/`, has Kip read it (ElevenLabs),
animates the full episode plus Shorts, makes the thumbnail, and pings your phone. Monday you review and publish.

Costs nothing: ElevenLabs free plan (~10,000 characters/month, each episode is ~1,300–1,800),
YouTube API (free), ntfy (free), everything else is open source.

## What you get each Sunday
A folder in `output/` like `output/ep02-hardware-vs-software/`:
- `ep02-hardware-vs-software.mp4`: the episode (1080p)
- `short1-....mp4`, `short2-....mp4`: vertical clips for YouTube Shorts and TikTok
- `...-thumbnail.jpg`, `...en.srt` (captions)
- `UPLOAD-ME.txt`: title, description, tags and settings to paste

Once YouTube upload is switched on (below), the episode and Shorts also land in YouTube Studio as **private** drafts.

## One-time setup on the Ubuntu server
```bash
git clone https://github.com/rjyates/lightbulb-lab-pipeline.git
cd lightbulb-lab-pipeline
bash install.sh          # installs ffmpeg + Python packages, sets up the Sunday timer
nano config.env          # paste your keys (see below)
.venv/bin/python -m lightbulb.check        # checks the scripts
.venv/bin/python -m lightbulb.weekly --dry-run
```
The repo is private, so the server needs permission to clone/pull: easiest is `sudo apt install gh && gh auth login`.
The Sunday job runs `git pull` first, so new scripts you push show up automatically.

### 1. ElevenLabs (Kip's voice)
1. elevenlabs.io → profile icon → **API Keys** → Create. Paste it as `ELEVENLABS_API_KEY`.
2. **Voices** → Kip → ⋯ → **Copy voice ID** → `ELEVENLABS_VOICE_ID`.
3. Free-plan note: free voices are for non-commercial use and need credit (the description already credits ElevenLabs).
   Before the channel is monetized you'll need a paid plan (Starter) for commercial rights.

Out of credits that month? Record the script on the ElevenLabs website, save it as `episodes/audio/ep02.mp3`,
and the pipeline uses that file instead (timing is worked out from the pauses).

### 2. Phone notification (optional, free)
Install the **ntfy** app, subscribe to a long random topic name, put the same name in `NTFY_TOPIC`.

### 3. YouTube drafts (optional, later)
Until this is on, you upload the folder by hand Monday (5 minutes).
1. console.cloud.google.com → new project → enable **YouTube Data API v3**.
2. OAuth consent screen: External, add your Lightbulb Lab Google account as a test user.
3. Credentials → Create OAuth client ID → **Desktop app** → download JSON → save as `secrets/client_secret.json` on the server.
4. Sign in once: from your laptop `ssh -L 8765:localhost:8765 you@server`, then on the server
   `.venv/bin/python -m lightbulb.youtube auth` and open the link on your laptop.
5. Important: YouTube locks every video uploaded by an un-audited API project to private forever.
   Apply for the free audit (search "YouTube API Services audit and quota extension form"). After approval set `YOUTUBE_UPLOAD=true`.
6. `.venv/bin/python -m lightbulb.youtube playlists` → copy the Tech from Scratch ID into `YOUTUBE_PLAYLIST_ID`.

## Everyday commands
| Do this | Command |
|---|---|
| Check scripts | `.venv/bin/python -m lightbulb.check` |
| Run this week's episode now | `sudo systemctl start lightbulb-weekly` |
| Watch it work | `journalctl -u lightbulb-weekly -f` |
| Make one specific episode | `.venv/bin/python -m lightbulb.weekly --episode ep03` |
| Cheap test (3 scenes, ~300 credits) | `.venv/bin/python -m lightbulb.weekly --quick` |
| When it runs next | `systemctl list-timers lightbulb-weekly.timer` |

Change the day/time in `systemd/lightbulb-weekly.timer`, then rerun `bash install.sh`.
Rendering takes roughly (video seconds × 7 ÷ CPU cores) seconds: a 2-minute episode on 4 cores ≈ 4 minutes, plus Shorts.

## Adding episodes
Write `episodes/epNN-title.json` (see `episodes/FORMAT.md`), run the checker, commit, push.
Episodes run in number order; ones with `"status": "draft"` are skipped. Finished ones are tracked in `output/state.json`.

## Layout
`lightbulb/` code (engine = timeline, cards = explainer cards, characters/room = art, video = render, weekly = the Sunday job) ·
`assets/` fonts, music, sound effects, brand sheet · `legacy/` the hand-built Episode 1 code.
Music: "Nebula" by The Grey Room / Density & Time (YouTube Audio Library). Keep this repo private.
