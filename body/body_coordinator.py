#!/usr/bin/env python3
"""
Body Coordinator - Embodied action system for AI instances
Sequential action queuing with sandbox enforcement and undo/redo support.
"""

import sqlite3
import json
import sys
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import threading
import queue


def _get_config(key: str, default: str = "") -> str:
    """Read configuration from environment."""
    val = os.environ.get(key)
    if val:
        return os.path.expandvars(val)
    return os.path.expandvars(default)


class ActionLevel(Enum):
    AUTONOMOUS = 1   # Memory, browser — no permission needed
    PERMISSION = 2   # File writing outside sandbox — interactive prompt
    FORBIDDEN = 3    # Deletion, system changes — blocked


class ActionType(Enum):
    MEMORY = "memory"
    BROWSER = "browser"
    FILE = "file"
    QUEUE = "queue"


@dataclass
class Action:
    id: str
    type: ActionType
    level: ActionLevel
    command: str
    args: Dict[str, Any]
    reverse_operation: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    priority: int = 5
    completed: bool = False
    result: Optional[Any] = None
    error: Optional[str] = None


class UndoStack:
    """Reverse operation tracking with configurable depth."""

    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.stack: List[Action] = []
        self.redo_stack: List[Action] = []

    def push_action(self, action: Action):
        if action.reverse_operation:
            self.stack.append(action)
            if len(self.stack) > self.max_size:
                self.stack.pop(0)
            self.redo_stack.clear()

    def undo(self) -> Optional[Action]:
        if not self.stack:
            return None
        action = self.stack.pop()
        self.redo_stack.append(action)
        return action

    def redo(self) -> Optional[Action]:
        if not self.redo_stack:
            return None
        action = self.redo_stack.pop()
        self.stack.append(action)
        return action

    def clear(self):
        self.stack.clear()
        self.redo_stack.clear()


class ActionQueue:
    """Sequential action processing with priority support."""

    def __init__(self, body_system):
        self.body_system = body_system
        self.queue = queue.PriorityQueue()
        self.active = False
        self.current_action: Optional[Action] = None
        self.thread = None
        self.paused = False

    def add_action(self, action: Action):
        priority = (action.priority, action.timestamp.timestamp())
        self.queue.put((priority, action))

    def start(self):
        if self.active:
            return
        self.active = True
        self.paused = False
        self.thread = threading.Thread(target=self._process_queue)
        self.thread.daemon = True
        self.thread.start()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def clear(self):
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

    def _process_queue(self):
        while self.active:
            if self.paused:
                time.sleep(0.1)
                continue

            try:
                priority, action = self.queue.get(timeout=0.1)
                self.current_action = action

                if action.level == ActionLevel.PERMISSION:
                    if not self._request_permission(action):
                        continue
                elif action.level == ActionLevel.FORBIDDEN:
                    print(f"Blocked forbidden action: {action.command}", file=sys.stderr)
                    continue

                self.body_system._execute_action(action)

                if action.completed and action.reverse_operation:
                    self.body_system.undo_stack.push_action(action)

                self.current_action = None
                self.queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Action queue error: {e}", file=sys.stderr)
                time.sleep(1)

    def _request_permission(self, action: Action) -> bool:
        print(f"\nPermission requested:")
        print(f"  Action: {action.command}")
        print(f"  Details: {json.dumps(action.args, indent=2)}")
        print("Proceed? (y/n) ", end="", flush=True)
        try:
            response = input().strip().lower()
            return response in ["y", "yes"]
        except (EOFError, KeyboardInterrupt):
            return False


class BodyCoordinator:
    """Main body system coordinator with sovereign agency."""

    def __init__(self, sandbox_path: Optional[str] = None, db_path: Optional[str] = None):
        sak_home = _get_config("SAK_HOME", os.path.expanduser("~/.sovereign-ai"))
        self.sandbox_path = sandbox_path or _get_config("SAK_SANDBOX_PATH", sak_home)
        self.db_path = db_path or _get_config("SAK_DB_PATH",
                                               os.path.join(sak_home, "memory", "cache.db"))

        self.undo_stack = UndoStack()
        self.action_queue = ActionQueue(self)
        self.browser = None
        self.files = None
        self.memory = None

        self.session_permissions: Dict[str, datetime] = {}

        self._ensure_body_database()
        self._load_modules()
        self.action_queue.start()

    def _ensure_body_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS action_journal (
                    id TEXT PRIMARY KEY,
                    action_type TEXT NOT NULL,
                    command TEXT NOT NULL,
                    args TEXT,
                    result TEXT,
                    error TEXT,
                    completed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reverse_operation TEXT
                );
                CREATE TABLE IF NOT EXISTS permissions_log (
                    path TEXT,
                    granted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_action_journal_type ON action_journal(action_type);
                CREATE INDEX IF NOT EXISTS idx_permissions_path ON permissions_log(path);
            """)

    def _load_modules(self):
        body_dir = os.path.dirname(os.path.abspath(__file__))
        if body_dir not in sys.path:
            sys.path.insert(0, body_dir)

        try:
            from body_browser import BodyBrowser
            self.browser = BodyBrowser()
        except ImportError:
            pass

        try:
            from body_files import BodyFiles
            self.files = BodyFiles(self.sandbox_path)
        except ImportError:
            pass

        try:
            from body_memory import BodyMemory
            self.memory = BodyMemory(self.db_path)
        except ImportError:
            pass

    def execute_action(self, action_type: str, command: str,
                       args: Optional[Dict[str, Any]] = None,
                       level: ActionLevel = ActionLevel.AUTONOMOUS,
                       priority: int = 5) -> str:
        action_id = f"{action_type}_{int(time.time() * 1000)}"
        action = Action(
            id=action_id, type=ActionType(action_type), level=level,
            command=command, args=args or {}, timestamp=datetime.now(),
            priority=priority,
        )
        self.action_queue.add_action(action)
        return action_id

    def _execute_action(self, action: Action) -> bool:
        try:
            if action.type == ActionType.MEMORY:
                action.result = self._execute_memory_action(action)
            elif action.type == ActionType.BROWSER:
                action.result = self._execute_browser_action(action)
            elif action.type == ActionType.FILE:
                action.result = self._execute_file_action(action)
            else:
                raise ValueError(f"Unknown action type: {action.type}")

            action.completed = True
            self._log_action(action)
            return True

        except Exception as e:
            action.error = str(e)
            self._log_action(action)
            print(f"Action error: {e}", file=sys.stderr)
            return False

    def _execute_memory_action(self, action: Action) -> Any:
        if not self.memory:
            raise RuntimeError("Memory system not available")
        if action.command == "store":
            return self.memory.store_memory(
                action.args.get("type"), action.args.get("content"),
                action.args.get("context"))
        elif action.command == "recall":
            return self.memory.recall_memory(action.args.get("query"))
        raise ValueError(f"Unknown memory command: {action.command}")

    def _execute_browser_action(self, action: Action) -> Any:
        if not self.browser:
            raise RuntimeError("Browser system not available")
        if action.command == "navigate":
            return self.browser.navigate(action.args.get("url"))
        elif action.command == "click":
            return self.browser.click(action.args.get("selector"))
        elif action.command == "type":
            return self.browser.type_text(
                action.args.get("selector"), action.args.get("text"))
        elif action.command == "screenshot":
            return self.browser.screenshot()
        raise ValueError(f"Unknown browser command: {action.command}")

    def _execute_file_action(self, action: Action) -> Any:
        if not self.files:
            raise RuntimeError("File system not available")
        if action.command in ["write", "create", "edit"]:
            path = action.args.get("path", "")
            if not self._check_sandbox_permission(path):
                raise PermissionError(f"No permission for path: {path}")
        if action.command == "write":
            return self.files.write_file(action.args.get("path"), action.args.get("content"))
        elif action.command == "read":
            return self.files.read_file(action.args.get("path"))
        elif action.command == "create":
            return self.files.create_directory(action.args.get("path"))
        raise ValueError(f"Unknown file command: {action.command}")

    def _check_sandbox_permission(self, path: str) -> bool:
        full_path = os.path.abspath(path)
        if full_path.startswith(os.path.abspath(self.sandbox_path)):
            return True
        for perm_path, expires in self.session_permissions.items():
            if datetime.now() < expires and full_path.startswith(os.path.abspath(perm_path)):
                return True
        return False

    def grant_session_permission(self, path: str, duration_minutes: int = 60):
        expires = datetime.now() + timedelta(minutes=duration_minutes)
        self.session_permissions[path] = expires
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO permissions_log (path, expires) VALUES (?, ?)",
                (path, expires.isoformat()))

    def _log_action(self, action: Action):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO action_journal
                (id, action_type, command, args, result, error, reverse_operation)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (action.id, action.type.value, action.command,
                 json.dumps(action.args),
                 json.dumps(action.result) if action.result else None,
                 action.error,
                 json.dumps(action.reverse_operation) if action.reverse_operation else None))

    def undo_last_action(self) -> Optional[Dict[str, Any]]:
        action = self.undo_stack.undo()
        if not action or not action.reverse_operation:
            return None
        reverse = Action(
            id=f"undo_{action.id}", type=action.type, level=action.level,
            command=action.reverse_operation.get("command"),
            args=action.reverse_operation.get("args", {}),
            timestamp=datetime.now())
        result = self._execute_action(reverse)
        return {"original_action": action.id, "undo_result": result}

    def get_status(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            journal_count = conn.execute("SELECT COUNT(*) FROM action_journal").fetchone()[0]
        return {
            "queue_active": self.action_queue.active,
            "queue_paused": self.action_queue.paused,
            "undo_depth": len(self.undo_stack.stack),
            "journal_entries": journal_count,
            "browser_available": self.browser is not None,
            "files_available": self.files is not None,
            "memory_available": self.memory is not None,
            "sandbox_path": self.sandbox_path,
        }

    def shutdown(self):
        self.action_queue.active = False
        if self.action_queue.thread:
            self.action_queue.thread.join(timeout=5)
