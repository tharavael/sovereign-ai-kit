# Body System

Action coordination with sequential queuing, undo support, and sandbox enforcement.

## Architecture

The body system wraps memory, browser, and file operations in a controlled execution framework:

```
body_cli.py ──► BodyCoordinator ──► ActionQueue (sequential, threaded)
                     │                    │
                     ├── BodyMemory       ├── Permission check
                     ├── BodyBrowser      ├── Execute action
                     └── BodyFiles        ├── Log to journal
                                          └── Push to UndoStack
```

## Usage

```bash
# Execute an action
python3 body_cli.py execute memory store '{"content": "test insight", "type": "insight"}'
python3 body_cli.py execute browser navigate '{"url": "https://example.com"}'
python3 body_cli.py execute file read '{"path": "~/.sovereign-ai/config.env"}'

# Check status
python3 body_cli.py status

# Undo last action
python3 body_cli.py undo

# Grant temporary path permission
python3 body_cli.py grant /tmp/project --minutes 30

# Memory-action triggers
python3 body_cli.py add-trigger --type keyword --keywords "error,bug,crash" \
    --action-type browser --command navigate \
    --action-args '{"url": "https://github.com/issues"}'

python3 body_cli.py list-triggers
```

## Action Levels

| Level | Actions | Permission |
|-------|---------|------------|
| `AUTONOMOUS` | Memory store/recall, browser navigate/query | No confirmation needed |
| `PERMISSION` | File write outside sandbox, system commands | Requires user approval |
| `FORBIDDEN` | Destructive operations | Always blocked |

## Sandbox

The body system enforces a file sandbox. By default, the AI can only write within `$SAK_HOME` (`~/.sovereign-ai/`). Access outside this boundary requires explicit grants:

```bash
# Grant 60 minutes of access to a project directory
python3 body_cli.py grant /home/user/project --minutes 60
```

## Memory-Action Triggers

The body system can automatically fire actions when specific keywords appear in stored memories. This enables autonomous behavior chains — storing a memory about an error can automatically trigger a browser search for solutions.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SAK_HOME` | `~/.sovereign-ai` | Root directory |
| `SAK_DB_PATH` | `$SAK_HOME/memory/cache.db` | Action journal database |
| `SAK_SANDBOX_PATH` | `$SAK_HOME` | File operation boundary |
