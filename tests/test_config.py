import json

import pytest

from teams_backup.config import load_config


def test_loads_file_and_cli_override(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"client_id": "from-file", "tenant": "old-tenant"}))

    config = load_config(path, "from-cli", "new-tenant")

    assert config.client_id == "from-cli"
    assert config.tenant == "new-tenant"
    assert config.authority.endswith("/new-tenant")


def test_rejects_missing_client_id(monkeypatch):
    monkeypatch.delenv("TEAMS_BACKUP_CLIENT_ID", raising=False)

    with pytest.raises(ValueError, match="Missing client ID"):
        load_config(None, None, None)


def test_rejects_unsafe_tenant():
    with pytest.raises(ValueError, match="Tenant"):
        load_config(None, "client", "tenant/path")
