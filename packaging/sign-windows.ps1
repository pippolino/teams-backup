<#
.SYNOPSIS
    Authenticode-signs a teams-backup onedir build.

.DESCRIPTION
    Signs the executable and every bundled DLL and PYD. Signing the bundled
    binaries matters as much as signing the executable: an antivirus on-access
    scanner inspects each module as it is loaded, so an unsigned dependency
    undoes most of the benefit of signing the entry point.

    Configuration comes from environment variables so that no credential is
    ever committed. When none of the three modes below is configured the script
    exits successfully without signing, which keeps unsigned local builds
    working.

    Mode 1 - certificate store, by thumbprint (most precise):
        TEAMS_BACKUP_SIGN_SHA1       certificate SHA1 thumbprint
    Mode 2 - certificate store, by subject name:
        TEAMS_BACKUP_SIGN_SUBJECT    substring of the certificate subject
    Mode 3 - Azure Artifact Signing / Trusted Signing:
        TEAMS_BACKUP_SIGN_DLIB       path to the signing dlib
        TEAMS_BACKUP_SIGN_DMDF       path to the metadata json

    Optional:
        TEAMS_BACKUP_SIGN_TIMESTAMP_URL   RFC3161 timestamp server
                                          (default: DigiCert)

    A timestamp is not optional in practice: without one every signature stops
    validating the day the certificate expires.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$ErrorActionPreference = "Stop"

$Sha1 = $env:TEAMS_BACKUP_SIGN_SHA1
$Subject = $env:TEAMS_BACKUP_SIGN_SUBJECT
$Dlib = $env:TEAMS_BACKUP_SIGN_DLIB
$Dmdf = $env:TEAMS_BACKUP_SIGN_DMDF
$TimestampUrl = if ($env:TEAMS_BACKUP_SIGN_TIMESTAMP_URL) {
    $env:TEAMS_BACKUP_SIGN_TIMESTAMP_URL
} else {
    "http://timestamp.digicert.com"
}

if (-not $Sha1 -and -not $Subject -and -not $Dlib) {
    Write-Host "Code signing not configured; leaving the build unsigned."
    Write-Host "Set TEAMS_BACKUP_SIGN_SHA1, TEAMS_BACKUP_SIGN_SUBJECT or TEAMS_BACKUP_SIGN_DLIB to enable it."
    exit 0
}

function Resolve-SignTool {
    $onPath = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($onPath) { return $onPath.Source }

    # The Windows SDK is not on PATH by default. Prefer the highest version of
    # the x64 build when several SDKs are installed side by side.
    $roots = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin",
        "${env:ProgramFiles}\Windows Kits\10\bin"
    ) | Where-Object { $_ -and (Test-Path $_) }

    $candidate = Get-ChildItem -Path $roots -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match "\\x64\\" } |
        Sort-Object FullName -Descending |
        Select-Object -First 1

    if (-not $candidate) {
        throw "signtool.exe not found. Install the Windows SDK 'Windows App Certification Kit' component."
    }
    return $candidate.FullName
}

$SignTool = Resolve-SignTool
Write-Host "Using signtool: $SignTool"

if (-not (Test-Path $Path)) {
    throw "Path to sign not found: $Path"
}

$targets = Get-ChildItem -Path $Path -Recurse -Include *.exe, *.dll, *.pyd -File |
    Sort-Object FullName |
    ForEach-Object { $_.FullName }

if (-not $targets) {
    throw "No signable files found under $Path"
}

# Build the mode-specific arguments once.
$modeArgs = if ($Dlib) {
    if (-not $Dmdf) { throw "TEAMS_BACKUP_SIGN_DLIB is set but TEAMS_BACKUP_SIGN_DMDF is missing." }
    @("/v", "/dlib", $Dlib, "/dmdf", $Dmdf)
} elseif ($Sha1) {
    @("/sha1", $Sha1)
} else {
    @("/n", $Subject)
}

$common = @("/fd", "SHA256", "/tr", $TimestampUrl, "/td", "SHA256")

Write-Host "Signing $($targets.Count) files under $Path"
# signtool accepts many files per invocation, but batching keeps the command
# line under the Windows limit on large bundles.
$batchSize = 40
for ($i = 0; $i -lt $targets.Count; $i += $batchSize) {
    $batch = $targets[$i..([Math]::Min($i + $batchSize - 1, $targets.Count - 1))]
    & $SignTool sign @modeArgs @common @batch
    if ($LASTEXITCODE -ne 0) {
        throw "signtool sign failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Verifying signatures"
& $SignTool verify /pa /all @targets
if ($LASTEXITCODE -ne 0) {
    throw "signtool verify failed with exit code $LASTEXITCODE"
}

Write-Host "Signed and verified $($targets.Count) files."
