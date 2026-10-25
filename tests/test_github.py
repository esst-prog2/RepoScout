from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

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

    result = search_repositories("expense tracker", token=None)

    assert len(responses.calls) == 1
    assert result.total_count == 2
    assert [r.name for r in result.repos] == ["a/one", "a/two"]
    assert result.repos[0].stars == 100
    assert result.repos[0].language == "Python"
    assert result.repos[0].pushed_at == datetime(2026, 8, 1, tzinfo=timezone.utc)


@responses.activate
def test_search_lets_github_rank_by_relevance_not_stars():
    responses.add(responses.GET, SEARCH_URL, json=search_payload(0, []), status=200)

    search_repositories("repo activity research", token=None)

    query = parse_qs(urlparse(responses.calls[0].request.url).query)
    assert query["q"] == ["repo activity research"]
    assert query["per_page"] == ["50"]
    assert "sort" not in query
    assert "order" not in query


@responses.activate
def test_total_count_distinct_from_fetched_items():
    payload = search_payload(3241, [repo_item("a/one", 100)])
    responses.add(responses.GET, SEARCH_URL, json=payload, status=200)

    result = search_repositories("popular keyword", token=None)

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
        search_repositories("expense tracker", token=None)

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
        search_repositories("expense tracker", token=None)


@responses.activate
def test_timeout_raises_network_error():
    responses.add(
        responses.GET,
        SEARCH_URL,
        body=requests.exceptions.Timeout("timed out"),
    )

    with pytest.raises(NetworkError):
        search_repositories("expense tracker", token=None)


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


@responses.activate
def test_rate_limit_without_reset_headers_has_unknown_reset_time():
    responses.add(responses.GET, SEARCH_URL, json={}, status=429)

    with pytest.raises(RateLimitExceeded) as excinfo:
        search_repositories("expense tracker", token="t")

    assert excinfo.value.reset_at is None


@pytest.mark.parametrize(
    "body",
    [
        {"message": "something unexpected"},
        {"total_count": 1, "items": [{"full_name": "a/b"}]},
        {"total_count": 1, "items": None},
    ],
)
@responses.activate
def test_success_response_without_expected_fields_raises_instead_of_zero_results(body):
    responses.add(responses.GET, SEARCH_URL, json=body, status=200)

    with pytest.raises(GitHubAPIError):
        search_repositories("expense tracker", token="t")


@responses.activate
def test_incomplete_results_flag_is_kept():
    body = search_payload(1, [repo_item("a/one", 100)]) | {"incomplete_results": True}
    responses.add(responses.GET, SEARCH_URL, json=body, status=200)

    assert search_repositories("expense tracker", token="t").incomplete is True


@pytest.mark.parametrize("missing", ["incomplete_results", "language"])
@responses.activate
def test_missing_always_present_field_is_an_error_not_a_default(missing):
    body = search_payload(1, [repo_item("a/one", 100)])
    if missing == "language":
        del body["items"][0]["language"]
    else:
        del body[missing]
    responses.add(responses.GET, SEARCH_URL, json=body, status=200)

    with pytest.raises(GitHubAPIError):
        search_repositories("expense tracker", token=None)


@responses.activate
def test_null_language_is_normal_not_an_error():
    item = repo_item("a/one", 100) | {"language": None}
    responses.add(responses.GET, SEARCH_URL, json=search_payload(1, [item]), status=200)

    assert search_repositories("expense tracker", token=None).repos[0].language is None


@responses.activate
def test_error_body_that_is_not_an_object_still_reports_the_status():
    responses.add(responses.GET, SEARCH_URL, json=["unexpected"], status=500)

    with pytest.raises(GitHubAPIError, match="HTTP 500"):
        search_repositories("expense tracker", token=None)


def test_token_must_be_passed_explicitly():
    with pytest.raises(TypeError):
        search_repositories("expense tracker")
