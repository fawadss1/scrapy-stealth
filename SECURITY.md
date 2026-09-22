# Security Policy

## Supported Versions

Security fixes are published only for the **current latest release** on [PyPI](https://pypi.org/project/scrapy-stealth/). Upgrade to
the newest version before reporting issues that may already be fixed.

| Version         | Supported |
|-----------------|-----------|
| **0.9.x**       | ✅        |
| 0.8.x and older | ❌        |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public GitHub issue.

Report it privately via [GitHub Security Advisories](https://github.com/fawadss1/scrapy-stealth/security/advisories/new) (preferred) or
email **fawadstar6@gmail.com** with:

- A description of the issue and impact
- Steps to reproduce (minimal PoC if possible)
- Affected version (s) and suggested fix (optional)

We aim to acknowledge reports within a few business days. Once confirmed and fixed, a patched release will be published on PyPI and
noted in the [changelog](https://scrapy-stealth.readthedocs.io/en/latest/reference/changelog/).

## Scope

This policy covers the **scrapy-stealth** Python package and its documented public API (middleware, engines, settings, and
`request.meta["stealth"]`). Third-party services (proxies, target sites, Chrome/nodriver, curl_cffi) are outside this project’s
control.
