#!/bin/zsh
# computersounds installer
# Sets up the virtualenv, registers Claude Code hooks, and adds shell aliases.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SETTINGS="$HOME/.claude/settings.json"
RC_FILE="$HOME/.zshrc"
ALIAS_TAG="# computersounds aliases"

# ── 1. Virtualenv + deps ──────────────────────────────────────────────────────

echo "==> Creating virtualenv..."
python3 -m venv "$REPO_DIR/.venv"

echo "==> Installing dependencies..."
"$REPO_DIR/.venv/bin/pip" install --quiet -r "$REPO_DIR/requirements.txt"

# ── 2. Make hook scripts executable ──────────────────────────────────────────

chmod +x "$REPO_DIR/bin/start_sounds.sh"
chmod +x "$REPO_DIR/bin/stop_sounds.sh"

# ── 3. Register hooks in ~/.claude/settings.json ─────────────────────────────

echo "==> Registering Claude Code hooks..."

# Ensure the file exists and is valid JSON
if [ ! -f "$SETTINGS" ]; then
    echo '{}' > "$SETTINGS"
fi

python3 - "$SETTINGS" "$REPO_DIR" <<'PYEOF'
import json, sys

settings_path = sys.argv[1]
repo_dir = sys.argv[2]

start_hook = {
    "type": "command",
    "command": f"{repo_dir}/bin/start_sounds.sh",
    "timeout": 5,
    "async": True
}
stop_hook = {
    "type": "command",
    "command": f"{repo_dir}/bin/stop_sounds.sh",
    "timeout": 5
}

with open(settings_path) as f:
    settings = json.load(f)

# UserPromptSubmit — append start_hook if not already present
ups = settings.setdefault("UserPromptSubmit", [])
existing_matchers = [e.get("matcher") for e in ups]
if ".*" not in existing_matchers:
    ups.append({"matcher": ".*", "hooks": [start_hook]})
else:
    for entry in ups:
        if entry.get("matcher") == ".*":
            hooks = entry.setdefault("hooks", [])
            if not any(h.get("command", "").endswith("start_sounds.sh") for h in hooks):
                hooks.append(start_hook)
            break

# Stop — append stop_hook if not already present
stop_entries = settings.setdefault("Stop", [])
# Stop entries have no matcher field
if not any(
    any(h.get("command", "").endswith("stop_sounds.sh") for h in e.get("hooks", []))
    for e in stop_entries
):
    stop_entries.append({"hooks": [stop_hook]})

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")

print("  hooks registered.")
PYEOF

# ── 4. Add shell aliases ──────────────────────────────────────────────────────

echo "==> Adding shell aliases to $RC_FILE..."

if grep -q "$ALIAS_TAG" "$RC_FILE" 2>/dev/null; then
    echo "  aliases already present, skipping."
else
    cat >> "$RC_FILE" <<RCEOF

$ALIAS_TAG
alias scifi-on="touch \$HOME/.claude/scifi_sounds_enabled && echo 'Sci-fi sounds ON'"
alias scifi-off="rm -f \$HOME/.claude/scifi_sounds_enabled && pkill -f scifi_live.py 2>/dev/null; echo 'Sci-fi sounds OFF'"
alias scifi-toggle='[ -f \$HOME/.claude/scifi_sounds_enabled ] && scifi-off || scifi-on'
RCEOF
    echo "  aliases added. Run: source $RC_FILE"
fi

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
echo "Installation complete!"
echo ""
echo "  scifi-on      enable sounds"
echo "  scifi-off     disable sounds"
echo "  scifi-toggle  flip current state"
echo ""
echo "Sounds will play automatically while Claude Code is processing."
