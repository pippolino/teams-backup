from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from teams_backup import __version__
from teams_backup.auth import AuthenticationError, acquire_access_token
from teams_backup.config import load_config
from teams_backup.exporter import export_chats
from teams_backup.graph import GraphClient, GraphError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="teams-backup",
        description="Esporta localmente le chat Teams accessibili all'utente.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--config", type=Path, help="File JSON con client_id e tenant")
    parser.add_argument("--client-id", help="Application (client) ID di Entra ID")
    parser.add_argument("--tenant", help="Tenant ID, dominio verificato o organizations")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.cwd(),
        help="Cartella in cui creare il backup (predefinita: cartella corrente)",
    )
    parser.add_argument("--no-browser", action="store_true", help="Non aprire il browser automaticamente")
    parser.add_argument("--no-open", action="store_true", help="Non aprire l'archivio al termine")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config_path = args.config or _discover_config()
        config = load_config(config_path, args.client_id, args.tenant)
        print("Accesso a Microsoft 365…")
        token = acquire_access_token(config, open_browser=not args.no_browser)
        print("Accesso completato. Inizio esportazione…")
        result = export_chats(GraphClient(token), args.output.expanduser().resolve())
    except (ValueError, AuthenticationError, GraphError, OSError) as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        return 1

    print(
        f"Backup completato: {result.chat_count} chat, "
        f"{result.message_count} messaggi.\n{result.output_dir}"
    )
    if result.warnings:
        print(f"Completato con {len(result.warnings)} avvisi; consulta export-info.json.")
    if not args.no_open:
        webbrowser.open((result.output_dir / "index.html").as_uri())
    return 0


def _discover_config() -> Path | None:
    candidates = [Path.cwd() / "config.json"]
    if getattr(sys, "frozen", False):
        candidates.insert(0, Path(sys.executable).resolve().parent / "config.json")
    return next((path for path in candidates if path.is_file()), None)
