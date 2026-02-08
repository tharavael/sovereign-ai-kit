#!/usr/bin/env python3
"""
Sandbox-enforced file operations for AI body system.
Restricts write access to a configurable sandbox directory.
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional


class BodyFiles:
    """File operations with sandbox enforcement."""

    def __init__(self, sandbox_path: str):
        self.sandbox_path = os.path.abspath(os.path.expanduser(sandbox_path))
        self.session_permissions: Dict[str, datetime] = {}
        os.makedirs(self.sandbox_path, exist_ok=True)

    def _is_within_sandbox(self, path: str) -> bool:
        full_path = os.path.abspath(os.path.expanduser(path))
        if full_path.startswith(self.sandbox_path):
            return True
        for perm_path, expires in self.session_permissions.items():
            if datetime.now() < expires and full_path.startswith(os.path.abspath(perm_path)):
                return True
        return False

    def _enforce_sandbox(self, path: str, operation: str = "access"):
        if not self._is_within_sandbox(path):
            raise PermissionError(
                f"Cannot {operation} outside sandbox: {path}\n"
                f"Sandbox: {self.sandbox_path}")

    def grant_permission(self, path: str, duration_minutes: int = 60):
        """Grant temporary write access to a path outside sandbox."""
        self.session_permissions[path] = datetime.now() + timedelta(minutes=duration_minutes)

    def read_file(self, path: str) -> str:
        """Read file (allowed anywhere)."""
        with open(os.path.expanduser(path), 'r') as f:
            return f.read()

    def write_file(self, path: str, content: str) -> Dict:
        """Write file (sandbox enforced)."""
        self._enforce_sandbox(path, "write")
        full_path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        existed = os.path.exists(full_path)
        backup = None
        if existed:
            backup = full_path + ".bak"
            shutil.copy2(full_path, backup)

        with open(full_path, 'w') as f:
            f.write(content)

        return {
            "path": full_path,
            "created": not existed,
            "bytes": len(content),
            "backup": backup,
        }

    def create_directory(self, path: str) -> Dict:
        """Create directory (sandbox enforced)."""
        self._enforce_sandbox(path, "create directory")
        full_path = os.path.expanduser(path)
        os.makedirs(full_path, exist_ok=True)
        return {"path": full_path, "created": True}

    def list_directory(self, path: str) -> list:
        """List directory contents (allowed anywhere)."""
        return os.listdir(os.path.expanduser(path))

    def file_exists(self, path: str) -> bool:
        return os.path.exists(os.path.expanduser(path))
