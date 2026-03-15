#!/bin/zsh
# computersounds uninstaller
# Removes hooks from ~/.claude/settings.json, shell aliases, and optionally the virtualenv.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SETTINGS="$HOME/.claude/settings.json"
RC_FILE="$HOME/.zshrc"
ALIAS_TAG="# computersounds aliases"

# ── 1. Stop any running instance ──────────────────────────────────────────────

echo "==> Stopping sounds..."
pkill -f scifi_live.py 2>/dev/null && echo "  process killed." || echo "  not running."
rm -f /tmp/scifi_sounds.pid
rm -f "$HOME/.claude/scifi_sounds_enabled"

# ── 2. Remove hooks from ~/.claude/settings.json ─────────────────────────────

if [ -f "$SETTINGS" ]; then
    echo "==> Removing Claude Code hooks..."
    python3 - "$SETTINGS" <<'PYEOF'
import json, sys

settings_path = sys.argv[1]

with open(settings_path) as f:
    settings = json.load(f)

# Remove start_sounds.sh hook from UserPromptSubmit
for entry in settings.get("UserPromptSubmit", []):
    entry["hooks"] = [
        h for h in entry.get("hooks", [])
        if not h.get("command", "").endswith("start_sounds.sh")
    ]

# Remove stop_sounds.sh hook from Stop
settings["Stop"] = [
    entry for entry in settings.get("Stop", [])
    if not any(h.get("command", "").endswith("stop_sounds.sh") for h in entry.get("hooks", []))
]

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")

print("  hooks removed.")
PYEOF
fi

# ── 3. Remove shell aliases ───────────────────────────────────────────────────

if grep -q "$ALIAS_TAG" "$RC_FILE" 2>/dev/null; then
    echo "==> Removing shell aliases from $RC_FILE..."
    # Remove the tag line and the 3 alias lines that follow it
    python3 - "$RC_FILE" "$ALIAS_TAG" <<'PYEOF'
import sys

rc_path = sys.argv[1]
tag = sys.argv[2]

with open(rc_path) as f:
    lines = f.readlines()

out = []
skip = 0
for line in lines:
    if line.strip() == tag:
        skip = 4  # tag + 3 alias lines
    if skip > 0:
        skip -= 1
        continue
    out.append(line)

# Trim any trailing blank lines added by the block
while out and out[-1].strip() == "":
    out.pop()
out.append("\n")

with open(rc_path, "w") as f:
    f.writelines(out)

print(f"  aliases removed. Run: source {rc_path}")
PYEOF
else
    echo "  no aliases found, skipping."
fi

# ── 4. Optionally remove the virtualenv ──────────────────────────────────────

echo ""
read "REPLY?Remove .venv directory? [y/N] "
if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    rm -rf "$REPO_DIR/.venv"
    echo "  .venv removed."
fi

echo ""
echo "Uninstall complete."
