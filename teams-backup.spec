import os
import sys

from PyInstaller.utils.hooks import collect_data_files

IS_WINDOWS = sys.platform == "win32"

# UPX packing is itself a strong indicator of malware for antivirus heuristics,
# so it stays disabled on every platform.
USE_UPX = False

VERSION_INFO = os.path.join(SPECPATH, "packaging", "windows-version-info.txt")

analysis = Analysis(
    ["src/teams_backup/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=collect_data_files("teams_backup"),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(analysis.pure)

if IS_WINDOWS:
    # One directory on Windows. A onefile executable unpacks itself into %TEMP%
    # and executes code from there, which generic antivirus heuristics score as
    # dropper behaviour. Shipping the dependencies next to the executable keeps
    # the binary a plain application and leaves a signature verifiable on disk.
    executable = EXE(
        pyz,
        analysis.scripts,
        [],
        exclude_binaries=True,
        name="teams-backup",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=USE_UPX,
        console=True,
        version=VERSION_INFO,
    )
    collected = COLLECT(
        executable,
        analysis.binaries,
        analysis.datas,
        strip=False,
        upx=USE_UPX,
        name="teams-backup",
    )
else:
    # One file on macOS. The launcher ships a single binary next to the config,
    # and Gatekeeper judges the signature and notarisation rather than the
    # layout, so onefile stays the simpler distribution here.
    executable = EXE(
        pyz,
        analysis.scripts,
        analysis.binaries,
        analysis.datas,
        [],
        name="teams-backup",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=USE_UPX,
        console=True,
    )
