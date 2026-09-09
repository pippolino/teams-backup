import json

from teams_backup.exporter import export_chats


class StubGraph:
    def get_object(self, path):
        assert path == "/me"
        return {"id": "me", "displayName": "Ada Lovelace", "userPrincipalName": "ada@example.com"}

    def get_all(self, path):
        if path.startswith("/me/chats?"):
            chats = [
                {"id": "chat-1", "chatType": "oneOnOne", "topic": None, "webUrl": "https://teams.microsoft.com/chat"},
                {"id": "channel-like", "chatType": "unknownFutureType"},
            ]
            return chats, [{"value": chats}]
        if path.endswith("/members"):
            members = [
                {"userId": "me", "displayName": "Ada Lovelace"},
                {"userId": "grace", "displayName": "Grace Hopper"},
            ]
            return members, [{"value": members}]
        if "/messages?" in path:
            messages = [
                {"id": "2", "createdDateTime": "2026-01-02T00:00:00Z", "body": {"content": "Second"}},
                {"id": "1", "createdDateTime": "2026-01-01T00:00:00Z", "body": {"content": "First"}},
            ]
            return messages, [{"value": messages}]
        raise AssertionError(path)


def test_exports_supported_chats_raw_json_and_html(tmp_path):
    result = export_chats(StubGraph(), tmp_path, emit=lambda _: None)

    assert result.chat_count == 1
    assert result.message_count == 2
    archive = json.loads((result.output_dir / "json" / "archive.json").read_text())
    assert archive["chats"][0]["title"] == "Grace Hopper"
    assert [message["id"] for message in archive["chats"][0]["messages"]] == ["1", "2"]
    assert (result.output_dir / "json" / "original-data" / "chat-0001" / "messages-pages.json").exists()
    assert (result.output_dir / "index.html").exists()
