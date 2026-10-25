"""Terminal table, one-line verdict, and CSV export."""

from __future__ import annotations

import csv
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tabulate import tabulate

from reposcout.bucketing import ACTIVE, BucketedRepo, active_window_text
from reposcout.cache import normalize_query

TABLE_HEADERS = ["#", "Repository", "Stars", "Last Push", "Language", "Bucket"]
CSV_HEADERS = TABLE_HEADERS + ["URL"]


# Characters invalid in filenames on Windows (only "/" on macOS/Linux), control
# characters, and whitespace: each run becomes a single hyphen.
_UNSAFE_FILENAME_RUN = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f\s]+')
FALLBACK_SLUG = "search"


def slugify_keyword(keyword: str) -> str:
    """The normalized query as a safe filename stem ("expense tracker" -> "expense-tracker")."""
    slug = _UNSAFE_FILENAME_RUN.sub("-", normalize_query(keyword))
    slug = re.sub(r"-{2,}", "-", slug).strip("-.")
    return slug or FALLBACK_SLUG


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
    pushed_ago = time_ago(now - most_recent.pushed_at)

    if total_count <= len(bucketed):
        return (
            f"{total_count} repos found, {active_count} active in the last {active_window_text()} "
            f"— most recent entrant pushed {pushed_ago}"
        )
    return (
        f"Showing the {len(bucketed)} best-matching of {total_count} repos, "
        f"{active_count} active among them — most recent entrant pushed {pushed_ago}"
    )


def _count(n: int, unit: str) -> str:
    return f"{n} {unit}" if n == 1 else f"{n} {unit}s"


def time_ago(delta: timedelta) -> str:
    """Relative time, always rounded down so it is never later than the truth.

    Weeks run up to 90 days, so a repo inside the active window never reads "3 months".
    Months are 30 days and years 365, as in the bucket thresholds.
    """
    seconds = max(int(delta.total_seconds()), 0)  # a push slightly in the future (clock skew) is "just now"
    days = seconds // 86400
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{_count(seconds // 60, 'minute')} ago"
    if days < 1:
        return f"{_count(seconds // 3600, 'hour')} ago"
    if days < 14:
        return f"{_count(days, 'day')} ago"
    if days < 90:
        return f"{_count(days // 7, 'week')} ago"
    if days < 365:
        return f"{_count(days // 30, 'month')} ago"
    years, months = days // 365, min((days % 365) // 30, 11)
    if months == 0:
        return f"{_count(years, 'year')} ago"
    return f"{_count(years, 'year')}, {_count(months, 'month')} ago"


def write_csv(path: Path, bucketed: list[BucketedRepo]) -> None:
    """Write the full ranked, bucketed result set (plus URL) to a CSV file."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        for i, b in enumerate(bucketed, start=1):
            writer.writerow(_row(i, b, missing_language="") + [b.repo.url])
