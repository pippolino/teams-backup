from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from teams_backup.graph import GraphClient, GraphError, chat_path
from teams_backup.renderer import render_archive

SUPPORTED_CHAT_TYPES = {"oneOnOne", "group", "meeting"}


@dataclass(frozen=True)
class ExportResult:
    output_dir: Path
    chat_count: int
    message_count: int
    warnings: tuple[str, ...]


def export_chats(
    graph: GraphClient,
    output_parent: Path,
    emit: Callable[[str], None] = print,
) -> ExportResult:
    exported_at = datetime.now(timezone.utc)
    user = graph.get_object("/me")
    chats, chat_pages = graph.get_all("/me/chats?$top=50")
    chats = [chat for chat in chats if chat.get("chatType") in SUPPORTED_CHAT_TYPES]

    output_dir = _unique_output_dir(output_parent, exported_at)
    raw_dir = output_dir / "json" / "original-data"
    raw_dir.mkdir(parents=True)
    _write_json(raw_dir / "me.json", user)
    _write_json(raw_dir / "chats-pages.json", chat_pages)

    archive_chats: list[dict] = []
    warnings: list[str] = []
    message_count = 0
    for index, chat in enumerate(chats, start=1):
        emit(f"[{index}/{len(chats)}] Esporto {_chat_label(chat, [])}")
        chat_id = chat["id"]
        try:
            members, member_pages = graph.get_all(chat_path(chat_id, "members"))
            messages, message_pages = graph.get_all(
                f"{chat_path(chat_id, 'messages')}?$top=50&$orderby=createdDateTime desc"
            )
        except GraphError as exc:
            warning = f"Chat {chat_id}: {exc}"
            warnings.append(warning)
            emit(f"  Avviso: {warning}")
            continue

        chat_dir = raw_dir / f"chat-{index:04d}"
        chat_dir.mkdir()
        _write_json(chat_dir / "chat.json", chat)
        _write_json(chat_dir / "members-pages.json", member_pages)
        _write_json(chat_dir / "messages-pages.json", message_pages)

        messages.sort(key=lambda item: item.get("createdDateTime") or "")
        archive_chats.append(
            {
                "id": chat_id,
                "type": chat.get("chatType"),
                "title": _chat_label(chat, members, user.get("id")),
                "topic": chat.get("topic"),
                "webUrl": chat.get("webUrl"),
                "members": members,
                "messages": messages,
            }
        )
        message_count += len(messages)

    archive = {
        "formatVersion": 1,
        "exportedAt": exported_at.isoformat(),
        "user": user,
        "chatCount": len(archive_chats),
        "messageCount": message_count,
        "warnings": warnings,
        "chats": archive_chats,
    }
    _write_json(output_dir / "json" / "archive.json", archive)
    _write_json(
        output_dir / "export-info.json",
        {key: archive[key] for key in ("formatVersion", "exportedAt", "chatCount", "messageCount", "warnings")},
    )
    render_archive(output_dir, archive)
    return ExportResult(output_dir, len(archive_chats), message_count, tuple(warnings))


def _chat_label(chat: dict, members: list[dict], current_user_id: str | None = None) -> str:
    if chat.get("topic"):
        return str(chat["topic"])
    names = [
        member.get("displayName") or member.get("email")
        for member in members
        if member.get("userId") != current_user_id
    ]
    names = [str(name) for name in names if name]
    if names:
        return ", ".join(names[:4]) + ("…" if len(names) > 4 else "")
    labels = {"oneOnOne": "Chat individuale", "group": "Chat di gruppo", "meeting": "Chat riunione"}
    return labels.get(chat.get("chatType"), "Chat Teams")


def _unique_output_dir(parent: Path, exported_at: datetime) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    base = f"TeamsBackup-{exported_at:%Y-%m-%d_%H-%M-%S}"
    candidate = parent / base
    suffix = 2
    while candidate.exists():
        candidate = parent / f"{base}-{suffix}"
        suffix += 1
    candidate.mkdir()
    return candidate


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
