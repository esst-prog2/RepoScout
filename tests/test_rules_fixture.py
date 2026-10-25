"""Shared rules fixture, Python side.

tests/fixtures/rules.json is fixed reference data, checked by this file and by
tests/js/rules.test.mjs (the web page's site/rules.js). Two implementations,
one fixture: a rule changed in only one language fails a test. Edit the
fixture by hand, on purpose; never regenerate it from either implementation.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests
import responses

from reposcout.bucketing import BucketedRepo, classify_bucket
from reposcout.cache import normalize_query
from reposcout.github import (
    SEARCH_URL,
    GitHubAPIError,
    RepoData,
    _is_rate_limited,
    _parse_reset_time,
    search_repositories,
)
from reposcout.output import csv_filename, format_verdict, time_ago, write_csv

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "rules.json").read_text(encoding="utf-8"))
NOW = datetime.fromisoformat(FIXTURE["now"].replace("Z", "+00:00"))


def _when(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _bucketed(repo: dict) -> BucketedRepo:
    pushed = _when(repo["pushed_at"])
    data = RepoData(name=repo["name"], url=repo["url"], stars=repo["stars"], pushed_at=pushed, language=repo["language"])
    return BucketedRepo(repo=data, bucket=classify_bucket(pushed, now=NOW))


def _response(status: int, headers: dict) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response.headers.update(headers)
    return response


@pytest.mark.parametrize("case", FIXTURE["bucket"], ids=lambda c: c["pushed_at"])
def test_bucket(case):
    assert classify_bucket(_when(case["pushed_at"]), now=NOW) == case["expected"]


@pytest.mark.parametrize("case", FIXTURE["time_ago"], ids=lambda c: str(c["seconds"]))
def test_time_ago(case):
    assert time_ago(timedelta(seconds=case["seconds"])) == case["expected"]


@pytest.mark.parametrize("case", FIXTURE["verdict"], ids=lambda c: c["name"])
def test_verdict(case):
    assert format_verdict(case["total_count"], [_bucketed(r) for r in case["repos"]], now=NOW) == case["expected"]


@pytest.mark.parametrize("case", FIXTURE["normalize"], ids=lambda c: c["input"])
def test_normalize(case):
    assert normalize_query(case["input"]) == case["expected"]


@pytest.mark.parametrize("case", FIXTURE["filename"], ids=lambda c: c["input"])
def test_filename(case):
    assert csv_filename(case["input"]) == case["expected"]


def test_csv(tmp_path):
    path = tmp_path / "report.csv"
    write_csv(path, [_bucketed(r) for r in FIXTURE["csv"]["repos"]])
    assert path.read_bytes().decode("utf-8") == FIXTURE["csv"]["expected"]


@pytest.mark.parametrize("case", FIXTURE["rate_limit"], ids=lambda c: c["name"])
def test_rate_limit(case):
    # The CLI only checks non-OK responses; a 200 is never treated as limited.
    response = _response(case["status"], case["headers"])
    limited = (not response.ok) and _is_rate_limited(response)
    assert limited is case["limited"]


@pytest.mark.parametrize("case", FIXTURE["reset"], ids=lambda c: c["name"])
def test_reset(case):
    result = _parse_reset_time(_response(429, case["headers"]))
    expected = case["expected"]
    if expected is None:
        assert result is None
    elif "epoch" in expected:
        assert result == datetime.fromtimestamp(expected["epoch"], tz=timezone.utc)
    else:  # Retry-After is relative to the real clock in the CLI
        target = datetime.now(timezone.utc) + timedelta(seconds=expected["retry_after_seconds"])
        assert abs((result - target).total_seconds()) < 5


@responses.activate
@pytest.mark.parametrize("case", FIXTURE["payload"], ids=lambda c: c["name"])
def test_payload(case):
    responses.add(responses.GET, SEARCH_URL, json=case["body"], status=200)
    if case["valid"]:
        assert len(search_repositories("anything", token=None).repos) == len(case["body"]["items"])
    else:
        with pytest.raises(GitHubAPIError, match="doesn't understand"):
            search_repositories("anything", token=None)
