"""Acceptance tests directly encoding README.md §4 'How we would know it works'."""

import csv
from datetime import datetime, timedelta, timezone

import responses
from typer.testing import CliRunner

from reposcout.bucketing import STALE, classify_bucket
from reposcout.cli import app
from reposcout.github import SEARCH_URL

runner = CliRunner()


def _payload(total_count: int, items: list[dict]) -> dict:
    return {"total_count": total_count, "incomplete_results": False, "items": items}


def _item(name: str, stars: int, pushed_at: str) -> dict:
    return {
        "full_name": name,
        "html_url": f"https://github.com/{name}",
        "stargazers_count": stars,
        "language": "Python",
        "pushed_at": pushed_at,
    }


@responses.activate
def test_zero_matching_repos_prints_0_found_and_headers_only_csv_not_an_error(
    isolated_dirs, monkeypatch, tmp_path
):
    """README §4: "Given a keyword with zero matching repos, it prints '0 repos
    found' and writes a CSV with headers only, not an error."""
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "test-token")
    monkeypatch.chdir(tmp_path)
    responses.add(responses.GET, SEARCH_URL, json=_payload(0, []), status=200)

    result = runner.invoke(app, ["search", "totally nonexistent keyword"])

    assert result.exit_code == 0
    assert "0 repos found" in result.stdout
    csv_path = tmp_path / "totally-nonexistent-keyword-report.csv"
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert len(rows) == 1


def test_repo_with_no_recent_commits_is_not_bucketed_active():
    """README §4: "Given a repo with no commits in the last 3 months, it is
    bucketed as 'slowing' or 'stale,' not 'active,' in the summary line."""
    now = datetime(2026, 9, 24, tzinfo=timezone.utc)
    pushed_at = now - timedelta(days=400)  # well over 3 months

    bucket = classify_bucket(pushed_at, now=now)

    assert bucket != "active"
    assert bucket == STALE


@responses.activate
def test_same_keyword_twice_within_24h_makes_zero_api_calls_on_second_run(
    isolated_dirs, monkeypatch, tmp_path
):
    """README §4: "Given the same keyword run twice within 24 hours, the second
    run makes zero GitHub API calls — verified by a logged call count."""
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "test-token")
    monkeypatch.chdir(tmp_path)
    responses.add(
        responses.GET,
        SEARCH_URL,
        json=_payload(1, [_item("a/one", 100, "2026-08-01T00:00:00Z")]),
        status=200,
    )

    runner.invoke(app, ["search", "expense tracker"])
    call_count_after_first = len(responses.calls)

    runner.invoke(app, ["search", "expense tracker"])
    call_count_after_second = len(responses.calls)

    assert call_count_after_first == 1
    assert call_count_after_second == call_count_after_first
