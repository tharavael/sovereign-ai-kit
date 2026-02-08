# Browser Automation

Chrome extension + HTTP daemon for AI-controlled browser interaction.

## Architecture

```
AI Client ──► browser.js (CLI) ──► Unix Socket ──► browser-daemon.js ──► HTTP ──► Chrome Extension
                                                        ▲
                                                   Port 19222
                                                        │
                                                   Extension polls
                                                   via Alarms API
```

**Why HTTP polling?** Chrome aggressively kills native messaging hosts on disconnection. HTTP polling via the Alarms API survives tab closes, extension reloads, and browser restarts. The extension polls every 100ms during active commands.

## Setup

### 1. Install

```bash
./install.sh
# Or use the master installer: ../setup.sh
```

### 2. Load Chrome Extension

1. Open `chrome://extensions/`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select `~/.sovereign-ai/browser/extension/`

### 3. Start Daemon

```bash
~/.sovereign-ai/browser/start-daemon.sh
```

## Commands

```bash
NODE=node
BROWSER="$NODE ~/.sovereign-ai/browser/scripts/browser.js"

# Navigation
$BROWSER navigate "https://example.com"

# Query DOM (CSS selector)
$BROWSER query "h1"
$BROWSER query ".article-content p"

# Click element
$BROWSER click "button.submit"
$BROWSER click "a.next-page" 2          # Click 3rd match (0-indexed)

# Type into field
$BROWSER type "input#search" "search query"

# Screenshot
$BROWSER screenshot

# List tabs
$BROWSER get_tabs
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SAK_BROWSER_PORT` | `19222` | Daemon HTTP port |
| `SAK_BROWSER_SKILL_DIR` | `$SAK_HOME/browser` | Installation directory |
| `SAK_HOME` | `~/.sovereign-ai` | Root directory |

The Chrome extension port can also be configured via `chrome.storage.local` in the extension options.

## Troubleshooting

**Daemon not starting:** Check `~/.sovereign-ai/browser/daemon.log` and verify Node.js is installed.

**Extension not connecting:** Verify the daemon is running (`curl http://localhost:19222/health`) and the extension is loaded in Chrome.

**Queries returning null:** The page may not have loaded yet. Add a short delay after `navigate` before querying, or check that the CSS selector is correct.
