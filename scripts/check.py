#!/usr/bin/env python3
"""Run the same checks as GitHub Actions (Lint + CI) on your machine.

Usage (from repo root):
    python scripts/check.py

Requires dev dependencies:
    pip install -e ".[dev]"
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def _py(*args: str) -> list[str]:
    """Run a tool via ``python -m`` (reliable on Windows with app-control policies)."""
    return [PYTHON, "-m", *args]


STEPS: list[tuple[str, list[str]]] = [
    ("Ruff — lint", _py("ruff", "check", ".")),
    ("Ruff — format check", _py("ruff", "format", "--check", ".")),
    ("Mypy — type check", _py("mypy", "scrapy_stealth")),
    ("Pytest", _py("pytest")),
]


def _run_step(name: str, command: list[str]) -> bool:
    bar = "=" * 60
    print(f"\n{bar}\n{name}\n{bar}", flush=True)
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode == 0:
        print(f"OK  {name}", flush=True)
        return True
    print(f"FAIL  {name}  (exit code {result.returncode})", flush=True)
    return False


def main() -> int:
    print(f"Running CI checks in {ROOT}", flush=True)
    failed = [name for name, cmd in STEPS if not _run_step(name, cmd)]

    print(f"\n{'=' * 60}", flush=True)
    if failed:
        print(f"FAILED ({len(failed)}/{len(STEPS)}):", flush=True)
        for name in failed:
            print(f"  - {name}", flush=True)
        print("\nFix the errors above before pushing to GitHub.", flush=True)
        return 1

    print(f"ALL CHECKS PASSED ({len(STEPS)}/{len(STEPS)})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
