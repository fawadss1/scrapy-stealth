#!/usr/bin/env python3
"""Run the same checks as GitHub Actions locally.

python scripts/check.py           # all checks
python scripts/check.py mypy      # one check (ruff|format|mypy|pytest)
python scripts/check.py --fix    # auto-fix ruff lint + format
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def py(*a: str) -> list[str]:
    return [sys.executable, "-m", *a]


# Match GitHub CI: dev deps only (pytest + pytest-asyncio), not pytest-twisted
# which may be installed locally via Scrapy and masks unmarked async tests.
PYTEST_CMD = py("pytest", "-p", "no:twisted")


# key → (label, command, how_to_fix)
STEPS = {
    "ruff": (
        "Ruff — lint",
        py("ruff", "check", "."),
        "Run:  python scripts/check.py --fix",
    ),
    "format": (
        "Ruff — format",
        py("ruff", "format", "--check", "."),
        "Run:  python scripts/check.py --fix",
    ),
    "mypy": (
        "Mypy — type check",
        py("mypy", "scrapy_stealth"),
        "Open each file:line shown ABOVE, fix the type error, then:\n"
        "         python scripts/check.py mypy",
    ),
    "pytest": (
        "Pytest",
        PYTEST_CMD,
        "Read the failing test output ABOVE, fix code/tests, then:\n"
        "         python scripts/check.py pytest",
    ),
}


def run(name: str, cmd: list[str]) -> bool:
    print(f"\n{'=' * 60}\n{name}\n{'=' * 60}", flush=True)
    ok = subprocess.run(cmd, cwd=ROOT).returncode == 0
    print(f"{'OK' if ok else 'FAIL'}  {name}", flush=True)
    return ok


def main() -> int:
    p = argparse.ArgumentParser(description="Run GitHub Actions checks locally.")
    p.add_argument("check", nargs="?", choices=list(STEPS))
    p.add_argument("--fix", action="store_true", help="auto-fix ruff lint + format")
    args = p.parse_args()
    print(f"Running CI checks in {ROOT}", flush=True)

    if args.fix:
        ok = all(
            run(n, c)
            for n, c in (
                ("Ruff — lint --fix", py("ruff", "check", ".", "--fix")),
                ("Ruff — format", py("ruff", "format", ".")),
            )
        )
        if ok:
            print("\nDone. Now run:  python scripts/check.py", flush=True)
        return int(not ok)

    keys = [args.check] if args.check else list(STEPS)
    failed = [(k, n, h) for k in keys for n, c, h in [STEPS[k]] if not run(n, c)]

    print(f"\n{'=' * 60}", flush=True)
    if not failed:
        print(f"ALL CHECKS PASSED ({len(keys)}/{len(keys)})", flush=True)
        return 0

    print(f"FAILED ({len(failed)}/{len(keys)}). How to fix:\n", flush=True)
    for i, (_key, name, hint) in enumerate(failed, 1):
        print(f"  {i}. {name}\n         {hint}\n", flush=True)
    print("When fixed, run again:  python scripts/check.py", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
