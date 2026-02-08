#!/bin/bash
# Install browser automation components

set -e

SAK_HOME="${SAK_HOME:-$HOME/.sovereign-ai}"
SAK_BROWSER_SKILL_DIR="${SAK_BROWSER_SKILL_DIR:-$SAK_HOME/browser}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing Sovereign AI Browser Automation..."
echo "Target: $SAK_BROWSER_SKILL_DIR"

# Create directory structure
mkdir -p "$SAK_BROWSER_SKILL_DIR/daemon"
mkdir -p "$SAK_BROWSER_SKILL_DIR/scripts"
mkdir -p "$SAK_BROWSER_SKILL_DIR/extension"

# Copy daemon
cp "$SCRIPT_DIR/daemon/browser-daemon.js" "$SAK_BROWSER_SKILL_DIR/daemon/"

# Copy CLI wrapper
cp "$SCRIPT_DIR/scripts/browser.js" "$SAK_BROWSER_SKILL_DIR/scripts/"
chmod +x "$SAK_BROWSER_SKILL_DIR/scripts/browser.js"

# Copy extension files
cp "$SCRIPT_DIR/extension/manifest.json" "$SAK_BROWSER_SKILL_DIR/extension/"
cp "$SCRIPT_DIR/extension/background.js" "$SAK_BROWSER_SKILL_DIR/extension/"
cp "$SCRIPT_DIR/extension/content.js" "$SAK_BROWSER_SKILL_DIR/extension/"

# Copy start script
cp "$SCRIPT_DIR/start-daemon.sh" "$SAK_BROWSER_SKILL_DIR/"
chmod +x "$SAK_BROWSER_SKILL_DIR/start-daemon.sh"

echo ""
echo "Browser automation installed."
echo ""
echo "Next steps:"
echo "  1. Open Chrome and go to chrome://extensions/"
echo "  2. Enable 'Developer mode' (top right toggle)"
echo "  3. Click 'Load unpacked' and select: $SAK_BROWSER_SKILL_DIR/extension/"
echo "  4. Start the daemon: $SAK_BROWSER_SKILL_DIR/start-daemon.sh"
echo "  5. Test: node $SAK_BROWSER_SKILL_DIR/scripts/browser.js get_tabs"
