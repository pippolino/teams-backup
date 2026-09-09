from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import quote, urlparse

import requests

GRAPH_ROOT = "https://graph.microsoft.com/v1.0"


@dataclass
class GraphError(RuntimeError):
    status_code: int
    message: str
    request_id: str | None = None

    def __str__(self) -> str:
        suffix = f" (request ID: {self.request_id})" if self.request_id else ""
        return f"Microsoft Graph returned {self.status_code}: {self.message}{suffix}"


class GraphClient:
    def __init__(
        self,
        access_token: str,
        session: requests.Session | None = None,
        max_retries: int = 5,
    ) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "User-Agent": "teams-local-backup/0.1",
            }
        )
        self.max_retries = max_retries

    def get_pages(self, path_or_url: str) -> list[dict]:
        url = self._url(path_or_url)
        pages: list[dict] = []
        while url:
            payload = self._get_json(url)
            pages.append(payload)
            next_link = payload.get("@odata.nextLink")
            url = self._url(next_link) if next_link else ""
        return pages

    def get_all(self, path_or_url: str) -> tuple[list[dict], list[dict]]:
        pages = self.get_pages(path_or_url)
        values = [item for page in pages for item in page.get("value", [])]
        return values, pages

    def get_object(self, path_or_url: str) -> dict:
        return self._get_json(self._url(path_or_url))

    def _get_json(self, url: str) -> dict:
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=(10, 60))
            except requests.RequestException as exc:
                if attempt >= self.max_retries:
                    raise GraphError(0, f"Network error: {exc}") from exc
                time.sleep(min(2**attempt, 16))
                continue

            if response.status_code not in {429, 500, 502, 503, 504}:
                break
            if attempt >= self.max_retries:
                break
            retry_after = response.headers.get("Retry-After")
            delay = int(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
            time.sleep(min(delay, 60))

        if not response.ok:
            try:
                error = response.json().get("error", {})
                message = error.get("message") or response.reason
                request_id = error.get("innerError", {}).get("request-id")
            except ValueError:
                message = response.reason or "Unknown error"
                request_id = None
            raise GraphError(response.status_code, message, request_id)
        try:
            return response.json()
        except ValueError as exc:
            raise GraphError(response.status_code, "Response was not valid JSON.") from exc

    @staticmethod
    def _url(path_or_url: str) -> str:
        if path_or_url.startswith("http"):
            parsed = urlparse(path_or_url)
            if parsed.scheme != "https" or parsed.hostname != "graph.microsoft.com":
                raise ValueError("Refusing to send a token outside graph.microsoft.com.")
            return path_or_url
        return f"{GRAPH_ROOT}/{path_or_url.lstrip('/')}"


def chat_path(chat_id: str, resource: str) -> str:
    return f"/me/chats/{quote(chat_id, safe='')}/{resource}"
