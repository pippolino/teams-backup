from __future__ import annotations

import webbrowser
from collections.abc import Callable

import msal

from teams_backup.config import AppConfig

SCOPES = ["User.Read", "Chat.Read"]


class AuthenticationError(RuntimeError):
    """Raised when Microsoft sign-in does not return an access token."""


def acquire_access_token(
    config: AppConfig,
    emit: Callable[[str], None] = print,
    open_browser: bool = True,
) -> str:
    app = msal.PublicClientApplication(config.client_id, authority=config.authority)
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        description = flow.get("error_description", "Device login could not be started.")
        raise AuthenticationError(description)

    emit(flow.get("message", "Complete Microsoft sign-in in your browser."))
    if open_browser and flow.get("verification_uri"):
        webbrowser.open(flow["verification_uri"])

    result = app.acquire_token_by_device_flow(flow)
    token = result.get("access_token")
    if token:
        return token

    error = result.get("error", "authentication_failed")
    description = result.get("error_description", "Microsoft sign-in failed.")
    raise AuthenticationError(f"{error}: {description}")
