# Contributing

Thank you for contributing to scrapy-stealth.

## Local setup

```bash
git clone https://github.com/fawadss1/scrapy-stealth.git
cd scrapy-stealth
pip install -e ".[dev]"
```

## Run checks

```bash
python scripts/check.py
```

Individual steps:

```bash
python scripts/check.py ruff
python scripts/check.py format
python scripts/check.py mypy
python scripts/check.py pytest
```

See [CHECK.md](https://github.com/fawadss1/scrapy-stealth/blob/master/CHECK.md) in the repository.

## Documentation

Build docs locally:

```bash
pip install -e ".[docs]"
mkdocs serve
```

Submit doc changes under `docs/` with the same PR as code changes when behavior changes.

### Read the Docs setup (maintainers)

1. Sign in at [readthedocs.org](https://readthedocs.org/)
2. Import the GitHub repo `fawadss1/scrapy-stealth`
3. RTD reads `.readthedocs.yaml` and builds with MkDocs automatically
4. Set **default branch** and enable **PDF/epub** if desired
5. Update PyPI `Documentation` URL to `https://scrapy-stealth.readthedocs.io/`

## Conventions

- Per-request options: `request.meta["stealth"]`
- Global defaults: Scrapy settings or `scrapy_stealth.config.config`
- Tests use `example.com` / `*.example.com` — avoid real third-party URLs in tests
- Run `python scripts/check.py` before opening a PR

## Links

- [CONTRIBUTING.md](https://github.com/fawadss1/scrapy-stealth/blob/master/CONTRIBUTING.md)
- [AGENTS.md](https://github.com/fawadss1/scrapy-stealth/blob/master/AGENTS.md) — agent guide
- [CHANGELOG](https://github.com/fawadss1/scrapy-stealth/releases)
