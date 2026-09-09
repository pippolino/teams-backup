from PyInstaller.utils.hooks import collect_data_files


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
    upx=True,
    console=True,
)
