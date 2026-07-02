# Contributing to scrapy-stealth

Contributions are welcome! This is an open source project and all help is appreciated.

## Getting Started

1. Fork the repository on [GitHub](https://github.com/fawadss1/scrapy-stealth)
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests if applicable
4. Run linting and tests locally before opening a pull request (see below)
5. Open a pull request describing what you changed and why

## Code Style & Linting

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting, and [mypy](https://mypy-lang.org/) for type checking. GitHub Actions will fail if any of these checks do not pass:

```bash
pip install -e ".[dev]"

ruff check .
ruff format --check .
mypy scrapy_stealth
```

All three must pass before your pull request can be merged.

## Running Tests

```bash
pytest
```

## CI on GitHub

Two workflows run on every push and pull request to `master`:

| Workflow | Checks |
|----------|--------|
| **Lint** | `ruff check`, `ruff format --check`, `mypy` |
| **CI** | `pytest` on Python 3.11–3.14 (Ubuntu, Windows, macOS) |

## Ways to Contribute

- Report bugs via [GitHub Issues](https://github.com/fawadss1/scrapy-stealth/issues)
- Suggest new engines, strategies, or detectors
- Improve documentation or examples
- Add support for new browser fingerprints
