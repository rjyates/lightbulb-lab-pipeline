#!/usr/bin/env bash
# One-time setup of the worker on Ubuntu:  bash install.sh
# Installs everything and the nightly timer, but does not start it: see docs/runbooks/worker-setup.md.
set -euo pipefail
cd "$(dirname "$0")"
sudo apt-get update && sudo apt-get install -y ffmpeg espeak-ng git python3-venv python3-pip
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements-voice.txt
[ -f config.env ] || cp config.example.env config.env
chmod 600 config.env
mkdir -p secrets output && chmod 700 secrets
DIR="$(pwd)"; ME="$(whoami)"
sed -e "s#__DIR__#$DIR#g" -e "s#__USER__#$ME#g" systemd/lightbulb-worker.service | sudo tee /etc/systemd/system/lightbulb-worker.service >/dev/null
sudo cp systemd/lightbulb-worker.timer /etc/systemd/system/
sudo systemctl daemon-reload
echo
echo "Installed. Next steps (docs/runbooks/worker-setup.md):"
echo "  1. Edit config.env"
echo "  2. .venv/bin/python -m lightbulb.worker --plan"
echo "  3. sudo systemctl enable --now lightbulb-worker.timer"
