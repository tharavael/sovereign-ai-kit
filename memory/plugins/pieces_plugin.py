#!/usr/bin/env python3
"""
Pieces LTM plugin — integrates Pieces for Developers as a semantic search backend.
Requires Pieces OS running locally and the Pieces SQLite database accessible.
"""

import os
import subprocess
import json
from typing import Dict, List, Optional, Any
from base_plugin import LTMPlugin


class PiecesPlugin(LTMPlugin):
    """LTM integration via Pieces for Developers."""

    def __init__(self, query_script: Optional[str] = None):
        self.query_script = query_script or os.environ.get("SAK_LTM_SCRIPT", "")

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.query_script or not os.path.isfile(self.query_script):
            return []

        try:
            result = subprocess.run(
                ["python3", self.query_script, "search", query,
                 "--limit", str(limit)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            pass

        return []

    def store(self, content: str, metadata: Optional[Dict] = None) -> bool:
        # Pieces storage is managed by the Pieces application itself.
        # This plugin is read-only — it queries existing Pieces data.
        return False

    def health_check(self) -> Dict[str, Any]:
        if not self.query_script:
            return {"healthy": False, "message": "No LTM script configured (SAK_LTM_SCRIPT)"}

        if not os.path.isfile(self.query_script):
            return {"healthy": False, "message": f"Script not found: {self.query_script}"}

        try:
            result = subprocess.run(
                ["python3", self.query_script, "search", "health check", "--limit", "1"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return {"healthy": True, "message": "Pieces LTM accessible"}
        except subprocess.TimeoutExpired:
            return {"healthy": False, "message": "Query timed out"}

        return {"healthy": False, "message": f"Query failed: {result.stderr[:200]}"}
