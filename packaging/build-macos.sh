#!/usr/bin/env bash
set -euo pipefail

export PYINSTALLER_CONFIG_DIR="${PWD}/.pyinstaller-cache"
python3 -m pip install ".[dev]"
python3 -m pytest
python3 -m PyInstaller --clean --noconfirm teams-backup.spec
cp packaging/avvia-mac.command dist/avvia-mac.command
chmod +x dist/avvia-mac.command
