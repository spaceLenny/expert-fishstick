#!/bin/zsh
# Stop sci-fi sounds if running.

PID_FILE="/tmp/scifi_sounds.pid"

if [ -f "$PID_FILE" ]; then
    kill "$(cat "$PID_FILE")" 2>/dev/null
    rm -f "$PID_FILE"
fi
