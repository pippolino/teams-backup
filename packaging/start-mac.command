#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"
xattr -d com.apple.quarantine teams-backup 2>/dev/null || true
chmod +x teams-backup
exec ./teams-backup "$@"
