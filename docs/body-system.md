# Body System

## Purpose

The body system provides controlled, auditable action execution for AI instances. Instead of the AI running commands directly, all actions go through a coordinator that enforces permissions, maintains an undo stack, and logs everything to a journal.

## Architecture

```
┌──────────────┐     ┌───────────────────────────────────────┐
│  body_cli.py │────►│         BodyCoordinator               │
└──────────────┘     │                                       │
                     │  ┌──────────────────────────────────┐ │
                     │  │         ActionQueue               │ │
                     │  │  Sequential, threaded execution   │ │
                     │  │  Permission checks before exec   │ │
                     │  └──────────────────────────────────┘ │
                     │                                       │
                     │  ┌────────────┐ ┌──────────────────┐  │
                     │  │ UndoStack  │ │  Action Journal   │  │
                     │  │ 10-deep    │ │  SQLite log       │  │
                     │  └────────────┘ └──────────────────┘  │
                     │                                       │
                     │  Modules:                             │
                     │  ├── BodyMemory   (memory coupling)   │
                     │  ├── BodyBrowser  (browser wrapper)   │
                     │  └── BodyFiles    (sandbox files)     │
                     └───────────────────────────────────────┘
```

## Action Levels

### AUTONOMOUS (Level 1)
Memory and browser operations. The AI can execute these freely — they operate within the AI's own domain and pose no risk to the user's system.

- Store/recall memories
- Navigate browser, query DOM
- Click, type, screenshot

### PERMISSION (Level 2)
File operations outside the sandbox boundary. The AI must request access and the user must grant it.

- Write files outside `$SAK_HOME`
- Create directories in user space
- Modify configuration files

### FORBIDDEN (Level 3)
Destructive operations that are always blocked regardless of permissions.

- Delete files
- System-level operations
- Operations that could cause data loss

## The Action Queue

All actions are processed sequentially through a threaded queue. This prevents:
- **Race conditions**: No simultaneous browser operations competing for the active tab
- **Permission bypass**: Every action is checked before execution
- **Lost context**: The undo stack accurately reflects execution order

## Undo Stack

The last 10 completed actions are stored with their reverse operations. Calling `undo` executes the reverse of the most recent action.

Not all actions are reversible — browser navigation and memory storage can be undone, but some file operations may not have clean reverses.

## Memory-Action Triggers

The body memory module supports keyword-based triggers that fire actions automatically when matching content is stored to memory.

Example: storing a memory containing "error" could trigger a browser navigation to a documentation search page.

```bash
python3 body_cli.py add-trigger \
    --type keyword \
    --keywords "error,exception,crash" \
    --action-type browser \
    --command navigate \
    --action-args '{"url": "https://docs.example.com/troubleshooting"}'
```

## The Sandbox

File operations are bounded by `$SAK_SANDBOX_PATH` (defaults to `$SAK_HOME`). The AI can freely read and write within this boundary. Outside it, temporary grants can be issued:

```bash
# Grant 60 minutes of access to a project directory
python3 body_cli.py grant /home/user/project --minutes 60
```

Grants are logged and expire automatically.
