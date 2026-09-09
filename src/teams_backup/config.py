from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    client_id: str
    tenant: str = "organizations"

    @property
    def authority(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant}"


def load_config(path: Path | None, client_id: str | None, tenant: str | None) -> AppConfig:
    file_values: dict[str, str] = {}
    if path:
        try:
            file_values = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ValueError(f"Configuration file not found: {path}") from exc
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"Cannot read configuration file: {exc}") from exc

    resolved_client_id = (
        client_id
        or os.environ.get("TEAMS_BACKUP_CLIENT_ID")
        or file_values.get("client_id")
    )
    resolved_tenant = (
        tenant
        or os.environ.get("TEAMS_BACKUP_TENANT")
        or file_values.get("tenant")
        or "organizations"
    )
    if not resolved_client_id:
        raise ValueError(
            "Missing client ID. Use --client-id, TEAMS_BACKUP_CLIENT_ID, or config.json."
        )
    if any(char in resolved_tenant for char in "/?#"):
        raise ValueError("Tenant must be a tenant ID, verified domain, or 'organizations'.")
    return AppConfig(client_id=resolved_client_id, tenant=resolved_tenant)
