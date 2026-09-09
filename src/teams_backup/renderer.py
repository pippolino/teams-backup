from __future__ import annotations

import copy
import json
from importlib.resources import files
from pathlib import Path

import bleach

ALLOWED_TAGS = {
    "a", "b", "blockquote", "br", "code", "del", "div", "em", "i", "li",
    "ol", "p", "pre", "s", "span", "strong", "table", "tbody", "td", "th",
    "thead", "tr", "u", "ul",
}
ALLOWED_ATTRIBUTES = {"a": ["href", "title"]}


def render_archive(output_dir: Path, archive: dict) -> None:
    browser_data = copy.deepcopy(archive)
    for chat in browser_data["chats"]:
        for message in chat["messages"]:
            body = message.get("body") or {}
            content = body.get("content") or ""
            body["content"] = bleach.clean(
                content,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRIBUTES,
                protocols={"http", "https", "mailto"},
                strip=True,
            )
            message["body"] = body

    assets = files("teams_backup.assets")
    (output_dir / "index.html").write_text(
        assets.joinpath("index.html").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (output_dir / "archive.css").write_text(
        assets.joinpath("archive.css").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (output_dir / "archive.js").write_text(
        assets.joinpath("archive.js").read_text(encoding="utf-8"), encoding="utf-8"
    )
    serialized = json.dumps(browser_data, ensure_ascii=False).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    (output_dir / "archive-data.js").write_text(
        f"window.__TEAMS_ARCHIVE__ = {serialized};\n", encoding="utf-8"
    )
