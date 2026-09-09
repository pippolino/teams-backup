$ErrorActionPreference = "Stop"
$env:PYINSTALLER_CONFIG_DIR = Join-Path (Get-Location) ".pyinstaller-cache"

py -m pip install ".[dev]"
py -m pytest
py -m PyInstaller --clean --noconfirm teams-backup.spec

$ReleaseRoot = Join-Path (Get-Location) "release"
$PackageDir = Join-Path $ReleaseRoot "teams-backup-windows-x64"
$PackageZip = Join-Path $ReleaseRoot "teams-backup-windows-x64.zip"
New-Item -ItemType Directory -Force -Path $PackageDir | Out-Null
Copy-Item "dist\teams-backup.exe" (Join-Path $PackageDir "teams-backup.exe") -Force
Copy-Item "config.example.json" (Join-Path $PackageDir "config.example.json") -Force
Copy-Item "README.md" (Join-Path $PackageDir "README.md") -Force
Compress-Archive -Path "$PackageDir\*" -DestinationPath $PackageZip -Force
Write-Host "Windows package created at $PackageZip"
