# Lightbulb Lab pipeline — agent instructions

Python pipeline that turns structured episode scripts (`episodes/`) into narrated animation, short-form clips, thumbnails, captions and publishing metadata. Operations and configuration: `docs/operations.md`.

## Commands
- Setup: create a virtual environment and install `requirements.txt`.
- Validate scripts (safe, offline): `python -m lightbulb.check`
- Describe the workflow without running it: `python -m lightbulb.weekly --dry-run`

## Cost and external-action guardrails
- Do NOT run voice generation (ElevenLabs), full renders, YouTube uploads, notifications, or install/enable systemd timers without explicit approval. Voice generation consumes paid credits; uploads publish publicly.
- Never read or print `config.env` or any real credentials; document new settings in `config.example.env`.
- Treat `legacy/` as reference only unless asked.

## Working conventions
- Branch per change. Run `python -m lightbulb.check` before committing.
- Keep episode JSON schema changes backward compatible or migrate all bundled episodes in the same change.
- This repo is private (public until 2026-10-28), but keep it shareable: no personal data, keys or channel credentials.
