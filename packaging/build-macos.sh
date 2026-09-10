#!/usr/bin/env bash
set -euo pipefail

export PYINSTALLER_CONFIG_DIR="${PWD}/.pyinstaller-cache"
python3 -m pip install ".[dev]"
python3 -m pytest
python3 -m PyInstaller --clean --noconfirm teams-backup.spec
cp packaging/start-mac.command dist/start-mac.command
cp config.example.json dist/config.example.json
cp README.md dist/README.md
chmod +x dist/start-mac.command

# Printed for the same reason as on Windows: security tooling identifies a
# build by its hash.
echo
echo "SHA256 digests:"
shasum -a 256 dist/teams-backup | awk '{printf "  %s  %s\n", $1, "teams-backup"}'
