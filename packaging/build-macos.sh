#!/usr/bin/env bash
set -euo pipefail

export PYINSTALLER_CONFIG_DIR="${PWD}/.pyinstaller-cache"
python3 -m pip install ".[dev]"
python3 -m pytest
python3 -m PyInstaller --clean --noconfirm teams-backup.spec
