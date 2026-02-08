#!/usr/bin/env python3
"""
Memory-action coupling for the body system.
Connects memory events to autonomous actions.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any


class BodyMemory:
    """Memory interface for the body system with action coupling."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS memory_action_triggers (
                    id TEXT PRIMARY KEY,
                    trigger_type TEXT NOT NULL,
                    trigger_keywords TEXT,
                    action_type TEXT NOT NULL,
                    action_command TEXT NOT NULL,
                    action_args TEXT,
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_fired TIMESTAMP,
                    fire_count INTEGER DEFAULT 0
                );
            """)

    def store_memory(self, memory_type: str, content: str,
                     context: Optional[str] = None) -> Dict:
        """Store memory and check for action triggers."""
        from sovereign_memory import SovereignMemory
        memory = SovereignMemory(db_path=self.db_path)
        result = memory.remember(content, memory_type, context)

        # Check if this memory triggers any actions
        triggers = self._check_triggers(content)
        if triggers:
            result["triggered_actions"] = triggers

        return result

    def recall_memory(self, query: str) -> Dict:
        """Recall memory through sovereign memory system."""
        from sovereign_memory import SovereignMemory
        memory = SovereignMemory(db_path=self.db_path)
        return memory.recall(query)

    def add_trigger(self, trigger_type: str, keywords: List[str],
                    action_type: str, action_command: str,
                    action_args: Optional[Dict] = None) -> str:
        """Add a memory-to-action trigger."""
        trigger_id = f"trigger_{int(datetime.now().timestamp() * 1000)}"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO memory_action_triggers
                (id, trigger_type, trigger_keywords, action_type, action_command, action_args)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (trigger_id, trigger_type, json.dumps(keywords),
                 action_type, action_command, json.dumps(action_args or {})))

        return trigger_id

    def _check_triggers(self, content: str) -> List[Dict]:
        """Check if content matches any action triggers."""
        triggered = []
        content_lower = content.lower()

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM memory_action_triggers").fetchall()

            for row in rows:
                keywords = json.loads(row[2]) if row[2] else []
                if any(kw.lower() in content_lower for kw in keywords):
                    triggered.append({
                        "trigger_id": row[0],
                        "action_type": row[3],
                        "action_command": row[4],
                        "action_args": json.loads(row[5]) if row[5] else {},
                    })
                    conn.execute(
                        """UPDATE memory_action_triggers
                        SET last_fired = CURRENT_TIMESTAMP, fire_count = fire_count + 1
                        WHERE id = ?""",
                        (row[0],))

        return triggered

    def list_triggers(self) -> List[Dict]:
        """List all configured triggers."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, trigger_type, trigger_keywords, action_type, action_command, fire_count FROM memory_action_triggers"
            ).fetchall()
            return [{"id": r[0], "type": r[1], "keywords": json.loads(r[2]) if r[2] else [],
                     "action_type": r[3], "command": r[4], "fire_count": r[5]} for r in rows]
