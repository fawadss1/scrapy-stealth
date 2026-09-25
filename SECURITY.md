# Security Policy

## Supported Versions

Security fixes are published only for the **current latest release** on [PyPI](https://pypi.org/project/scrapy-stealth/). Upgrade to
the newest version before reporting issues that may already be fixed.

| Version         | Supported |
|-----------------|-----------|
| **1.0.x**       | ✅        |
| 0.9.x and older | ❌        |

Latest stable: **1.0.1** — install with `pip install -U scrapy-stealth`.

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public GitHub issue.

Report it privately via [GitHub Security Advisories](https://github.com/fawadss1/scrapy-stealth/security/advisories/new) (preferred) or
email **fawadstar6@gmail.com** with:

- A description of the issue and impact
- Steps to reproduce (minimal PoC if possible)
- Affected version(s) and suggested fix (optional)

We aim to acknowledge reports within a few business days. Once confirmed and fixed, a patched release will be published on PyPI and
noted in the [changelog](https://scrapy-stealth.readthedocs.io/en/latest/reference/changelog/).

## Scope

This policy covers the **scrapy-stealth** Python package and its documented public API (middleware, engines, settings, and
`request.meta["stealth"]`).

**In scope for hardening discussions**

- The local **CONNECT relay** used with the browser driver (proxy auth, DNS pin), including bind/advertise behavior with external CDP
- **External CDP** configuration (`STEALTH_CDP_URL`, `STEALTH_CDP_CONNECT_KWARGS`, per-request `cdp_url` / `cdp_connect_kwargs`),
  including `http`/`https` discovery and `ws`/`wss` endpoints
- Handling of proxy URLs, cookies, and request data passed through stealth engines
- Full-page **snapshots** (`snapshot=True`) stored in `response.meta["snapshot_content"]`

**Out of scope**

- Third-party runtimes and services: Chrome/Chromium, nodriver, curl_cffi, wreq, proxy providers, and target websites
- Misconfiguration (e.g. exposing CDP `:9222` or the relay port to the public internet without authentication or firewall rules)
- Storing proxy passwords or API keys in source control — use environment variables or secret stores, not committed settings

## Operational notes

- Treat **CDP endpoints** like admin interfaces: bind to trusted networks, use auth headers where supported, and restrict firewall access.
- Prefer **`http://host:9222`** or **`ws://host:9222/`** for `STEALTH_CDP_URL`, not copied `ws://…/devtools/browser/…` session URLs
  (they expire and are not a stable security boundary).
- When Scrapy runs on one host and the browser on another, the relay is reachable at your LAN IP; allow only the CDP host to connect.
- Snapshot PNGs may contain sensitive page content; restrict file permissions and sharing when using the `@snapshot` decorator or
  `snapshot_content` in pipelines.
