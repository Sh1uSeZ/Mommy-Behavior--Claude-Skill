# Rebuilds mommy-skill.zip - the upload package for the Claude app.
#
# GitHub's "Download ZIP" is NOT usable for this: it wraps everything in a folder
# named after the repo, and includes the README, evals and installers. The app
# wants just the skill, in a folder named `mommy` (the name must match `name:`
# in the SKILL.md frontmatter).
#
#   powershell -File build-zip.ps1

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$zipPath = Join-Path $root 'mommy-skill.zip'

$files = @(
    @{ src = 'SKILL.md';                 entry = 'mommy/SKILL.md' }
    @{ src = 'reference/voice.md';       entry = 'mommy/reference/voice.md' }
    @{ src = 'reference/situations.md';  entry = 'mommy/reference/situations.md' }
    @{ src = 'reference/dials.md';       entry = 'mommy/reference/dials.md' }
    @{ src = 'reference/grounding.md';   entry = 'mommy/reference/grounding.md' }
)

foreach ($f in $files) {
    $p = Join-Path $root $f.src
    if (-not (Test-Path $p)) { throw "missing: $($f.src)" }
}

Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

# Built entry-by-entry rather than with Compress-Archive: Windows PowerShell
# writes backslash separators, which violate the zip spec and break extraction
# on macOS and Linux.
$zip = [System.IO.Compression.ZipFile]::Open($zipPath, 'Create')
try {
    foreach ($f in $files) {
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $zip, (Join-Path $root $f.src), $f.entry) | Out-Null
    }
} finally {
    $zip.Dispose()
}

Write-Host "built $zipPath"
[System.IO.Compression.ZipFile]::OpenRead($zipPath).Entries |
    ForEach-Object { Write-Host ("  {0,-34} {1,6} bytes" -f $_.FullName, $_.Length) }
Write-Host ("SHA256 " + (Get-FileHash $zipPath -Algorithm SHA256).Hash)
