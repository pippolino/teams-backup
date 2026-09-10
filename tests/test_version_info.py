"""The Windows version resource has to stay in sync with the package version.

Antivirus heuristics score an executable without a version resource badly, and
SignPath requires ProductName to match the project name with consistent
ProductVersion values. Both break silently on a version bump, so they are
asserted here instead.
"""

from __future__ import annotations

import re
from pathlib import Path

from teams_backup import __version__

VERSION_INFO = Path(__file__).resolve().parent.parent / "packaging" / "windows-version-info.txt"
PRODUCT_NAME = "Teams Local Backup"


def _version_info_text() -> str:
    return VERSION_INFO.read_text(encoding="utf-8")


def _string_struct(name: str, text: str) -> str:
    match = re.search(rf"StringStruct\('{name}', '([^']*)'\)", text)
    assert match, f"StringStruct('{name}', ...) missing from {VERSION_INFO.name}"
    return match.group(1)


def test_version_resource_exists() -> None:
    assert VERSION_INFO.is_file()


def test_binary_version_tuples_match_package_version() -> None:
    text = _version_info_text()
    expected = tuple(int(part) for part in __version__.split(".")) + (0,)
    for field in ("filevers", "prodvers"):
        match = re.search(rf"{field}=\(([\d, ]+)\)", text)
        assert match, f"{field} missing from {VERSION_INFO.name}"
        actual = tuple(int(part) for part in match.group(1).split(","))
        assert actual == expected, f"{field} is {actual}, expected {expected}"


def test_version_strings_match_package_version() -> None:
    text = _version_info_text()
    expected = f"{__version__}.0"
    assert _string_struct("FileVersion", text) == expected
    assert _string_struct("ProductVersion", text) == expected


def test_product_name_is_stable() -> None:
    # SignPath rejects a signed binary whose ProductName does not match the
    # project name, so this value is not free to drift.
    assert _string_struct("ProductName", _version_info_text()) == PRODUCT_NAME
