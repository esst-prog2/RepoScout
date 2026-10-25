import csv

import requests
import responses
from typer.testing import CliRunner

from reposcout import auth
from reposcout.cli import app
from reposcout.github import SEARCH_URL

from helpers import repo_item, search_payload

runner = CliRunner()


def _no_prompt(*args, **kwargs):
    raise AssertionError("prompt should not have been invoked")


@responses.activate
def test_search_end_to_end_prints_table_verdict_and_writes_csv(isolated_dirs, monkeypatch, tmp_path):
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "test-token")
    monkeypatch.chdir(tmp_path)
    payload = search_payload(1, [repo_item("a/one", 100)])
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
def test_refresh_flag_bypasses_cache(isolated_dirs, monkeypatch, tmp_path):
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "test-token")
    monkeypatch.chdir(tmp_path)
    payload = search_payload(1, [repo_item("a/one", 100)])
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
def test_unexpected_github_error_is_reported_cleanly(isolated_dirs, monkeypatch, tmp_path):
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "test-token")
    monkeypatch.chdir(tmp_path)
    responses.add(responses.GET, SEARCH_URL, json={"message": "Validation Failed"}, status=422)

    result = runner.invoke(app, ["search", "expense tracker"])

    assert result.exit_code == 1
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "HTTP 422" in result.stdout
    assert "Validation Failed" in result.stdout


@responses.activate
def test_rejected_token_is_replaced_and_search_retried(isolated_dirs, monkeypatch, tmp_path):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "bad-token")
    monkeypatch.setattr("reposcout.auth.pwinput.pwinput", lambda prompt, mask: "good-token")
    monkeypatch.chdir(tmp_path)
    responses.add(responses.GET, SEARCH_URL, json={"message": "Bad credentials"}, status=401)
    responses.add(responses.GET, SEARCH_URL, json=search_payload(1, [repo_item("a/one", 100)]), status=200)

    result = runner.invoke(app, ["search", "expense tracker"])

    assert result.exit_code == 0
    assert responses.calls[1].request.headers["Authorization"] == "Bearer good-token"
    assert result.stdout.count("invalid or expired") == 1
    assert "a/one" in result.stdout


@responses.activate
def test_rejected_replacement_token_exits_cleanly(isolated_dirs, monkeypatch, tmp_path):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "bad-token")
    monkeypatch.setattr("reposcout.auth.pwinput.pwinput", lambda prompt, mask: "also-bad")
    monkeypatch.chdir(tmp_path)
    responses.add(responses.GET, SEARCH_URL, json={"message": "Bad credentials"}, status=401)
    responses.add(responses.GET, SEARCH_URL, json={"message": "Bad credentials"}, status=401)

    result = runner.invoke(app, ["search", "expense tracker"])

    assert result.exit_code == 1
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "rejected the new token as well" in result.stdout


@responses.activate
def test_rejected_env_var_token_says_fix_the_variable_without_prompting(isolated_dirs, monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_TOKEN", "bad-env-token")
    monkeypatch.setattr("reposcout.auth.pwinput.pwinput", _no_prompt)
    monkeypatch.chdir(tmp_path)
    responses.add(responses.GET, SEARCH_URL, json={"message": "Bad credentials"}, status=401)

    result = runner.invoke(app, ["search", "expense tracker"])

    assert result.exit_code == 1
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "GITHUB_TOKEN" in result.stdout
    assert "update or unset" in result.stdout
    assert "saved" not in result.stdout
    assert len(responses.calls) == 1
    assert not auth.config_path().exists()


@responses.activate
def test_incomplete_results_warning_is_shown_and_survives_the_cache(isolated_dirs, monkeypatch, tmp_path):
    monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "test-token")
    monkeypatch.chdir(tmp_path)
    body = search_payload(1, [repo_item("a/one", 100)]) | {"incomplete_results": True}
    responses.add(responses.GET, SEARCH_URL, json=body, status=200)

    first = runner.invoke(app, ["search", "expense tracker"])
    second = runner.invoke(app, ["search", "expense tracker"])  # served from cache

    assert len(responses.calls) == 1
    for result in (first, second):
        assert result.exit_code == 0
        assert "may be incomplete" in result.stdout
