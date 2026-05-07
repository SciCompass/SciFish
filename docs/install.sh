#!/usr/bin/env bash
#
# SciFish skill installer.
#
#   curl -fsSL https://scicompass.github.io/SciFish/install.sh | bash -s <skill-name>
#
# Optional env:
#   SKILL_DIR   target directory (default: $HOME/.claude/skills)
#   REPO_URL    override the source repo (default: https://github.com/SciCompass/SciFish)
#   REF         git ref to install from (default: main)

set -euo pipefail

SKILL=${1:-}
if [[ -z "$SKILL" ]]; then
  echo "usage: install.sh <skill-name>" >&2
  echo "       (e.g. raman-analysis, ftir-analysis, contact-angle-surface-tension-analysis)" >&2
  exit 2
fi

SKILL_DIR=${SKILL_DIR:-"$HOME/.claude/skills"}
REPO_URL=${REPO_URL:-"https://github.com/SciCompass/SciFish"}
REF=${REF:-"main"}

command -v git >/dev/null 2>&1 || {
  echo "❌ git is required but not found in PATH" >&2
  exit 1
}

mkdir -p "$SKILL_DIR"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "→ cloning $REPO_URL ($REF) ..."
git clone --depth 1 --branch "$REF" "$REPO_URL" "$TMP/SciFish" >/dev/null 2>&1 || {
  echo "❌ failed to clone $REPO_URL@$REF" >&2
  exit 1
}

SRC="$TMP/SciFish/skills/$SKILL"
if [[ ! -d "$SRC" ]]; then
  echo "❌ skill '$SKILL' not found in $REPO_URL@$REF" >&2
  echo "   available skills:" >&2
  ls "$TMP/SciFish/skills" | sed 's/^/     - /' >&2
  exit 1
fi

DEST="$SKILL_DIR/$SKILL"
if [[ -e "$DEST" ]]; then
  echo "⚠️  $DEST already exists — overwriting"
  rm -rf "$DEST"
fi

cp -R "$SRC" "$DEST"

echo "✅ installed $SKILL → $DEST"
echo "   restart your Agent (Claude Code / Codex CLI) to pick up the new skill."
