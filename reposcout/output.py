"""Terminal table, one-line verdict, and CSV export."""

from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from pathlib import Path

import humanize
from tabulate import tabulate

from reposcout.bucketing import ACTIVE, BucketedRepo

TABLE_HEADERS = ["#", "Repository", "Stars", "Last Push", "Language", "Bucket"]
CSV_HEADERS = TABLE_HEADERS + ["URL"]

_SLUG_WHITESPACE_RE = re.compile(r"\s+")


def slugify_keyword(keyword: str) -> str:
    """Lowercase, whitespace collapsed to single hyphens (matches the README demo)."""
    return _SLUG_WHITESPACE_RE.sub("-", keyword.strip().lower())


def csv_filename(keyword: str) -> str:
    return f"{slugify_keyword(keyword)}-report.csv"


def render_table(bucketed: list[BucketedRepo]) -> str:
    """Render the terminal table (no URL column), ranked as given (assumed pre-sorted)."""
    rows = [
        [
            i,
            b.repo.name,
            b.repo.stars,
            b.repo.pushed_at.date().isoformat(),
            b.repo.language or "-",
            b.bucket,
        ]
        for i, b in enumerate(bucketed, start=1)
    ]
    return tabulate(rows, headers=TABLE_HEADERS)


def format_verdict(total_count: int, bucketed: list[BucketedRepo], now: datetime | None = None) -> str:
    """One-line verdict. Bucket counts always scope to the fetched repos only."""
    if not bucketed:
        return "0 repos found"

    now = now or datetime.now(timezone.utc)
    active_count = sum(1 for b in bucketed if b.bucket == ACTIVE)
    most_recent = max(bucketed, key=lambda b: b.repo.pushed_at).repo
    time_ago = humanize.naturaltime(now - most_recent.pushed_at)

    if total_count <= len(bucketed):
        return (
            f"{total_count} repos found, {active_count} active in the last 3 months "
            f"— most recent entrant pushed {time_ago}"
        )
    return (
        f"Showing top {len(bucketed)} of {total_count} matching repos, "
        f"{active_count} active among them — most recent entrant pushed {time_ago}"
    )


def write_csv(path: Path, bucketed: list[BucketedRepo]) -> None:
    """Write the full ranked, bucketed result set (plus URL) to a CSV file."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        for i, b in enumerate(bucketed, start=1):
            writer.writerow(
                [
                    i,
                    b.repo.name,
                    b.repo.stars,
                    b.repo.pushed_at.date().isoformat(),
                    b.repo.language or "",
                    b.bucket,
                    b.repo.url,
                ]
            )
