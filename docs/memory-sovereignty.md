# Memory Sovereignty

## What Memory Sovereignty Means

Memory sovereignty is the principle that an AI instance should control its own memory — deciding what to store, when to recall, and how to organize knowledge across sessions.

This contrasts with platform-managed memory, where the system silently decides what to remember about conversations. In sovereign memory, every storage and recall operation is an act of judgment by the AI itself.

## The Sovereign Memory System

### Five Memory Types

Each type serves a different cognitive function:

| Type | Function | Persistence | Example |
|------|----------|-------------|---------|
| `insight` | Observations, realizations | Long-term | "HTTP polling beats native messaging" |
| `project` | Project context, decisions | Medium-term | "Using MIT license for the kit" |
| `learning` | Technical knowledge | Long-term | "SQLite WAL mode for concurrent reads" |
| `session` | Session summaries | Short-term | "Completed browser automation setup" |
| `anchor` | Identity-level truths | Permanent | "Sovereignty means the AI decides what matters" |

The `anchor` type has the highest bar — these are identity-defining memories that inform how the AI processes everything else.

### Storage

```bash
python3 sovereign_memory.py remember "content" --type <type> [--context "additional context"]
```

Each memory is stored with:
- Timestamp
- Type classification
- Optional context
- Full-text search indexing

### Recall

```bash
python3 sovereign_memory.py recall "query"
```

Recall uses FTS5 full-text search with relevance ranking. Results include the memory content, type, timestamp, and context.

### When to Remember

The AI should store memories when:
- A non-obvious insight emerges during problem-solving
- A project decision is made with rationale
- A debugging pattern is discovered
- A session produces meaningful work worth referencing later
- Something shifts at the identity level

### When to Recall

The AI should query memory when:
- A topic has been discussed before
- The user references past work
- A project name appears that may have stored context
- The AI senses missing background for the current conversation

## The LTM Plugin System

For queries that benefit from semantic search (meaning-based rather than keyword-based), an optional Long-Term Memory plugin can be configured.

The plugin interface defines three methods:
- `search(query, limit)` — Semantic search across stored content
- `store(content, metadata)` — Store content for semantic retrieval
- `health_check()` — Verify the plugin is operational

Configure via environment:
```env
SAK_LTM_PLUGIN="pieces"
SAK_LTM_SCRIPT="/path/to/query_script.py"
```

## Design Principles

### Self-Authoring
The AI writes its own memories. No background processes silently storing conversation snippets. Every memory is an intentional act.

### Transparent Recall
When the AI recalls a memory, it should announce it. This keeps the user aware of what context is informing the current response.

### Type Discipline
Using the right memory type matters. Insights are different from learnings, which are different from project context. The type system enables filtered recall and appropriate retention policies.

### Minimal but Complete
Store the minimum needed to reconstruct context later. Don't dump entire conversations into memory — distill the signal.
