#!/bin/zsh
# Start sci-fi sounds if enabled (flag file present) and not already running.

FLAG="$HOME/.claude/scifi_sounds_enabled"
PID_FILE="/tmp/scifi_sounds.pid"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$REPO_DIR/.venv/bin/python"
SCRIPT="$REPO_DIR/bin/scifi_live.py"

[ -f "$FLAG" ] || exit 0

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    exit 0  # already running
fi

nohup "$PYTHON" "$SCRIPT" > /tmp/scifi_sounds.log 2>&1 &
echo $! > "$PID_FILE"
