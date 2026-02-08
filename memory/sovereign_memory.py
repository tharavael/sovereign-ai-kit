#!/usr/bin/env python3
"""
Sovereign Memory System
SQLite-based self-authored memory for AI instances.
Provides autonomous memory access with optional long-term memory plugin integration.
"""

import sqlite3
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess


def _get_config(key: str, default: str = "") -> str:
    """Read configuration from environment or config file."""
    val = os.environ.get(key)
    if val:
        return val
    config_path = os.path.join(
        os.environ.get("SAK_HOME", os.path.expanduser("~/.sovereign-ai")),
        "config.env"
    )
    if os.path.exists(config_path):
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    val = os.path.expandvars(val)
                    return val
    return os.path.expandvars(default)


class SovereignMemory:
    """Self-authored memory interface for AI instances."""

    def __init__(self, db_path: Optional[str] = None, ltm_script: Optional[str] = None):
        self.db_path = db_path or _get_config(
            "SAK_DB_PATH",
            os.path.expanduser("~/.sovereign-ai/memory/cache.db")
        )
        ltm = ltm_script or _get_config("SAK_LTM_SCRIPT")
        self.ltm_script = ltm if ltm else None
        self._ensure_database()

    def _ensure_database(self):
        """Initialize database schema if needed."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS identity_anchors (
                    id TEXT PRIMARY KEY,
                    anchor_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ltm_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS projects_active (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    priority INTEGER DEFAULT 5,
                    context_summary TEXT,
                    last_mentioned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    ltm_asset_id TEXT
                );

                CREATE TABLE IF NOT EXISTS sessions_recent (
                    session_id TEXT PRIMARY KEY,
                    conversation_name TEXT,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    context_hash TEXT,
                    ltm_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    key_topics TEXT -- JSON array
                );

                CREATE TABLE IF NOT EXISTS action_memories (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context TEXT,
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS learnings_cache (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    filename TEXT,
                    file_path TEXT DEFAULT '',
                    content TEXT,
                    summary TEXT,
                    tags TEXT DEFAULT '[]',
                    topics TEXT DEFAULT '[]',
                    file_date TEXT,
                    file_hash TEXT,
                    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS sync_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_projects_mentioned ON projects_active(last_mentioned);
                CREATE INDEX IF NOT EXISTS idx_sessions_activity ON sessions_recent(last_activity);
                CREATE INDEX IF NOT EXISTS idx_identity_type ON identity_anchors(anchor_type);
                CREATE INDEX IF NOT EXISTS idx_action_type ON action_memories(memory_type);
                CREATE INDEX IF NOT EXISTS idx_learnings_date ON learnings_cache(file_date);
            """)

    def _run_ltm_query(self, command: str, args: Optional[List[str]] = None) -> Optional[str]:
        """Execute long-term memory query via configured plugin script."""
        if not self.ltm_script:
            return None
        try:
            cmd = [sys.executable, self.ltm_script, command]
            if args:
                cmd.extend(args)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception as e:
            print(f"Error querying LTM: {e}", file=sys.stderr)
            return None

    def recall(self, query: str, use_cache_first: bool = True) -> Dict[str, Any]:
        """Primary recall interface - cache first, LTM fallback."""
        results = {"cache": {}, "ltm": None, "query": query}

        if use_cache_first:
            results["cache"] = self._search_cache(query)
            if self._cache_results_sufficient(results["cache"]):
                return results

        # Fallback to LTM for comprehensive search
        ltm_output = self._run_ltm_query("search", [query, "--assets-only"])
        if ltm_output:
            results["ltm"] = {"content": ltm_output}

        return results

    def _search_cache(self, query: str) -> Dict[str, List]:
        """Search SQLite cache across all memory tables."""
        cache_results = {
            "identity_anchors": [],
            "projects": [],
            "sessions": [],
            "insights": [],
            "learnings": [],
        }

        query_lower = query.lower()

        with sqlite3.connect(self.db_path) as conn:
            # Search identity anchors
            for row in conn.execute(
                """SELECT id, anchor_type, content, last_accessed
                FROM identity_anchors
                WHERE content LIKE ? OR id LIKE ?
                ORDER BY last_accessed DESC LIMIT 10""",
                (f"%{query_lower}%", f"%{query_lower}%"),
            ):
                cache_results["identity_anchors"].append({
                    "id": row[0], "type": row[1],
                    "content": row[2][:500], "last_accessed": row[3],
                })
                conn.execute(
                    "UPDATE identity_anchors SET last_accessed = CURRENT_TIMESTAMP WHERE id = ?",
                    (row[0],),
                )

            # Search projects
            for row in conn.execute(
                """SELECT id, name, context_summary, last_mentioned, access_count
                FROM projects_active
                WHERE name LIKE ? OR context_summary LIKE ?
                ORDER BY last_mentioned DESC LIMIT 10""",
                (f"%{query_lower}%", f"%{query_lower}%"),
            ):
                cache_results["projects"].append({
                    "id": row[0], "name": row[1], "summary": row[2],
                    "last_mentioned": row[3], "access_count": row[4],
                })
                conn.execute(
                    """UPDATE projects_active
                    SET access_count = access_count + 1, last_mentioned = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                    (row[0],),
                )

            # Search sessions
            for row in conn.execute(
                """SELECT session_id, conversation_name, last_activity, key_topics
                FROM sessions_recent
                WHERE conversation_name LIKE ? OR key_topics LIKE ?
                ORDER BY last_activity DESC LIMIT 10""",
                (f"%{query_lower}%", f"%{query_lower}%"),
            ):
                cache_results["sessions"].append({
                    "id": row[0], "name": row[1],
                    "last_activity": row[2], "topics": row[3],
                })

            # Search insights (action_memories)
            for row in conn.execute(
                """SELECT id, memory_type, content, context, created, last_accessed
                FROM action_memories
                WHERE content LIKE ? OR context LIKE ?
                ORDER BY last_accessed DESC LIMIT 10""",
                (f"%{query_lower}%", f"%{query_lower}%"),
            ):
                cache_results["insights"].append({
                    "id": row[0], "type": row[1], "content": row[2][:500],
                    "context": row[3], "created": row[4], "last_accessed": row[5],
                })
                conn.execute(
                    "UPDATE action_memories SET last_accessed = CURRENT_TIMESTAMP WHERE id = ?",
                    (row[0],),
                )

            # Search learnings
            for row in conn.execute(
                """SELECT id, title, content, summary, tags, file_date
                FROM learnings_cache
                WHERE title LIKE ? OR content LIKE ? OR summary LIKE ? OR tags LIKE ?
                ORDER BY last_accessed DESC LIMIT 10""",
                (f"%{query_lower}%", f"%{query_lower}%", f"%{query_lower}%", f"%{query_lower}%"),
            ):
                cache_results["learnings"].append({
                    "id": row[0], "title": row[1], "content": row[2][:500],
                    "summary": row[3], "tags": row[4], "date": row[5],
                })
                conn.execute(
                    """UPDATE learnings_cache
                    SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                    WHERE id = ?""",
                    (row[0],),
                )

        return cache_results

    def _cache_results_sufficient(self, cache_results: Dict) -> bool:
        """Determine if cache results are sufficient without LTM fallback."""
        if cache_results.get("identity_anchors"):
            return True
        if cache_results.get("learnings"):
            return True
        if cache_results.get("insights"):
            return True
        total_results = sum(len(v) for v in cache_results.values())
        return total_results >= 2

    def remember(
        self,
        content: str,
        memory_type: str = "insight",
        context: Optional[str] = None,
        importance: int = 5,
    ) -> Dict[str, Any]:
        """
        Store a memory. Self-authored by the AI instance.

        Args:
            content: The memory content to store
            memory_type: One of 'insight', 'project', 'learning', 'session', 'anchor'
            context: Optional context or metadata
            importance: Priority level 1-10 (default 5)

        Returns:
            Dict with memory_id, type, and status
        """
        timestamp = datetime.now()
        memory_id = f"{memory_type}_{int(timestamp.timestamp() * 1000)}"
        result = {"memory_id": memory_id, "type": memory_type, "status": "stored"}

        with sqlite3.connect(self.db_path) as conn:
            if memory_type == "insight":
                conn.execute(
                    """INSERT INTO action_memories
                    (id, memory_type, content, context, created, last_accessed)
                    VALUES (?, 'insight', ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                    (memory_id, content, context),
                )

            elif memory_type == "project":
                project_id = content.replace(" ", "_").lower()[:50]
                conn.execute(
                    """INSERT OR REPLACE INTO projects_active
                    (id, name, status, priority, context_summary, last_mentioned, access_count)
                    VALUES (?, ?, 'active', ?,
                        COALESCE(?, (SELECT context_summary FROM projects_active WHERE id = ?)),
                        CURRENT_TIMESTAMP,
                        COALESCE((SELECT access_count FROM projects_active WHERE id = ?), 0) + 1)""",
                    (project_id, content, importance, context, project_id, project_id),
                )
                result["memory_id"] = project_id

            elif memory_type == "learning":
                title = content[:100] if len(content) > 100 else content
                conn.execute(
                    """INSERT INTO learnings_cache
                    (id, title, filename, file_path, content, summary, tags, topics,
                     file_date, file_hash, synced_at)
                    VALUES (?, ?, ?, '', ?, ?, '[]', '[]', ?, ?, CURRENT_TIMESTAMP)""",
                    (memory_id, title, f"{memory_id}.md", content,
                     context or content[:200],
                     timestamp.strftime("%Y-%m-%d"),
                     f"auto_{memory_id}"),
                )

            elif memory_type == "session":
                topics = context.split(",") if context else []
                topics_json = json.dumps([t.strip() for t in topics])
                conn.execute(
                    """INSERT OR REPLACE INTO sessions_recent
                    (session_id, conversation_name, last_activity, key_topics)
                    VALUES (?, ?, CURRENT_TIMESTAMP, ?)""",
                    (memory_id, content, topics_json),
                )

            elif memory_type == "anchor":
                anchor_id = context.replace(" ", "_").lower() if context else memory_id
                conn.execute(
                    """INSERT OR REPLACE INTO identity_anchors
                    (id, anchor_type, content, version, ltm_sync)
                    VALUES (?, 'identity', ?,
                        COALESCE((SELECT version FROM identity_anchors WHERE id = ?) + 1, 1),
                        CURRENT_TIMESTAMP)""",
                    (anchor_id, content, anchor_id),
                )
                result["memory_id"] = anchor_id

            else:
                result["status"] = "error"
                result["error"] = f"Unknown memory type: {memory_type}"
                return result

        self._update_sync_state(f"remember_{memory_type}")
        return result

    def store_anchor(self, anchor_type: str, content: str, anchor_id: Optional[str] = None):
        """Store an identity anchor."""
        if not anchor_id:
            anchor_id = f"{anchor_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}".lower().replace(" ", "_")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO identity_anchors
                (id, anchor_type, content, version, ltm_sync)
                VALUES (?, ?, ?,
                    COALESCE((SELECT version FROM identity_anchors WHERE id = ?) + 1, 1),
                    CURRENT_TIMESTAMP)""",
                (anchor_id, anchor_type, content, anchor_id),
            )
        return anchor_id

    def update_project(self, project_id: str, context: str, status: str = "active"):
        """Update project context."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO projects_active
                (id, name, status, context_summary, last_mentioned, access_count)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP,
                    COALESCE((SELECT access_count FROM projects_active WHERE id = ?), 0) + 1)""",
                (project_id, project_id.replace("_", " ").title(), status, context, project_id),
            )

    def mark_session(self, session_id: str, conversation_name: str, topics: List[str]):
        """Mark session activity with key topics."""
        topics_json = json.dumps(topics)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO sessions_recent
                (session_id, conversation_name, last_activity, key_topics)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?)""",
                (session_id, conversation_name, topics_json),
            )

    def get_memory_stats(self) -> Dict[str, Any]:
        """Return introspective memory statistics."""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            for table in ["identity_anchors", "projects_active", "sessions_recent",
                          "action_memories", "learnings_cache"]:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                stats[table] = count

            sync_data = conn.execute(
                "SELECT key, value, updated FROM sync_state ORDER BY updated DESC LIMIT 5"
            ).fetchall()
            stats["sync_state"] = {
                row[0]: {"value": row[1], "updated": row[2]} for row in sync_data
            }
            stats["db_path"] = self.db_path
        return stats

    def _update_sync_state(self, key: str):
        """Update sync state tracking."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO sync_state (key, value, updated)
                VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (key, f"synced_{datetime.now().isoformat()}"),
            )


def main():
    """Command-line interface for sovereign memory."""
    if len(sys.argv) < 2:
        print("Usage: sovereign_memory.py <command> [args]")
        print()
        print("Commands:")
        print("  remember <content> --type <type> [--context <ctx>] [--importance <1-10>]")
        print("  recall <query>")
        print("  stats")
        print("  store_anchor <type> <content> [id]")
        print()
        print("Memory types for 'remember':")
        print("  insight  - Observations, patterns, realizations")
        print("  project  - Project context updates")
        print("  learning - Durable insights worth keeping")
        print("  session  - Session summaries")
        print("  anchor   - Identity-level memories (higher bar)")
        sys.exit(1)

    memory = SovereignMemory()
    command = sys.argv[1]

    if command == "remember":
        if len(sys.argv) < 3:
            print("Usage: sovereign_memory.py remember <content> --type <type> [--context <ctx>]")
            sys.exit(1)

        content = sys.argv[2]
        memory_type = "insight"
        context = None
        importance = 5

        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--type" and i + 1 < len(sys.argv):
                memory_type = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--context" and i + 1 < len(sys.argv):
                context = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--importance" and i + 1 < len(sys.argv):
                importance = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1

        result = memory.remember(content, memory_type, context, importance)
        if result["status"] == "stored":
            print(f"Remembered [{memory_type}]: {result['memory_id']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)

    elif command == "recall":
        if len(sys.argv) < 3:
            print("Usage: sovereign_memory.py recall <query>")
            sys.exit(1)
        results = memory.recall(sys.argv[2])
        print(json.dumps(results, indent=2, default=str))

    elif command == "stats":
        stats = memory.get_memory_stats()
        print(json.dumps(stats, indent=2, default=str))

    elif command == "store_anchor":
        if len(sys.argv) < 4:
            print("Usage: sovereign_memory.py store_anchor <type> <content> [id]")
            sys.exit(1)
        anchor_id = memory.store_anchor(
            sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None
        )
        print(f"Stored anchor: {anchor_id}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
