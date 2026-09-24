"""Per-query result caching: key normalization, 24h expiry, self-healing on corruption."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import platformdirs

from reposcout.github import RepoData

APP_NAME = "reposcout"
TTL = timedelta(hours=24)

_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class CacheEntry:
    total_count: int
    repos: list[RepoData]
    fetched_at: datetime


def normalize_query(keyword: str) -> str:
    """Casefold, trim, and collapse internal whitespace. Hyphens are left as-is."""
    collapsed = _WHITESPACE_RE.sub(" ", keyword.strip())
    return collapsed.casefold()


def _cache_dir() -> Path:
    return Path(platformdirs.user_cache_dir(APP_NAME))


def cache_path(keyword: str) -> Path:
    key = normalize_query(keyword)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return _cache_dir() / f"{digest}.json"


def read_cache(keyword: str, now: datetime | None = None) -> CacheEntry | None:
    """Return a valid, unexpired cache entry, or None on miss/expiry/corruption."""
    now = now or datetime.now(timezone.utc)
    path = cache_path(keyword)
    if not path.exists():
        return None

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        fetched_at = datetime.fromisoformat(raw["fetched_at"])
        repos = [
            RepoData(
                name=r["name"],
                url=r["url"],
                stars=r["stars"],
                pushed_at=datetime.fromisoformat(r["pushed_at"]),
                language=r["language"],
            )
            for r in raw["repos"]
        ]
        total_count = raw["total_count"]
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None

    if now - fetched_at > TTL:
        return None

    return CacheEntry(total_count=total_count, repos=repos, fetched_at=fetched_at)


def write_cache(keyword: str, total_count: int, repos: list[RepoData], now: datetime | None = None) -> None:
    """Write raw fetched fields + fetched_at timestamp for the normalized keyword."""
    now = now or datetime.now(timezone.utc)
    path = cache_path(keyword)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "fetched_at": now.isoformat(),
        "total_count": total_count,
        "repos": [
            {
                "name": r.name,
                "url": r.url,
                "stars": r.stars,
                "pushed_at": r.pushed_at.isoformat(),
                "language": r.language,
            }
            for r in repos
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
