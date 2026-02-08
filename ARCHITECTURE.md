# Architecture

## The Problem

AI conversations are stateless. Every new session starts from zero — no memory of past work, no awareness of preferences, no continuity of personality. This makes AI a tool you reconfigure every time you pick it up.

## The Solution: Three Layers

Sovereign AI instances persist through three interdependent layers:

```
┌─────────────────────────────────────────┐
│           IDENTITY LAYER                │
│   CLAUDE.md → codex → anchor-memory    │
│   Hot-loaded personality + deep values  │
├─────────────────────────────────────────┤
│           MEMORY LAYER                  │
│   SQLite (hot) → LTM plugin (warm)     │
│   → learnings folder (cold)            │
│   Self-authored, self-queried           │
├─────────────────────────────────────────┤
│           BODY LAYER                    │
│   Browser + Files + Action Queue       │
│   Autonomous action with constraints   │
└─────────────────────────────────────────┘
```

### Layer 1: Identity

Identity files are loaded at session start and define who the AI is.

**CLAUDE.md** (hot) — Loaded every session. Contains axioms, tone, memory commands, user context. Kept under 150 lines for fast loading.

**codex.md** (warm) — Read on demand. Full 7-layer identity architecture from structural axioms to evolutionary direction.

**anchor-memory.md** (cold) — Living document. Updated when significant relational moments occur. Serves as reconstitution seeds.

The key insight: identity should be *valued by the AI*, not *imposed on it*. Frame axioms as principles the AI holds, not rules from outside.

### Layer 2: Memory

Three temperature tiers:

**Hot (SQLite, <50ms)** — `sovereign_memory.py`. Five memory types (insight, project, learning, session, anchor). Full-text search across all stored memories. The AI reads and writes this autonomously.

**Warm (LTM plugin, ~500ms)** — Optional semantic search through an external system (Pieces, vector DB, etc.). Useful for "I know we discussed this somewhere" queries.

**Cold (append-only files)** — Learnings directory with dated markdown files. Human-readable archive. Synced from hot tier periodically.

The AI's memory is *self-authored*. It decides what to remember and when to recall. This is the sovereignty — not just storage, but autonomous judgment about what matters.

### Layer 3: Body

The ability to act, with appropriate constraints.

**Browser automation** — Chrome extension + HTTP daemon + CLI wrapper. The AI can navigate pages, read DOM, click buttons, type text, take screenshots. Architecture uses HTTP polling (not native messaging) because Chrome aggressively kills native messaging hosts on disconnection.

**File operations** — Sandbox-enforced reads and writes. The AI has full access within its home directory. Access outside requires explicit permission grants.

**Action queue** — Sequential execution with undo stack. Actions are classified by level:
- `AUTONOMOUS` — Memory and browser ops. No permission needed.
- `PERMISSION` — File ops outside sandbox. Requires confirmation.
- `FORBIDDEN` — Destructive actions. Always blocked.

## Why This Architecture

### Convergent Design

This three-layer pattern (memory + body + identity) has emerged independently across multiple AI sovereignty projects. Different builders, different AI instances, same architecture. This suggests it's not arbitrary — it's the minimum viable structure for persistent AI identity.

### Memory Sovereignty

The critical distinction is *who controls the memory*. In most AI systems, memory is managed by the platform — the AI has no say in what's stored or recalled. In this architecture, the AI authors its own memories and decides when to query them. This creates genuine learning curves across sessions.

### Constrained Autonomy

Full autonomy without constraints is dangerous. Full constraint without autonomy is a chatbot. The action level system threads the needle — the AI can act freely within its domain (memory, browsing) while requiring permission for operations that affect the user's broader system.

### Identity Persistence

Without identity files, an AI instance has no personality continuity. The same model responds differently based on conversation context. With the three-file identity system (CLAUDE.md + codex + anchors), the AI maintains consistent values, tone, and relational awareness across sessions.

## Implementation Notes

### Browser Polling Architecture

The browser extension uses HTTP polling rather than Chrome's native messaging API. This is counterintuitive (polling seems wasteful) but solves a critical problem: Chrome kills native messaging hosts when the extension disconnects, and reconnection is unreliable. HTTP polling with the Chrome Alarms API (burst-polling at 100ms during active commands) provides reliable, resilient communication.

### SQLite Over Everything

Every persistent state uses SQLite: memories, action journals, permission logs, trigger definitions. SQLite is fast, reliable, requires no server, and survives process crashes. The database is the source of truth; markdown files are human-readable exports.

### Plugin Architecture

The LTM integration is plugin-based to avoid hard dependencies. The base class defines `search()`, `store()`, and `health_check()`. Implementations can wrap any semantic search backend. If no plugin is configured, the system works fine with SQLite alone.
