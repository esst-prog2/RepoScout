import csv
import locale
from datetime import datetime, timedelta, timezone

import pytest

from reposcout.bucketing import BucketedRepo
from reposcout.github import RepoData
from reposcout.output import csv_filename, format_verdict, render_table, slugify_keyword, time_ago, write_csv

NOW = datetime(2026, 9, 24, tzinfo=timezone.utc)


def _bucketed(name: str, stars: int, days_ago: int, bucket: str, language: str = "Python") -> BucketedRepo:
    repo = RepoData(
        name=name,
        url=f"https://github.com/{name}",
        stars=stars,
        pushed_at=NOW - timedelta(days=days_ago),
        language=language,
    )
    return BucketedRepo(repo=repo, bucket=bucket)


def test_render_table_lists_repos_without_url_column():
    rows = [_bucketed("a/one", 100, 10, "active")]

    table = render_table(rows)

    assert "a/one" in table
    assert "100" in table
    assert "active" in table
    assert "github.com" not in table


def test_format_verdict_exact_count_when_total_within_fetched_limit():
    rows = [_bucketed("a/one", 100, 10, "active"), _bucketed("a/two", 50, 400, "stale")]

    verdict = format_verdict(total_count=2, bucketed=rows, now=NOW)

    assert verdict.startswith("2 repos found, 1 active in the last 3 months")
    assert "most recent entrant pushed" in verdict


def test_format_verdict_top_50_phrasing_when_total_exceeds_fetched():
    rows = [_bucketed(f"a/{i}", 100 - i, 10, "active") for i in range(50)]

    verdict = format_verdict(total_count=3241, bucketed=rows, now=NOW)

    assert verdict.startswith("Showing the 50 best-matching of 3,241 repos, 50 active among them")


@pytest.fixture
def hungarian_locale():
    """Switch the process to a Hungarian locale (thousands written "244 832"), if installed."""
    saved = locale.setlocale(locale.LC_ALL)
    for name in ("hu_HU.UTF-8", "hu_HU.utf8", "hu_HU", "Hungarian_Hungary.1250", "hu-HU"):
        try:
            locale.setlocale(locale.LC_ALL, name)
            break
        except locale.Error:
            continue
    else:
        pytest.skip("no Hungarian locale installed")
    yield
    locale.setlocale(locale.LC_ALL, saved)


def test_format_verdict_thousands_separator_ignores_locale(hungarian_locale):
    rows = [_bucketed(f"a/{i}", 100 - i, 10, "active") for i in range(50)]

    verdict = format_verdict(total_count=244832, bucketed=rows, now=NOW)

    assert verdict.startswith("Showing the 50 best-matching of 244,832 repos")


@pytest.mark.parametrize(
    "days_ago, bucket, expected",
    [(16, "active", "pushed 2 weeks ago"), (89, "active", "pushed 12 weeks ago"), (100, "slowing", "pushed 3 months ago")],
)
def test_format_verdict_rounds_time_down(days_ago, bucket, expected):
    verdict = format_verdict(total_count=1, bucketed=[_bucketed("a/one", 100, days_ago, bucket)], now=NOW)

    assert verdict.endswith(expected)


@pytest.mark.parametrize(
    "delta, expected",
    [
        (timedelta(0), "just now"),
        (timedelta(seconds=-1), "just now"),
        (timedelta(days=-1), "just now"),
        (timedelta(seconds=59), "just now"),
        (timedelta(seconds=60), "1 minute ago"),
        (timedelta(seconds=119), "1 minute ago"),
        (timedelta(seconds=120), "2 minutes ago"),
        (timedelta(minutes=59), "59 minutes ago"),
        (timedelta(hours=1), "1 hour ago"),
        (timedelta(hours=1, minutes=59), "1 hour ago"),
        (timedelta(hours=2), "2 hours ago"),
        (timedelta(hours=23, minutes=59), "23 hours ago"),
        (timedelta(days=1), "1 day ago"),
        (timedelta(days=13), "13 days ago"),
        (timedelta(days=13, hours=23), "13 days ago"),
        (timedelta(days=14), "2 weeks ago"),
        (timedelta(days=16), "2 weeks ago"),
        (timedelta(days=89), "12 weeks ago"),
        (timedelta(days=90), "3 months ago"),
        (timedelta(days=100), "3 months ago"),
        (timedelta(days=364), "12 months ago"),
        (timedelta(days=365), "1 year ago"),
        (timedelta(days=395), "1 year, 1 month ago"),
        (timedelta(days=400), "1 year, 1 month ago"),
        (timedelta(days=729), "1 year, 11 months ago"),
        (timedelta(days=730), "2 years ago"),
        (timedelta(days=2057), "5 years, 7 months ago"),
    ],
)
def test_time_ago_rounds_down_at_every_unit(delta, expected):
    assert time_ago(delta) == expected


def test_format_verdict_zero_matches():
    assert format_verdict(total_count=0, bucketed=[], now=NOW) == "0 repos found"


def test_slugify_keyword_matches_readme_demo():
    assert slugify_keyword("expense tracker") == "expense-tracker"
    assert csv_filename("expense tracker") == "expense-tracker-report.csv"


@pytest.mark.parametrize(
    "keyword, slug",
    [
        ("c++/qt", "c++-qt"),
        ("c#: tools", "c#-tools"),
        ("a / b", "a-b"),
        (".hidden", "hidden"),
        ('a\\b|c*d"e<f>g', "a-b-c-d-e-f-g"),
        ("tab\there", "tab-here"),
        ("költség követő", "költség-követő"),
    ],
)
def test_slugify_keyword_replaces_filename_unsafe_characters(keyword, slug):
    assert slugify_keyword(keyword) == slug


def test_csv_filename_falls_back_when_nothing_usable_is_left():
    assert csv_filename("???") == "search-report.csv"


def test_write_csv_populated(tmp_path):
    rows = [_bucketed("a/one", 100, 10, "active")]
    path = tmp_path / "out.csv"

    write_csv(path, rows)

    with path.open(newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    assert reader[0] == ["#", "Repository", "Stars", "Last Push", "Language", "Bucket", "URL"]
    assert reader[1][1] == "a/one"
    assert reader[1][-1] == "https://github.com/a/one"


def test_write_csv_zero_matches_is_headers_only(tmp_path):
    path = tmp_path / "out.csv"

    write_csv(path, [])

    with path.open(newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    assert len(reader) == 1
    assert reader[0][0] == "#"
