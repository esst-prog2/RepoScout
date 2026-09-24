from datetime import datetime, timedelta, timezone

import pytest

from reposcout.bucketing import ACTIVE, SLOWING, STALE, classify_bucket, rank_by_stars
from reposcout.github import RepoData

NOW = datetime(2026, 9, 24, tzinfo=timezone.utc)


def _pushed(days_ago: int) -> datetime:
    return NOW - timedelta(days=days_ago)


@pytest.mark.parametrize(
    "days_ago, expected",
    [
        (0, ACTIVE),
        (89, ACTIVE),
        (90, SLOWING),  # just inside the active/slowing boundary
        (364, SLOWING),
        (365, STALE),  # just inside the slowing/stale boundary
        (1000, STALE),
    ],
)
def test_classify_bucket_boundaries(days_ago, expected):
    assert classify_bucket(_pushed(days_ago), now=NOW) == expected


def _repo(name: str, stars: int) -> RepoData:
    return RepoData(name=name, url=f"https://github.com/{name}", stars=stars, pushed_at=NOW, language="Python")


def test_rank_by_stars_sorts_descending():
    repos = [_repo("low", 5), _repo("high", 500), _repo("mid", 50)]

    ranked = rank_by_stars(repos)

    assert [r.name for r in ranked] == ["high", "mid", "low"]
