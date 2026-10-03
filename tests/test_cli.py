import csv

import requests
import responses
from typer.testing import CliRunner

from reposcout.cli import app
from reposcout.github import SEARCH_URL

runner = CliRunner()


def _search_payload(total_count: int, items: list[dict]) -> dict:
    return {"total_count": total_count, "incomplete_results": False, "items": items}


def _item(name: str, stars: int, pushed_at: str = "2026-08-01T00:00:00Z") -> dict:
    return {
        "full_name": name,
        "html_url": f"https://github.com/{name}",
        "stargazers_count": stars,
        "language": "Python",
        "pushed_at": pushed_at,
    }


@responses.activate
def test_search_end_to_end_prints_table_verdict_and_writes_csv(isolated_dirs, monkeypatch, tmp_path):
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "test-token")
    monkeypatch.chdir(tmp_path)
    payload = _search_payload(1, [_item("a/one", 100)])
    responses.add(responses.GET, SEARCH_URL, json=payload, status=200)

    result = runner.invoke(app, ["search", "expense tracker"])

    assert result.exit_code == 0
    assert "a/one" in result.stdout
    assert "1 repos found" in result.stdout
    csv_path = tmp_path / "expense-tracker-report.csv"
    assert csv_path.exists()
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[1][1] == "a/one"


@responses.activate
def test_second_search_within_cache_window_makes_zero_api_calls(isolated_dirs, monkeypatch, tmp_path):
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "test-token")
    monkeypatch.chdir(tmp_path)
    payload = _search_payload(1, [_item("a/one", 100)])
    responses.add(responses.GET, SEARCH_URL, json=payload, status=200)

    first = runner.invoke(app, ["search", "expense tracker"])
    assert first.exit_code == 0
    assert len(responses.calls) == 1

    second = runner.invoke(app, ["search", "expense tracker"])
    assert second.exit_code == 0
    assert len(responses.calls) == 1  # no additional call


@responses.activate
def test_refresh_flag_bypasses_cache(isolated_dirs, monkeypatch, tmp_path):
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "test-token")
    monkeypatch.chdir(tmp_path)
    payload = _search_payload(1, [_item("a/one", 100)])
    responses.add(responses.GET, SEARCH_URL, json=payload, status=200)
    responses.add(responses.GET, SEARCH_URL, json=payload, status=200)

    first = runner.invoke(app, ["search", "expense tracker"])
    assert first.exit_code == 0
    assert len(responses.calls) == 1

    second = runner.invoke(app, ["search", "expense tracker", "--refresh"])
    assert second.exit_code == 0
    assert len(responses.calls) == 2  # refresh forced a fresh call


@responses.activate
def test_rate_limit_error_is_reported_cleanly(isolated_dirs, monkeypatch, tmp_path):
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "test-token")
    monkeypatch.chdir(tmp_path)
    responses.add(
        responses.GET,
        SEARCH_URL,
        json={"message": "API rate limit exceeded"},
        status=403,
        headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1800000000"},
    )

    result = runner.invoke(app, ["search", "expense tracker"])

    assert result.exit_code == 2
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "rate limit" in result.stdout.lower()
    # 1800000000 unix -> 2027-01-15 08:00 UTC
    assert "2027-01-15 08:00" in result.stdout
    assert "Traceback" not in result.stdout


@responses.activate
def test_network_error_is_reported_cleanly(isolated_dirs, monkeypatch, tmp_path):
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "test-token")
    monkeypatch.chdir(tmp_path)
    responses.add(
        responses.GET,
        SEARCH_URL,
        body=requests.exceptions.ConnectionError("no route to host"),
    )

    result = runner.invoke(app, ["search", "expense tracker"])

    assert result.exit_code == 3
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "github" in result.stdout.lower()
    assert "connection" in result.stdout.lower() or "internet" in result.stdout.lower()
    assert "Traceback" not in result.stdout


@responses.activate
def test_zero_match_search_prints_message_and_writes_headers_only_csv(isolated_dirs, monkeypatch, tmp_path):
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "test-token")
    monkeypatch.chdir(tmp_path)
    payload = _search_payload(0, [])
    responses.add(responses.GET, SEARCH_URL, json=payload, status=200)

    result = runner.invoke(app, ["search", "no such repo exists xyz"])

    assert result.exit_code == 0
    assert "0 repos found" in result.stdout
    csv_path = tmp_path / "no-such-repo-exists-xyz-report.csv"
    assert csv_path.exists()
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert len(rows) == 1
