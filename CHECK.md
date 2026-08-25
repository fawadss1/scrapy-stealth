# Local CI checks

Run the same checks as GitHub Actions **before you push**, so errors show up on your PC instead of in the Actions tab.

## One-time setup

```bash
pip install -e ".[dev]"
```

## Run all checks

From the repo root:

```bash
python scripts/check.py
```

If a step fails, the script prints a **re-run / fix command** for that step.

## What it runs

Same as the **Lint** and **CI** workflows on GitHub:

| Step        | Command                 | Auto-fix?                         |
|-------------|-------------------------|-----------------------------------|
| Ruff lint   | `ruff check .`          | Yes: `ruff check . --fix`         |
| Ruff format | `ruff format --check .` | Yes: `ruff format .`              |
| Mypy        | `mypy scrapy_stealth`   | No — fix the reported type errors |
| Tests       | `pytest -p no:twisted`  | No — fix failing tests            |

## Run one check

```bash
python scripts/check.py ruff
python scripts/check.py format
python scripts/check.py mypy
python scripts/check.py pytest
```

## Auto-fix (ruff only)

```bash
python scripts/check.py --fix
```

Then re-run `python scripts/check.py`. Mypy and pytest still need manual fixes.

Pytest runs with `-p no:twisted` so local runs match GitHub CI (`pip install -e ".[dev]"` only).
If you have `pytest-twisted` installed from Scrapy, plain `pytest` can pass async tests that CI rejects.

## Run steps individually

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy scrapy_stealth
python -m pytest -p no:twisted
```
