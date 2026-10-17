"""Raw GitHub Search API client: fetches repo data and translates error responses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests

SEARCH_URL = "https://api.github.com/search/repositories"
PER_PAGE = 50


class GitHubAPIError(Exception):
    """Base class for GitHub API failures the CLI must handle gracefully."""


class RateLimitExceeded(GitHubAPIError):
    def __init__(self, reset_at: datetime, authenticated: bool):
        self.reset_at = reset_at
        self.authenticated = authenticated
        super().__init__(f"GitHub rate limit exceeded, resets at {reset_at.isoformat()}")


class InvalidTokenError(GitHubAPIError):
    def __init__(self):
        super().__init__("GitHub rejected the provided token as invalid or expired")


class NetworkError(GitHubAPIError):
    def __init__(self):
        super().__init__("Could not reach GitHub (connection error or timeout)")


@dataclass(frozen=True)
class RepoData:
    name: str
    url: str
    stars: int
    pushed_at: datetime
    language: str | None


@dataclass(frozen=True)
class SearchResult:
    total_count: int
    repos: list[RepoData]


def _parse_reset_time(response: requests.Response) -> datetime:
    retry_after = response.headers.get("Retry-After")
    if retry_after is not None and retry_after.isdigit():
        return datetime.now(timezone.utc) + timedelta(seconds=int(retry_after))
    reset_header = response.headers.get("X-RateLimit-Reset")
    if reset_header is not None:
        return datetime.fromtimestamp(int(reset_header), tz=timezone.utc)
    return datetime.now(timezone.utc)


def _is_rate_limited(response: requests.Response) -> bool:
    """Primary limit: remaining hits 0. Secondary limit: 403/429 with Retry-After."""
    if response.status_code == 429:
        return True
    if response.status_code == 403:
        return (
            response.headers.get("X-RateLimit-Remaining") == "0"
            or "Retry-After" in response.headers
        )
    return False


def _handle_error_response(response: requests.Response, authenticated: bool) -> None:
    """Translate every non-OK response into a typed error - never a raw requests one."""
    if response.status_code == 401:
        raise InvalidTokenError()
    if _is_rate_limited(response):
        raise RateLimitExceeded(_parse_reset_time(response), authenticated)
    try:
        detail = response.json().get("message", "")
    except ValueError:
        detail = ""
    message = f"GitHub returned an error (HTTP {response.status_code})"
    raise GitHubAPIError(f"{message}: {detail}" if detail else f"{message}.")


def search_repositories(keyword: str, token: str | None = None) -> SearchResult:
    """Search GitHub for repos matching keyword, top PER_PAGE results by stars.

    Uses only fields already present in the search response (stars, pushed_at,
    language) - no per-repo follow-up call.
    """
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {
        "q": keyword,
        "sort": "stars",
        "order": "desc",
        "per_page": PER_PAGE,
    }
    try:
        response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=30)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        raise NetworkError() from exc

    if not response.ok:
        _handle_error_response(response, authenticated=bool(token))

    try:
        payload = response.json()
    except ValueError as exc:
        raise GitHubAPIError("GitHub returned a response that isn't valid JSON.") from exc
    repos = [
        RepoData(
            name=item["full_name"],
            url=item["html_url"],
            stars=item["stargazers_count"],
            pushed_at=datetime.strptime(item["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            ),
            language=item.get("language"),
        )
        for item in payload.get("items", [])
    ]
    return SearchResult(total_count=payload.get("total_count", len(repos)), repos=repos)
