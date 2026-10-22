# Operations and configuration

[Overview](../README.md) · [Episode format](../episodes/FORMAT.md)

## Local configuration

Use `config.example.env` as a reference for local `config.env`. Never commit actual keys or OAuth files. The configuration loader also accepts supported environment variables.

- Narration: `ELEVENLABS_*` settings or a supplied audio file.
- Publishing: `YOUTUBE_*` settings and local OAuth credentials; upload defaults off in the configuration loader.
- Notifications: optional `NTFY_*` settings.
- Output/workers: `LBL_*` settings.

This guide intentionally does not reproduce credentials, notification destinations, or account identifiers.

## Commands

| Intent | Command |
| :--- | :--- |
| Validate scripts | `python -m lightbulb.check` |
| Inspect selection without rendering | `python -m lightbulb.weekly --dry-run` |
| Render a specific episode | `python -m lightbulb.weekly --episode ep03` |
| Short render test | `python -m lightbulb.weekly --quick` |

The last two commands may call the configured narration service. The orchestration CLI can also send a configured notification on a no-work or error path, including when a dry-run cannot select an episode. Confirm configuration, provider capacity, and intended external effects before running them.

`links.json` supplies website/guide metadata. Generated outputs and completion state belong in the configured output folder; moving/deleting state can affect which episode is selected next.

## Scheduling is optional

`install.sh` and `systemd/` describe the original Linux deployment. Read them before use: installation can create a virtual environment, install system packages, and enable a recurring job. No scheduler was installed or changed in this pass.

Use service logs and timer state on the actual host to establish operational status. The existence of a timer file or a dated report in Git does not prove that current rendering, uploads, or notifications work.

## Verification limits

The episode checker completed with 17 `ok` entries and no `FAIL` entries on October 22, 2026. This does not validate voice availability, FFmpeg output quality, external account permissions, scheduling, or publication. Existing runtime reports were not treated as proof of current availability.
