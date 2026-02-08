#!/usr/bin/env python3
"""
Browser subprocess wrapper for the body system.
Calls the browser.js CLI with retry logic.
"""

import subprocess
import json
import os
import time
from typing import Optional, Any


class BodyBrowser:
    """Browser automation via the daemon CLI wrapper."""

    def __init__(self):
        sak_home = os.environ.get("SAK_HOME", os.path.expanduser("~/.sovereign-ai"))
        skill_dir = os.environ.get("SAK_BROWSER_SKILL_DIR", os.path.join(sak_home, "browser"))
        self.browser_script = os.path.join(skill_dir, "scripts", "browser.js")
        self.max_retries = 3
        self.retry_delay = 1.0

    def _run(self, command: str, *args, timeout: int = 30) -> Any:
        """Run a browser command with retry logic."""
        cmd = ["node", self.browser_script, command] + [str(a) for a in args]

        for attempt in range(self.max_retries):
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=timeout)
                if result.returncode == 0:
                    return json.loads(result.stdout)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            except subprocess.TimeoutExpired:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            except json.JSONDecodeError:
                return result.stdout

        raise RuntimeError(f"Browser command failed after {self.max_retries} attempts: {command}")

    def navigate(self, url: str) -> Any:
        return self._run("navigate", url)

    def query(self, selector: str, mode: str = "list") -> Any:
        return self._run("query", selector, mode)

    def click(self, selector: str, index: int = 0) -> Any:
        return self._run("click", selector, str(index))

    def type_text(self, selector: str, text: str) -> Any:
        return self._run("type", selector, text)

    def screenshot(self) -> Any:
        return self._run("screenshot")

    def get_tabs(self) -> Any:
        return self._run("get_tabs")
