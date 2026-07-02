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

## What it runs

Same as the **Lint** and **CI** workflows on GitHub:

| Step        | Command                 |
|-------------|-------------------------|
| Ruff lint   | `ruff check .`          |
| Ruff format | `ruff format --check .` |
| Mypy        | `mypy scrapy_stealth`   |
| Tests       | `pytest`                |

If any step fails, the script prints which ones failed and exits with code `1`.

## Run steps individually

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy scrapy_stealth
python -m pytest
```

Auto-fix formatting:

```bash
python -m ruff format .
```
