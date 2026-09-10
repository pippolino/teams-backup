$ErrorActionPreference = "Stop"
$env:PYINSTALLER_CONFIG_DIR = Join-Path (Get-Location) ".pyinstaller-cache"

py -m pip install ".[dev]"
py -m pytest
py -m PyInstaller --clean --noconfirm teams-backup.spec

# The Windows build is onedir, so PyInstaller writes an application folder
# rather than a single file. Sign it before packaging: the signature has to
# cover the files that actually get loaded at runtime.
$AppDir = Join-Path (Get-Location) "dist\teams-backup"
& (Join-Path $PSScriptRoot "sign-windows.ps1") -Path $AppDir

$ReleaseRoot = Join-Path (Get-Location) "release"
$PackageDir = Join-Path $ReleaseRoot "teams-backup-windows-x64"
$PackageZip = Join-Path $ReleaseRoot "teams-backup-windows-x64.zip"
if (Test-Path $PackageDir) { Remove-Item $PackageDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $PackageDir | Out-Null

# Flatten the application folder into the package root so that config.json sits
# next to teams-backup.exe, which is where the tool looks for it when frozen.
Copy-Item (Join-Path $AppDir "*") $PackageDir -Recurse -Force
Copy-Item "config.example.json" (Join-Path $PackageDir "config.example.json") -Force
Copy-Item "README.md" (Join-Path $PackageDir "README.md") -Force
Compress-Archive -Path "$PackageDir\*" -DestinationPath $PackageZip -Force
Write-Host "Windows package created at $PackageZip"

# Antivirus allow-lists are keyed on the file hash, so print the digests an IT
# team needs rather than making them compute these by hand.
Write-Host ""
Write-Host "SHA256 digests:"
Get-FileHash -Algorithm SHA256 @(
    (Join-Path $PackageDir "teams-backup.exe"),
    $PackageZip
) | ForEach-Object { Write-Host ("  {0}  {1}" -f $_.Hash, (Split-Path $_.Path -Leaf)) }
