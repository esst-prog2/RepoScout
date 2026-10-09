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


def test_real_repo_compose_expense_is_slowing_not_active():
    """HW5: a real repo's real data, not a synthetic date.

    wisnukurniawan/Compose-Expense, from the HW4 spike sample
    (spike/pushed_at_drift.csv). Both dates below were fetched live from
    GitHub during the spike, not computed by this program. pushed_at - what
    RepoScout actually shows - currently buckets this repo "active", but its
    real last commit buckets it "slowing". Expected values decided by hand
    before this test was written; see AGENTS.md's 2026-10-09 HW5 entry.
    """
    fetched_at = datetime.fromisoformat("2026-10-03T10:42:05.733837+00:00")
    pushed_at = datetime.fromisoformat("2026-09-23T23:48:39+00:00")
    real_last_commit = datetime.fromisoformat("2026-05-05T04:09:48+00:00")

    assert classify_bucket(pushed_at, now=fetched_at) == ACTIVE  # what RepoScout currently shows
    assert classify_bucket(real_last_commit, now=fetched_at) == SLOWING  # what is actually true


def _repo(name: str, stars: int) -> RepoData:
    return RepoData(name=name, url=f"https://github.com/{name}", stars=stars, pushed_at=NOW, language="Python")


def test_rank_by_stars_sorts_descending():
    repos = [_repo("low", 5), _repo("high", 500), _repo("mid", 50)]

    ranked = rank_by_stars(repos)

    assert [r.name for r in ranked] == ["high", "mid", "low"]
