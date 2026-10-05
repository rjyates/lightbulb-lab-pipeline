#!/usr/bin/env bash
# One-time setup on Ubuntu:  bash install.sh
set -euo pipefail
cd "$(dirname "$0")"
sudo apt-get update && sudo apt-get install -y ffmpeg python3-venv python3-pip
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
[ -f config.env ] || cp config.example.env config.env
mkdir -p secrets output
DIR="$(pwd)"; ME="$(whoami)"
sed -e "s#__DIR__#$DIR#g" -e "s#__USER__#$ME#g" systemd/lightbulb-weekly.service | sudo tee /etc/systemd/system/lightbulb-weekly.service >/dev/null
sudo cp systemd/lightbulb-weekly.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now lightbulb-weekly.timer
echo
echo "Installed. Next: edit config.env (nano config.env), then test with:"
echo "  .venv/bin/python -m lightbulb.weekly --dry-run"
systemctl list-timers lightbulb-weekly.timer --no-pager || true
