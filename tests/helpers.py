"""Fake GitHub Search API payloads shared by the tests that mock HTTP."""


def search_payload(total_count: int, items: list[dict]) -> dict:
    return {"total_count": total_count, "incomplete_results": False, "items": items}


def repo_item(name: str, stars: int, pushed_at: str = "2026-08-01T00:00:00Z") -> dict:
    return {
        "full_name": name,
        "html_url": f"https://github.com/{name}",
        "stargazers_count": stars,
        "language": "Python",
        "pushed_at": pushed_at,
    }
