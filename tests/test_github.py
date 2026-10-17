from datetime import datetime, timezone

import pytest
import requests
import responses

from reposcout.github import (
    SEARCH_URL,
    GitHubAPIError,
    InvalidTokenError,
    NetworkError,
    RateLimitExceeded,
    search_repositories,
)

from helpers import repo_item, search_payload


@responses.activate
def test_search_returns_repos_from_single_call():
    payload = search_payload(2, [repo_item("a/one", 100), repo_item("a/two", 50)])
    responses.add(responses.GET, SEARCH_URL, json=payload, status=200)

    result = search_repositories("expense tracker")

    assert len(responses.calls) == 1
    assert result.total_count == 2
    assert [r.name for r in result.repos] == ["a/one", "a/two"]
    assert result.repos[0].stars == 100
    assert result.repos[0].language == "Python"
    assert result.repos[0].pushed_at == datetime(2026, 8, 1, tzinfo=timezone.utc)


@responses.activate
def test_total_count_distinct_from_fetched_items():
    payload = search_payload(3241, [repo_item("a/one", 100)])
    responses.add(responses.GET, SEARCH_URL, json=payload, status=200)

    result = search_repositories("popular keyword")

    assert result.total_count == 3241
    assert len(result.repos) == 1


@responses.activate
def test_rate_limit_exceeded_parses_reset_time():
    reset_ts = 1_800_000_000
    responses.add(
        responses.GET,
        SEARCH_URL,
        json={"message": "API rate limit exceeded"},
        status=403,
        headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(reset_ts)},
    )

    with pytest.raises(RateLimitExceeded) as exc_info:
        search_repositories("expense tracker")

    assert exc_info.value.reset_at == datetime.fromtimestamp(reset_ts, tz=timezone.utc)
    assert exc_info.value.authenticated is False


@responses.activate
def test_rate_limit_exceeded_authenticated_flag():
    responses.add(
        responses.GET,
        SEARCH_URL,
        json={"message": "API rate limit exceeded"},
        status=403,
        headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1800000000"},
    )

    with pytest.raises(RateLimitExceeded) as exc_info:
        search_repositories("expense tracker", token="tok")

    assert exc_info.value.authenticated is True


@responses.activate
def test_connection_error_raises_network_error():
    responses.add(
        responses.GET,
        SEARCH_URL,
        body=requests.exceptions.ConnectionError("no route to host"),
    )

    with pytest.raises(NetworkError):
        search_repositories("expense tracker")


@responses.activate
def test_timeout_raises_network_error():
    responses.add(
        responses.GET,
        SEARCH_URL,
        body=requests.exceptions.Timeout("timed out"),
    )

    with pytest.raises(NetworkError):
        search_repositories("expense tracker")


@responses.activate
def test_invalid_token_raises():
    responses.add(
        responses.GET,
        SEARCH_URL,
        json={"message": "Bad credentials"},
        status=401,
    )

    with pytest.raises(InvalidTokenError):
        search_repositories("expense tracker", token="bad-token")


@responses.activate
def test_secondary_rate_limit_403_with_retry_after_raises_rate_limit():
    responses.add(
        responses.GET,
        SEARCH_URL,
        json={"message": "You have exceeded a secondary rate limit."},
        status=403,
        headers={"Retry-After": "60", "X-RateLimit-Remaining": "25"},
    )

    with pytest.raises(RateLimitExceeded):
        search_repositories("expense tracker", token="t")


@pytest.mark.parametrize(
    "status,kwargs",
    [
        (422, {"json": {"message": "Validation Failed"}}),
        (500, {"json": {"message": "Server Error"}}),
        (403, {"json": {"message": "Forbidden"}}),
        (502, {"body": "<html>Bad Gateway</html>"}),
    ],
)
@responses.activate
def test_any_other_error_status_raises_github_api_error(status, kwargs):
    responses.add(responses.GET, SEARCH_URL, status=status, **kwargs)

    with pytest.raises(GitHubAPIError) as excinfo:
        search_repositories("expense tracker", token="t")

    assert not isinstance(excinfo.value, (RateLimitExceeded, InvalidTokenError, NetworkError))
    assert str(status) in str(excinfo.value)


@responses.activate
def test_non_json_success_body_raises_github_api_error():
    responses.add(responses.GET, SEARCH_URL, status=200, body="<html>captive portal</html>")

    with pytest.raises(GitHubAPIError):
        search_repositories("expense tracker", token="t")
