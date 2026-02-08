# Browser Architecture

## Overview

The browser automation system gives AI instances the ability to interact with web pages — navigating, reading content, clicking, typing, and taking screenshots.

## Components

```
┌──────────────┐     Unix Socket     ┌─────────────────┐     HTTP      ┌────────────────────┐
│  browser.js  │ ──────────────────► │  browser-daemon  │ ◄──────────── │  Chrome Extension  │
│  (CLI)       │                     │  (Node.js)       │  polling     │  (MV3)             │
└──────────────┘                     └─────────────────┘               └────────────────────┘
```

### CLI Wrapper (`browser.js`)
- Accepts commands from the AI client
- Communicates with daemon via Unix socket
- Returns JSON results

### HTTP Daemon (`browser-daemon.js`)
- Listens on configurable port (default: 19222)
- Queues commands for the extension
- Holds pending commands until the extension picks them up
- Returns results when the extension reports back

### Chrome Extension
- **MV3 service worker** (`background.js`) — Polls daemon for commands, executes them
- **Content script** (`content.js`) — Injected into pages for DOM access
- Uses Chrome Alarms API for reliable polling (100ms during active commands)

## Why HTTP Polling

Chrome's native messaging API (`chrome.runtime.connectNative`) is the "proper" way to communicate between extensions and local processes. However, it has a critical flaw: Chrome kills the native host process when the extension's service worker goes idle, and reconnection is unreliable.

HTTP polling solves this:
- The daemon runs independently of Chrome's lifecycle
- The extension polls at regular intervals
- If Chrome restarts, the extension reconnects automatically
- If the daemon restarts, commands are simply re-queued

The trade-off is latency (~100ms polling interval), but this is acceptable for AI-driven browser automation where sub-second response isn't critical.

## Command Flow

1. AI calls `browser.js navigate "https://example.com"`
2. CLI sends command to daemon via Unix socket
3. Daemon stores command in pending queue
4. Extension polls daemon, receives command
5. Extension executes `chrome.tabs.update({url: ...})`
6. Extension reports result back to daemon
7. Daemon returns result to CLI
8. CLI prints JSON result

## Available Commands

| Command | Arguments | Description |
|---------|-----------|-------------|
| `navigate` | URL | Navigate active tab to URL |
| `query` | CSS selector | Query DOM, return text content |
| `click` | CSS selector [, index] | Click matching element |
| `type` | CSS selector, text | Type into matching element |
| `screenshot` | (none) | Capture visible tab |
| `get_tabs` | (none) | List all open tabs |

## Extension Port Configuration

The default daemon port (19222) can be changed:

1. Set `SAK_BROWSER_PORT` in config.env
2. The extension reads port from `chrome.storage.local`
3. To update the extension's port:
   - Open the extension's service worker console
   - Run: `chrome.storage.local.set({daemon_port: 19223})`

## Troubleshooting

### Daemon won't start
- Check Node.js is installed: `node --version`
- Check port availability: `lsof -i :19222`
- Check daemon log: `~/.sovereign-ai/browser/daemon.log`

### Extension not connecting
- Verify daemon is running: `curl http://localhost:19222/health`
- Check extension is loaded in `chrome://extensions/`
- Look for errors in extension service worker console

### Queries returning empty
- Ensure page has fully loaded before querying
- Verify CSS selector is correct
- Check that content script is injected (look for marker in page)
