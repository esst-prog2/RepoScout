import csv
from datetime import datetime, timedelta, timezone

from reposcout.bucketing import BucketedRepo
from reposcout.github import RepoData
from reposcout.output import csv_filename, format_verdict, render_table, slugify_keyword, write_csv

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

    assert "top 50 of 3241" in verdict.replace(",", "")


def test_format_verdict_zero_matches():
    assert format_verdict(total_count=0, bucketed=[], now=NOW) == "0 repos found"


def test_slugify_keyword_matches_readme_demo():
    assert slugify_keyword("expense tracker") == "expense-tracker"
    assert csv_filename("expense tracker") == "expense-tracker-report.csv"


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
