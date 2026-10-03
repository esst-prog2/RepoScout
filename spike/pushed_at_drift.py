"""HW4 spike: how often does pushed_at disagree with the real last commit,
and how many repos change activity bucket because of it?

Usage:
    python spike/pushed_at_drift.py --fetch   # hits the live GitHub API once,
                                               # writes spike/pushed_at_drift.csv
    python spike/pushed_at_drift.py           # analyzes the committed CSV and
                                               # prints the answer (no network)

The committed CSV is the evidence; re-running without --fetch reproduces the
answer from that data alone, which is what the grader re-runs.
"""

from __future__ import annotations

import csv
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reposcout.auth import resolve_token
from reposcout.bucketing import classify_bucket
from reposcout.github import search_repositories

DATA_PATH = Path(__file__).parent / "pushed_at_drift.csv"
KEYWORD = "expense tracker"
COMMITS_URL = "https://api.github.com/repos/{full_name}/commits"


def _fetch_real_last_commit(full_name: str, token: str | None) -> datetime:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(
        COMMITS_URL.format(full_name=full_name),
        headers=headers,
        params={"per_page": 1},
        timeout=30,
    )
    response.raise_for_status()
    commit = response.json()[0]
    date_str = commit["commit"]["committer"]["date"]
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def fetch() -> None:
    token = resolve_token()
    result = search_repositories(KEYWORD, token)
    repos = result.repos[:50]
    now = datetime.now(timezone.utc)
    print(f"Fetched {len(repos)} repos from search {KEYWORD!r} (total_count={result.total_count})")

    rows = []
    for i, repo in enumerate(repos, 1):
        real_last_commit = _fetch_real_last_commit(repo.name, token)
        rows.append(
            {
                "repo": repo.name,
                "pushed_at": repo.pushed_at.isoformat(),
                "real_last_commit": real_last_commit.isoformat(),
                "fetched_at": now.isoformat(),
            }
        )
        print(f"  {i}/{len(repos)}: {repo.name}")

    with DATA_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["repo", "pushed_at", "real_last_commit", "fetched_at"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {DATA_PATH}")


def analyze() -> None:
    with DATA_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    drifts = []
    flips = 0
    for row in rows:
        pushed_at = datetime.fromisoformat(row["pushed_at"])
        real = datetime.fromisoformat(row["real_last_commit"])
        # bucket classification uses the time the data was fetched, not "now",
        # so the flip count stays reproducible no matter when this is re-run
        fetched_at = datetime.fromisoformat(row["fetched_at"])

        drift_days = abs((pushed_at - real).total_seconds()) / 86400
        drifts.append(drift_days)

        bucket_pushed = classify_bucket(pushed_at, now=fetched_at)
        bucket_real = classify_bucket(real, now=fetched_at)
        if bucket_pushed != bucket_real:
            flips += 1

    median_drift = statistics.median(drifts)
    print(f"Repos analyzed: {len(rows)}")
    print(f"Median drift (days): {median_drift:.2f}")
    print(f"Bucket flips: {flips}/{len(rows)}")


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch()
    else:
        analyze()
