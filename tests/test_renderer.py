import json

from teams_backup.renderer import render_archive


def test_renders_offline_archive_and_sanitizes_browser_data(tmp_path):
    archive = {
        "formatVersion": 1,
        "exportedAt": "2026-01-02T03:04:05+00:00",
        "user": {"displayName": "Ada"},
        "chatCount": 1,
        "messageCount": 1,
        "warnings": [],
        "chats": [
            {
                "id": "chat-1",
                "type": "oneOnOne",
                "title": "Grace",
                "members": [],
                "messages": [
                    {"body": {"content": '<p>Hello</p><script>alert("x")</script>'}}
                ],
            }
        ],
    }

    render_archive(tmp_path, archive)

    data = (tmp_path / "archive-data.js").read_text()
    assert "<script>" not in data
    assert "Hello" in data
    assert (tmp_path / "index.html").exists()
    assert (tmp_path / "archive.css").exists()
    assert (tmp_path / "archive.js").exists()
    assert json.loads(json.dumps(archive))["chats"][0]["messages"][0]["body"]["content"].startswith("<p>")
