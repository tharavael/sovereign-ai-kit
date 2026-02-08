#!/usr/bin/env python3
"""
Verify Sovereign AI Kit installation.
Checks that all components are properly installed and functional.
"""

import os
import sys
import json
import subprocess
import sqlite3


def get_sak_home():
    return os.environ.get("SAK_HOME", os.path.expanduser("~/.sovereign-ai"))


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    marker = "+" if condition else "x"
    msg = f"  [{marker}] {name}"
    if detail and not condition:
        msg += f" — {detail}"
    print(msg)
    return condition


def main():
    sak_home = get_sak_home()
    print(f"Verifying Sovereign AI Kit at: {sak_home}")
    print()

    passed = 0
    failed = 0

    # ── Directory Structure ──────────────────────────────
    print("Directory Structure:")
    dirs = [
        "memory", "browser/daemon", "browser/extension",
        "browser/scripts", "body", "identity",
        "history/learnings", "history/sessions"
    ]
    for d in dirs:
        path = os.path.join(sak_home, d)
        result = check(d, os.path.isdir(path), f"Missing: {path}")
        passed += result
        failed += not result

    # ── Core Files ───────────────────────────────────────
    print("\nCore Files:")
    files = [
        ("config.env", "config.env"),
        ("sovereign_memory.py", "memory/sovereign_memory.py"),
        ("browser-daemon.js", "browser/daemon/browser-daemon.js"),
        ("browser.js", "browser/scripts/browser.js"),
        ("manifest.json", "browser/extension/manifest.json"),
        ("background.js", "browser/extension/background.js"),
        ("start-daemon.sh", "browser/start-daemon.sh"),
        ("body_coordinator.py", "body/body_coordinator.py"),
        ("body_cli.py", "body/body_cli.py"),
    ]
    for name, rel_path in files:
        path = os.path.join(sak_home, rel_path)
        result = check(name, os.path.isfile(path), f"Missing: {path}")
        passed += result
        failed += not result

    # ── Memory System ────────────────────────────────────
    print("\nMemory System:")
    memory_script = os.path.join(sak_home, "memory/sovereign_memory.py")
    if os.path.isfile(memory_script):
        try:
            result_text = subprocess.check_output(
                ["python3", memory_script, "recall", "test"],
                env={**os.environ, "SAK_HOME": sak_home},
                stderr=subprocess.STDOUT, timeout=10
            ).decode()
            result = check("Memory recall", True)
            passed += 1
        except Exception as e:
            result = check("Memory recall", False, str(e))
            failed += 1

        # Check database exists
        db_path = os.path.join(sak_home, "memory/cache.db")
        result = check("Memory database", os.path.isfile(db_path),
                        f"Expected: {db_path}")
        passed += result
        failed += not result
    else:
        check("Memory system", False, "sovereign_memory.py not found")
        failed += 1

    # ── Browser Daemon ───────────────────────────────────
    print("\nBrowser Automation:")
    port = os.environ.get("SAK_BROWSER_PORT", "19222")
    try:
        import urllib.request
        req = urllib.request.urlopen(f"http://localhost:{port}/health",
                                     timeout=3)
        result = check("Browser daemon", req.status == 200)
        passed += 1
    except Exception:
        check("Browser daemon", False,
              f"Not running on port {port}. Start with: {sak_home}/browser/start-daemon.sh")
        failed += 1

    # Check Node.js
    try:
        subprocess.check_output(["node", "--version"],
                                stderr=subprocess.STDOUT, timeout=5)
        result = check("Node.js", True)
        passed += 1
    except Exception:
        check("Node.js", False, "Required for browser automation")
        failed += 1

    # ── Summary ──────────────────────────────────────────
    total = passed + failed
    print(f"\nResults: {passed}/{total} checks passed")

    if failed == 0:
        print("\nAll checks passed. Your sovereignty stack is ready.")
    else:
        print(f"\n{failed} check(s) failed. Review the output above.")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
