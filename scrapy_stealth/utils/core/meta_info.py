from __future__ import annotations

import re
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, metadata
from typing import Any

_PACKAGE_NAME = "scrapy-stealth"


def _project_url(meta: Any, label: str, default: str = "") -> str:
    """Return a PEP 621 Project-URL value by label (e.g. Documentation)."""
    for entry in meta.get_all("Project-URL") or []:
        name, sep, url = entry.partition(", ")
        if sep and name.strip() == label:
            return url.strip()
    return default


def _parse_author(raw: str) -> tuple[str, str]:
    """Return (name, email) from 'Name <email>' notation or plain name."""
    raw = (raw or "").strip()
    match = re.compile(r"^(.*?)\s*<([^>]+)>\s*$").match(raw)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return raw, ""


@dataclass(frozen=True)
class PackageMetadata:
    """Immutable snapshot of a package's distribution metadata."""

    name: str
    version: str
    author: str
    email: str
    license: str
    docs_url: str
    changelog_url: str

    @classmethod
    def load(cls, package: str = _PACKAGE_NAME) -> PackageMetadata:
        """Load metadata from the installed distribution."""
        try:
            meta = metadata(package)
        except PackageNotFoundError:
            return cls(
                name=package,
                version="",
                author="",
                email="",
                license="",
                docs_url="",
                changelog_url="",
            )

        raw_author = meta.get("Author-email") or meta.get("Author") or ""
        author, email = _parse_author(raw_author)

        return cls(
            name=meta.get("Name") or package,
            version=meta.get("Version", ""),
            author=author,
            email=email,
            license=meta.get("License", ""),
            docs_url=_project_url(
                meta,
                "Documentation",
                "https://scrapy-stealth.readthedocs.io/en/latest/",
            ),
            changelog_url=_project_url(
                meta,
                "Changelog",
                "https://scrapy-stealth.readthedocs.io/en/latest/reference/changelog/",
            ),
        )

    def __str__(self) -> str:
        return f"{self.name} v{self.version} by {self.author} <{self.email}>"

    def __repr__(self) -> str:
        return (
            f"PackageMetadata(name={self.name!r}, version={self.version!r}, "
            f"author={self.author!r}, license={self.license!r})"
        )


# Module-level singleton — resolved once at import time.
_pkg_meta: PackageMetadata = PackageMetadata.load()
