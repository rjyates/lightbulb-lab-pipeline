# Worker setup: an always-on laptop

[Operations](../operations.md) · [Proposal, section 8.2](../autonomy/proposal.md#82-running-the-worker-on-a-laptop)

The worker renders, checks and schedules videos every night. It needs Linux, because rendering uses `fork`. These steps assume Ubuntu 24.04 or later on a laptop that stays plugged in.

## 1. Make the laptop a server

1. Install Ubuntu with **full-disk encryption** (an installer option) and enable automatic security updates.
2. Keep it running with the lid closed. In `/etc/systemd/logind.conf`, set:
   ```text
   HandleLidSwitch=ignore
   HandleLidSwitchExternalPower=ignore
   ```
   Then run `sudo systemctl restart systemd-logind`.
3. Stop it from sleeping:
   ```bash
   sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
   ```
4. **Battery:** if the firmware or vendor tool supports a charge limit (often 80%), turn it on. A battery held at 100% around the clock wears out quickly.
5. **Power loss:** if the BIOS has "power on after AC loss", enable it.
6. **Remote access:** install `openssh-server`, use key-based login, and turn off password login.

## 2. Install the pipeline

```bash
git clone https://github.com/rjyates/lightbulb-lab-pipeline.git
git clone https://github.com/rjyates/lightbulb-lab-ops.git   # private: sign in with `gh auth login` or a deploy key first
cd lightbulb-lab-pipeline && bash install.sh
```

`install.sh` installs FFmpeg, espeak-ng, the Python environment and the free Kokoro voice. It also adds the nightly timer, but **does not start it**.

## 3. Configure

Edit `config.env` (it holds credentials and stays out of Git):

| Setting | Value |
| :--- | :--- |
| `LBL_VOICE`, `KOKORO_VOICE` | `kokoro`, plus the blend you picked from the voice samples |
| `NTFY_TOPIC` | A long, unguessable topic you subscribe to in the ntfy app |
| `LBL_OPS_REPO` | Path to the `lightbulb-lab-ops` checkout |
| `LBL_QUEUE`, `LBL_LEDGER` | `<ops repo>/ledger/queue.json` and `<ops repo>/ledger/videos.jsonl` |
| `YOUTUBE_UPLOAD` | `false` until step 4 is done |

## 4. Connect YouTube (owner only)

1. In Google Cloud Console, download the OAuth client file to `secrets/client_secret.json`. Set the consent screen to **In production**; in "Testing", sign-ins expire after 7 days.
2. Sign in once. From another computer, open a tunnel and run:
   ```bash
   ssh -L 8765:localhost:8765 you@worker
   ```
   Then, on the worker:
   ```bash
   .venv/bin/python -m lightbulb.youtube auth
   ```
   Open the printed link in your own browser.
3. Find the playlist ID with `.venv/bin/python -m lightbulb.youtube playlists` and set `YOUTUBE_PLAYLIST_ID`.
4. Set `YOUTUBE_UPLOAD=true`.

Until Google approves the API audit, uploads stay private even when scheduled. The worker still runs the whole schedule, so you can watch it work before videos go public.

## 5. Test, then start

```bash
.venv/bin/python -m lightbulb.check            # scripts and asset manifest
.venv/bin/python -m pytest -q                  # needs: .venv/bin/pip install pytest
.venv/bin/python -m lightbulb.weekly --quick   # 3-scene render through the voice and the quality gates; no upload
.venv/bin/python -m lightbulb.worker --plan    # next slots and episodes; renders nothing
sudo systemctl enable --now lightbulb-worker.timer
```

## Everyday control

| To | Do |
| :--- | :--- |
| See the schedule | `.venv/bin/python -m lightbulb.worker --plan` |
| Pause everything | `touch output/PAUSE`. Nothing new is made, and anything due within 48 hours is kept private. Remove the file to resume. |
| Stop one episode | `touch output/veto/<episode id>` at least 48 hours before it goes live |
| Read the logs | `journalctl -u lightbulb-worker --since today` |
| Stop the timer | `sudo systemctl disable --now lightbulb-worker.timer` |

If you change `LBL_OUTPUT`, the `PAUSE` and `veto/` paths move with it.

## What it does each night

1. Pulls the latest pipeline code (`main`) and the ops repo.
2. **Recheck:** for anything going live within 48 hours, keeps it private if publishing is paused, the episode is vetoed, or one of its facts expires before the publish date.
3. Marks videos whose slots have passed as published.
4. For each series, renders, checks and schedules the next approved scripts until it is booked three weeks ahead. Long-form: Tuesday (Tech from Scratch) and Friday (Fix It Friday) at 9:00 Central. Shorts: the next two days.
5. Commits the queue and upload record to the ops repo, and sends ntfy alerts only for problems.

**Security note:** the worker runs whatever is on `main`. Until signed releases are in place (proposal section 4.2), only the owner should merge to `main`.
