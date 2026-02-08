#!/bin/bash
# Start the browser automation daemon

SAK_HOME="${SAK_HOME:-$HOME/.sovereign-ai}"
SAK_BROWSER_SKILL_DIR="${SAK_BROWSER_SKILL_DIR:-$SAK_HOME/browser}"
SAK_BROWSER_PORT="${SAK_BROWSER_PORT:-19222}"
DAEMON_SCRIPT="$SAK_BROWSER_SKILL_DIR/daemon/browser-daemon.js"
PID_FILE="$SAK_BROWSER_SKILL_DIR/daemon.pid"

# Check if daemon is already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Daemon already running on port $SAK_BROWSER_PORT (PID: $PID)"
        exit 0
    fi
    rm -f "$PID_FILE"
fi

# Check prerequisites
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required but not installed."
    exit 1
fi

if [ ! -f "$DAEMON_SCRIPT" ]; then
    echo "Error: Daemon script not found at $DAEMON_SCRIPT"
    echo "Run setup.sh first or set SAK_BROWSER_SKILL_DIR"
    exit 1
fi

# Start daemon in background
SAK_HOME="$SAK_HOME" SAK_BROWSER_PORT="$SAK_BROWSER_PORT" SAK_BROWSER_SKILL_DIR="$SAK_BROWSER_SKILL_DIR" \
    nohup node "$DAEMON_SCRIPT" "$SAK_BROWSER_PORT" > /dev/null 2>&1 &

DAEMON_PID=$!
echo "$DAEMON_PID" > "$PID_FILE"

# Wait and verify
sleep 1
if kill -0 "$DAEMON_PID" 2>/dev/null; then
    echo "Daemon started successfully (PID: $DAEMON_PID)"
    echo "Port: $SAK_BROWSER_PORT"
    echo "Logs: $SAK_BROWSER_SKILL_DIR/daemon.log"
else
    echo "Error: Daemon failed to start. Check $SAK_BROWSER_SKILL_DIR/daemon.log"
    rm -f "$PID_FILE"
    exit 1
fi
