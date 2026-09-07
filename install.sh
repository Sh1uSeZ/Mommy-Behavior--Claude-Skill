#!/usr/bin/env bash
# Installs the /mommy skill for Claude Code.
#   curl -fsSL https://raw.githubusercontent.com/Sh1uSeZ/Mommy-Behavior--Claude-Skill/main/install.sh | bash
# Flags:  --project   install into ./.claude/skills instead of ~/.claude/skills
# Env:    MOMMY_REPO, MOMMY_BRANCH, CLAUDE_SKILLS_DIR
set -euo pipefail

REPO="${MOMMY_REPO:-Sh1uSeZ/Mommy-Behavior--Claude-Skill}"
BRANCH="${MOMMY_BRANCH:-main}"
SKILL="mommy"

if [ "${1:-}" = "--project" ]; then
  DEST_ROOT="$PWD/.claude/skills"
  SCOPE="this project"
else
  DEST_ROOT="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
  SCOPE="all projects"
fi
DEST="$DEST_ROOT/$SKILL"

for cmd in curl tar; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "error: '$cmd' is required but not installed." >&2
    exit 1
  fi
done

# A symlinked install means someone is developing the skill. Never overwrite it.
if [ -L "$DEST" ]; then
  echo "error: $DEST is a symlink (a dev install pointing at a working copy)." >&2
  echo "       installing would replace it with a static copy." >&2
  echo "       remove it first if that is what you want:  rm '$DEST'" >&2
  exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "downloading $REPO@$BRANCH ..."
if ! curl -fsSL "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" | tar -xz -C "$TMP"; then
  echo "error: download failed. check the repo name, branch, and your connection." >&2
  exit 1
fi

FOUND="$(find "$TMP" -maxdepth 2 -name SKILL.md -print -quit)"
if [ -z "$FOUND" ]; then
  echo "error: no SKILL.md in the downloaded archive - nothing to install." >&2
  exit 1
fi
SRC="$(dirname "$FOUND")"

mkdir -p "$DEST_ROOT"
if [ -d "$DEST" ]; then
  echo "replacing existing install at $DEST"
  rm -rf "$DEST"
fi
mv "$SRC" "$DEST"
rm -f "$DEST/install.sh" "$DEST/install.ps1"

echo
echo "  installed  $DEST"
echo "  scope      $SCOPE"
echo
echo "  Restart Claude Code, then run:  /mommy"
echo "  Turn it off any time with:      /mommy off"
