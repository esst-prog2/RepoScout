"""Terminal table, one-line verdict, and CSV export."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import humanize
from tabulate import tabulate

from reposcout.bucketing import ACTIVE, BucketedRepo, active_window_text
from reposcout.cache import normalize_query

TABLE_HEADERS = ["#", "Repository", "Stars", "Last Push", "Language", "Bucket"]
CSV_HEADERS = TABLE_HEADERS + ["URL"]


def slugify_keyword(keyword: str) -> str:
    """The normalized query with spaces turned into hyphens (matches the README demo)."""
    return normalize_query(keyword).replace(" ", "-")


def csv_filename(keyword: str) -> str:
    return f"{slugify_keyword(keyword)}-report.csv"


def _row(rank: int, b: BucketedRepo, missing_language: str) -> list:
    """One table/CSV row, in TABLE_HEADERS order."""
    return [
        rank,
        b.repo.name,
        b.repo.stars,
        b.repo.pushed_at.date().isoformat(),
        b.repo.language or missing_language,
        b.bucket,
    ]


def render_table(bucketed: list[BucketedRepo]) -> str:
    """Render the terminal table (no URL column), ranked as given (assumed pre-sorted)."""
    rows = [_row(i, b, missing_language="-") for i, b in enumerate(bucketed, start=1)]
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
            f"{total_count} repos found, {active_count} active in the last {active_window_text()} "
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
            writer.writerow(_row(i, b, missing_language="") + [b.repo.url])
