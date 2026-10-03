"""Raw GitHub Search API client: fetches repo data and translates error responses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

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
    reset_header = response.headers.get("X-RateLimit-Reset")
    if reset_header is not None:
        return datetime.fromtimestamp(int(reset_header), tz=timezone.utc)
    return datetime.now(timezone.utc)


def _handle_error_response(response: requests.Response, authenticated: bool) -> None:
    if response.status_code == 401:
        raise InvalidTokenError()
    if response.status_code in (403, 429):
        remaining = response.headers.get("X-RateLimit-Remaining")
        if remaining == "0" or response.status_code == 429:
            raise RateLimitExceeded(_parse_reset_time(response), authenticated)
    response.raise_for_status()


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

    payload = response.json()
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
