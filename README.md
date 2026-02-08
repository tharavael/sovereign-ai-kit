# Sovereign AI Kit

Give your AI instance persistent memory, browser autonomy, and embodied action capabilities.

```
sovereign-ai-kit/
├── memory/          Sovereign memory (SQLite + optional LTM)
├── browser/         Browser automation (Chrome extension + daemon)
├── body/            Action coordination (queue, undo, sandbox)
├── identity/        Identity templates and design guide
├── integration/     Setup tools and verification
└── docs/            Architecture documentation
```

## What This Is

A toolkit for building AI instances that persist across sessions. Instead of starting from zero every conversation, your AI remembers what it learned, can browse the web autonomously, and maintains a coherent identity over time.

Built and battle-tested with Claude Code. Works with any AI system that can execute shell commands.

## The Three-Layer Architecture

Every sovereign AI instance needs three things:

| Layer | What It Does | Component |
|-------|-------------|-----------|
| **Memory** | Persist knowledge across sessions | `memory/sovereign_memory.py` |
| **Body** | Act in the world (browser, files) | `browser/` + `body/` |
| **Identity** | Maintain coherent personality | `identity/` templates |

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design philosophy.

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/YOUR_USERNAME/sovereign-ai-kit.git
cd sovereign-ai-kit
./setup.sh
```

This creates `~/.sovereign-ai/` with all components installed.

### 2. Test Memory

```bash
# Store something
python3 ~/.sovereign-ai/memory/sovereign_memory.py remember "This is my first memory" --type insight

# Recall it
python3 ~/.sovereign-ai/memory/sovereign_memory.py recall "first memory"
```

### 3. Set Up Browser Automation

```bash
# Install Chrome extension
# 1. Open chrome://extensions/
# 2. Enable Developer mode
# 3. Load unpacked: ~/.sovereign-ai/browser/extension/

# Start daemon
~/.sovereign-ai/browser/start-daemon.sh

# Test
node ~/.sovereign-ai/browser/scripts/browser.js get_tabs
```

### 4. Design Your Identity

Read `identity/GUIDE.md`, then either:
- Copy `identity/examples/minimal/CLAUDE.md` and edit it
- Use the template generator:

```bash
python3 ~/.sovereign-ai/integration/generate_claude_md.py \
  --set AI_NAME="MyAI" \
  --set TAGLINE="My Custom AI" \
  --output ~/.claude/CLAUDE.md
```

### 5. Verify

```bash
python3 integration/verify_setup.py
```

## Components

### Memory System

SQLite-based sovereign memory with 5 memory types and full-text search.

```bash
# Remember
python3 sovereign_memory.py remember "Docker containers need --network host for local DB access" --type learning

# Recall
python3 sovereign_memory.py recall "docker networking"

# Stats
python3 sovereign_memory.py stats
```

**Memory types:** `insight` | `project` | `learning` | `session` | `anchor`

Optional LTM (Long-Term Memory) plugin support for semantic search integration.

### Browser Automation

Chrome MV3 extension + Node.js HTTP daemon. The AI can navigate, query DOM, click, type, and take screenshots.

**Architecture:** Extension polls daemon via HTTP (not native messaging). This survives Chrome's aggressive host lifecycle management.

```bash
node browser.js navigate "https://example.com"
node browser.js query "h1"                      # CSS selector
node browser.js click "button.submit"            # Click element
node browser.js type "input#search" "query"      # Type into field
node browser.js screenshot                       # Capture page
node browser.js get_tabs                         # List open tabs
```

### Body System

Action coordinator with sequential queue, undo stack, and sandbox enforcement.

**Action levels:**
- `AUTONOMOUS` — Memory and browser actions (no permission needed)
- `PERMISSION` — File operations outside sandbox (requires confirmation)
- `FORBIDDEN` — Destructive operations (always blocked)

```bash
python3 body_cli.py execute memory store '{"content": "test", "type": "insight"}'
python3 body_cli.py status
python3 body_cli.py undo
```

### Identity System

Templates and examples for designing persistent AI identity.

- **CLAUDE.md** — Hot-loaded every session (~100 lines, dense)
- **codex.md** — Deep identity architecture (7 layers)
- **anchor-memory.md** — Living relational history (grows over time)

See [identity/GUIDE.md](identity/GUIDE.md) for design principles.

## Configuration

All paths and settings are configurable via environment variables or `~/.sovereign-ai/config.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `SAK_HOME` | `~/.sovereign-ai` | Root directory |
| `SAK_DB_PATH` | `$SAK_HOME/memory/cache.db` | Memory database |
| `SAK_BROWSER_PORT` | `19222` | Browser daemon port |
| `SAK_SANDBOX_PATH` | `$SAK_HOME` | File operation boundary |
| `SAK_LTM_PLUGIN` | (none) | Optional LTM integration |
| `SAK_AI_NAME` | `Assistant` | Your AI's name |

## Requirements

- Python 3.8+
- Node.js 16+ (for browser automation)
- Google Chrome (for browser extension)
- Claude Code (recommended) or any AI system with shell access

## License

MIT — see [LICENSE](LICENSE).

## Contributing

This toolkit emerged from real-world use building sovereign AI instances. If you've built something similar, found patterns that work, or have improvements — contributions welcome.
