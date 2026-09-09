#!/usr/bin/env bash
# Rebuilds mommy-skill.zip - the upload package for the Claude app.
#
# GitHub's "Download ZIP" is NOT usable for this: it wraps everything in a folder
# named after the repo, and includes the README, evals and installers. The app
# wants just the skill, in a folder named `mommy` (the name must match `name:`
# in the SKILL.md frontmatter).
#
#   ./build-zip.sh

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$root"

files=(
  SKILL.md
  reference/voice.md
  reference/situations.md
  reference/dials.md
  reference/grounding.md
)

for f in "${files[@]}"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 1; }
done

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

mkdir -p "$tmp/mommy/reference"
for f in "${files[@]}"; do
  cp "$f" "$tmp/mommy/$f"
done

rm -f mommy-skill.zip
( cd "$tmp" && zip -qr "$root/mommy-skill.zip" mommy )

echo "built $root/mommy-skill.zip"
unzip -l mommy-skill.zip | sed '1,3d;$d'
if command -v shasum >/dev/null; then
  echo "SHA256 $(shasum -a 256 mommy-skill.zip | cut -d' ' -f1)"
fi
