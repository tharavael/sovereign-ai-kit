# Memory System

SQLite-based sovereign memory with self-authored storage and recall.

## Usage

```bash
# Remember something
python3 sovereign_memory.py remember "Docker needs --network host for local DB" --type learning

# Recall by keyword
python3 sovereign_memory.py recall "docker"

# View statistics
python3 sovereign_memory.py stats
```

## Memory Types

| Type | Purpose | Example |
|------|---------|---------|
| `insight` | Observations and realizations | "HTTP polling beats native messaging for Chrome extensions" |
| `project` | Project-specific context | "sovereign-ai-kit uses MIT license, SAK_HOME for paths" |
| `learning` | Technical knowledge | "SQLite WAL mode enables concurrent reads" |
| `session` | Session summaries | "Completed browser automation generalization" |
| `anchor` | Identity-level (high bar) | "Memory sovereignty means the AI decides what to remember" |

## Database Schema

Seven tables in `cache.db`:
- `memories` — Primary memory store with full-text search
- `memory_fts` — FTS5 virtual table for search
- `recall_log` — Track what was recalled and when
- `context_tags` — Tag memories with context
- `memory_links` — Link related memories
- `sync_log` — LTM sync tracking
- `learnings_sync` — Learnings folder sync state

## Optional LTM Plugin

For semantic search beyond keyword matching, configure an LTM plugin:

```env
SAK_LTM_PLUGIN="pieces"
SAK_LTM_SCRIPT="/path/to/query_script.py"
```

The plugin base class is in `plugins/base_plugin.py`.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SAK_HOME` | `~/.sovereign-ai` | Root directory |
| `SAK_DB_PATH` | `$SAK_HOME/memory/cache.db` | Database path |
| `SAK_LEARNINGS_DIR` | `$SAK_HOME/history/learnings` | Learnings export dir |
