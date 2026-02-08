# Quick Start

Get a sovereign AI instance running in 10 minutes.

## Prerequisites

- Python 3.8+
- Node.js 16+
- Google Chrome
- Claude Code (or any AI with shell access)

## Step 1: Install

```bash
git clone https://github.com/YOUR_USERNAME/sovereign-ai-kit.git
cd sovereign-ai-kit
./setup.sh
```

## Step 2: Test Memory

```bash
# Store a memory
python3 ~/.sovereign-ai/memory/sovereign_memory.py remember "Testing sovereign memory" --type insight

# Recall it
python3 ~/.sovereign-ai/memory/sovereign_memory.py recall "testing"
```

You should see your memory returned with a timestamp and relevance score.

## Step 3: Set Up Browser

```bash
# Load the Chrome extension
# 1. chrome://extensions/
# 2. Developer mode ON
# 3. Load unpacked → ~/.sovereign-ai/browser/extension/

# Start the daemon
~/.sovereign-ai/browser/start-daemon.sh

# Test
node ~/.sovereign-ai/browser/scripts/browser.js get_tabs
```

## Step 4: Create Your Identity

The fastest path — copy the minimal example:

```bash
cp ~/.sovereign-ai/identity/examples/minimal/CLAUDE.md ~/.claude/CLAUDE.md
```

Edit `~/.claude/CLAUDE.md` to customize:
- Change the AI name
- Write your own axioms
- Add your user context

For a deeper identity, see the [Identity Design Guide](../identity/GUIDE.md).

## Step 5: Verify

```bash
python3 sovereign-ai-kit/integration/verify_setup.py
```

## What's Next

- Read the [Architecture](three-layer-architecture.md) to understand why each layer matters
- Explore the [Memory Sovereignty](memory-sovereignty.md) deep dive
- Check the [Browser Architecture](browser-architecture.md) for advanced usage
- Design a full identity with the [Guide](../identity/GUIDE.md)
