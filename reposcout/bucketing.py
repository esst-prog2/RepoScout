"""Activity bucketing and ranking for fetched repositories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from reposcout.github import RepoData

ACTIVE_THRESHOLD_DAYS = 90
STALE_THRESHOLD_DAYS = 365

ACTIVE = "active"
SLOWING = "slowing"
STALE = "stale"


@dataclass(frozen=True)
class BucketedRepo:
    repo: RepoData
    bucket: str


def classify_bucket(pushed_at: datetime, now: datetime | None = None) -> str:
    """Classify a repo's activity bucket from its last-push timestamp."""
    now = now or datetime.now(timezone.utc)
    age_days = (now - pushed_at).total_seconds() / 86400
    if age_days < ACTIVE_THRESHOLD_DAYS:
        return ACTIVE
    if age_days < STALE_THRESHOLD_DAYS:
        return SLOWING
    return STALE


def active_window_text() -> str:
    """The active window in words, for the verdict - derived from the threshold, not restated."""
    months = round(ACTIVE_THRESHOLD_DAYS / 30)
    return f"{months} months" if months * 30 == ACTIVE_THRESHOLD_DAYS else f"{ACTIVE_THRESHOLD_DAYS} days"


def bucket_repos(repos: list[RepoData]) -> list[BucketedRepo]:
    """Classify a list of repos into activity buckets."""
    return [BucketedRepo(repo=r, bucket=classify_bucket(r.pushed_at)) for r in repos]


def rank_by_stars(repos: list[RepoData]) -> list[RepoData]:
    """Sort repos by star count, descending.

    GitHub's own `sort=stars` decides *which* 50 repos are fetched; this sort
    owns the *display* order, so the ranks shown always agree with the star
    counts shown, whatever order the API (or an old cache entry) returned.
    """
    return sorted(repos, key=lambda r: r.stars, reverse=True)
