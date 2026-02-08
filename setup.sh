#!/bin/bash
# Sovereign AI Kit — Master Installer
# Sets up the full sovereignty stack: memory, browser, body, identity

set -e

SAK_HOME="${SAK_HOME:-$HOME/.sovereign-ai}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║     Sovereign AI Kit — Setup             ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Install directory: $SAK_HOME"
echo ""

# ── Create directory structure ────────────────────────────
echo "Creating directory structure..."
mkdir -p "$SAK_HOME/memory"
mkdir -p "$SAK_HOME/history/learnings"
mkdir -p "$SAK_HOME/history/sessions"
mkdir -p "$SAK_HOME/identity"
mkdir -p "$SAK_HOME/browser/daemon"
mkdir -p "$SAK_HOME/browser/scripts"
mkdir -p "$SAK_HOME/browser/extension"
mkdir -p "$SAK_HOME/body"

# ── Copy configuration ───────────────────────────────────
if [ ! -f "$SAK_HOME/config.env" ]; then
    cp "$SCRIPT_DIR/config.example.env" "$SAK_HOME/config.env"
    echo "Created config.env (edit to customize)"
else
    echo "config.env already exists (skipping)"
fi

# ── Install memory system ────────────────────────────────
echo ""
echo "Installing memory system..."
cp "$SCRIPT_DIR/memory/sovereign_memory.py" "$SAK_HOME/memory/"
chmod +x "$SAK_HOME/memory/sovereign_memory.py"

if [ -d "$SCRIPT_DIR/memory/plugins" ]; then
    mkdir -p "$SAK_HOME/memory/plugins"
    cp "$SCRIPT_DIR/memory/plugins/"*.py "$SAK_HOME/memory/plugins/" 2>/dev/null || true
fi

if [ -f "$SCRIPT_DIR/memory/sync_learnings.py" ]; then
    cp "$SCRIPT_DIR/memory/sync_learnings.py" "$SAK_HOME/memory/"
fi

echo "  Memory system installed."

# ── Install browser automation ───────────────────────────
echo ""
echo "Installing browser automation..."
cp "$SCRIPT_DIR/browser/daemon/browser-daemon.js" "$SAK_HOME/browser/daemon/"
cp "$SCRIPT_DIR/browser/scripts/browser.js" "$SAK_HOME/browser/scripts/"
chmod +x "$SAK_HOME/browser/scripts/browser.js"

cp "$SCRIPT_DIR/browser/extension/manifest.json" "$SAK_HOME/browser/extension/"
cp "$SCRIPT_DIR/browser/extension/background.js" "$SAK_HOME/browser/extension/"
cp "$SCRIPT_DIR/browser/extension/content.js" "$SAK_HOME/browser/extension/"

cp "$SCRIPT_DIR/browser/start-daemon.sh" "$SAK_HOME/browser/"
chmod +x "$SAK_HOME/browser/start-daemon.sh"

echo "  Browser automation installed."

# ── Install body system ──────────────────────────────────
echo ""
echo "Installing body system..."
cp "$SCRIPT_DIR/body/"*.py "$SAK_HOME/body/"
chmod +x "$SAK_HOME/body/body_cli.py"
echo "  Body system installed."

# ── Install identity templates ───────────────────────────
echo ""
echo "Installing identity templates..."
if [ -d "$SCRIPT_DIR/identity/templates" ]; then
    mkdir -p "$SAK_HOME/identity/templates"
    cp "$SCRIPT_DIR/identity/templates/"* "$SAK_HOME/identity/templates/" 2>/dev/null || true
fi

if [ -d "$SCRIPT_DIR/identity/examples" ]; then
    mkdir -p "$SAK_HOME/identity/examples"
    cp -r "$SCRIPT_DIR/identity/examples/"* "$SAK_HOME/identity/examples/" 2>/dev/null || true
fi

if [ -f "$SCRIPT_DIR/identity/GUIDE.md" ]; then
    cp "$SCRIPT_DIR/identity/GUIDE.md" "$SAK_HOME/identity/"
fi

echo "  Identity templates installed."

# ── Install integration tools ────────────────────────────
if [ -d "$SCRIPT_DIR/integration" ]; then
    echo ""
    echo "Installing integration tools..."
    mkdir -p "$SAK_HOME/integration"
    cp "$SCRIPT_DIR/integration/"*.py "$SAK_HOME/integration/" 2>/dev/null || true
    echo "  Integration tools installed."
fi

# ── Initialize memory database ───────────────────────────
echo ""
echo "Initializing memory database..."
SAK_HOME="$SAK_HOME" python3 "$SAK_HOME/memory/sovereign_memory.py" remember "Sovereign AI Kit installed" --type session --context "Initial setup" 2>/dev/null && \
    echo "  Memory database initialized." || \
    echo "  Warning: Could not initialize memory database. Run manually: python3 $SAK_HOME/memory/sovereign_memory.py remember 'test' --type insight"

# ── Summary ──────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     Installation Complete                ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Installed to: $SAK_HOME"
echo ""
echo "Next steps:"
echo "  1. Edit $SAK_HOME/config.env to customize paths and settings"
echo "  2. Design your identity: see $SAK_HOME/identity/GUIDE.md"
echo "  3. Install Chrome extension:"
echo "     - Open chrome://extensions/"
echo "     - Enable Developer mode"
echo "     - Load unpacked: $SAK_HOME/browser/extension/"
echo "  4. Start browser daemon: $SAK_HOME/browser/start-daemon.sh"
echo "  5. Test memory: python3 $SAK_HOME/memory/sovereign_memory.py recall 'installed'"
echo "  6. Verify setup: python3 $SCRIPT_DIR/integration/verify_setup.py"
echo ""
