from __future__ import annotations

import re
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, metadata

_PACKAGE_NAME = "scrapy-stealth"


def _parse_author(raw: str) -> tuple[str, str]:
    """Return (name, email) from 'Name <email>' notation or plain name."""
    raw = (raw or "").strip()
    match = re.compile(r"^(.*?)\s*<([^>]+)>\s*$").match(raw)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return raw, ""


def _first_url(meta: object, *keys: str) -> str:
    """Return the first non-empty value found among the given metadata keys."""
    for key in keys:
        val = meta.get(key)  # type: ignore[union-attr]
        if val:
            return val.strip()
    return ""


@dataclass(frozen=True)
class PackageMetadata:
    """Immutable snapshot of a package's distribution metadata."""

    name: str
    version: str
    author: str
    email: str
    license: str

    @classmethod
    def load(cls, package: str = _PACKAGE_NAME) -> PackageMetadata:
        """Load metadata from the installed distribution."""
        try:
            meta = metadata(package)
        except PackageNotFoundError:
            meta = {}

        raw_author = meta.get("Author-email") or meta.get("Author") or ""
        author, email = _parse_author(raw_author)

        return cls(
            name=meta.get("Name") or package,
            version=meta.get("Version", ""),
            author=author,
            email=email,
            license=meta.get("License", ""),
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
