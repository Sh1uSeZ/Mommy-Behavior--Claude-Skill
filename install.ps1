# Installs the /mommy skill for Claude Code.
#   irm https://raw.githubusercontent.com/Sh1uSeZ/Mommy-Behavior--Claude-Skill/main/install.ps1 | iex
# Env:  MOMMY_REPO, MOMMY_BRANCH, CLAUDE_SKILLS_DIR (defaults to ~/.claude/skills)
#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

$Repo   = if ($env:MOMMY_REPO)         { $env:MOMMY_REPO }         else { 'Sh1uSeZ/Mommy-Behavior--Claude-Skill' }
$Branch = if ($env:MOMMY_BRANCH)       { $env:MOMMY_BRANCH }       else { 'main' }
$Root   = if ($env:CLAUDE_SKILLS_DIR)  { $env:CLAUDE_SKILLS_DIR }  else { Join-Path $env:USERPROFILE '.claude\skills' }
$Dest   = Join-Path $Root 'mommy'

# A junction/symlink install means someone is developing the skill. Never overwrite it.
$existing = Get-Item $Dest -Force -ErrorAction SilentlyContinue
if ($existing -and $existing.LinkType) {
    Write-Host "error: $Dest is a $($existing.LinkType) (a dev install pointing at a working copy)." -ForegroundColor Red
    Write-Host "       installing would replace it with a static copy."
    Write-Host "       remove it first if that is what you want:  cmd /c rmdir `"$Dest`""
    return
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("mommy-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $tmp | Out-Null
try {
    Write-Host "downloading $Repo@$Branch ..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    try {
        Invoke-WebRequest "https://github.com/$Repo/archive/refs/heads/$Branch.zip" -OutFile "$tmp\src.zip" -UseBasicParsing
    } catch {
        Write-Host "error: download failed - check the repo name, branch, and your connection." -ForegroundColor Red
        Write-Host "       $($_.Exception.Message)"
        return
    }
    Expand-Archive "$tmp\src.zip" -DestinationPath $tmp -Force

    $skill = Get-ChildItem $tmp -Recurse -Depth 2 -Filter 'SKILL.md' | Select-Object -First 1
    if (-not $skill) {
        Write-Host "error: no SKILL.md in the downloaded archive - nothing to install." -ForegroundColor Red
        return
    }

    New-Item -ItemType Directory -Force $Root | Out-Null
    if (Test-Path $Dest) {
        Write-Host "replacing existing install at $Dest"
        Remove-Item $Dest -Recurse -Force
    }
    Move-Item $skill.Directory.FullName $Dest
    Remove-Item (Join-Path $Dest 'install.sh'), (Join-Path $Dest 'install.ps1') -Force -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "  installed  $Dest" -ForegroundColor Green
    Write-Host "  scope      all projects"
    Write-Host ""
    Write-Host "  Restart Claude Code, then run:  /mommy"
    Write-Host "  Turn it off any time with:      /mommy off"
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
