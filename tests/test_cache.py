from datetime import datetime, timedelta, timezone

from reposcout.cache import cache_path, normalize_query, read_cache, write_cache
from reposcout.github import RepoData

NOW = datetime(2026, 9, 24, 12, 0, tzinfo=timezone.utc)


def test_normalize_query_case_and_whitespace_equivalence():
    assert normalize_query("expense tracker") == normalize_query("Expense   Tracker")
    assert normalize_query("  Expense Tracker  ") == normalize_query("expense tracker")


def test_normalize_query_hyphen_distinct_from_space():
    assert normalize_query("expense tracker") != normalize_query("expense-tracker")


def test_hyphen_and_space_variants_use_different_cache_files(isolated_dirs):
    assert cache_path("expense tracker") != cache_path("expense-tracker")


def _repo(name: str = "a/one") -> RepoData:
    return RepoData(name=name, url=f"https://github.com/{name}", stars=10, pushed_at=NOW, language="Python")


def test_write_then_read_round_trips_raw_fields(isolated_dirs):
    repos = [_repo()]
    write_cache("expense tracker", total_count=1, repos=repos, now=NOW)

    entry = read_cache("expense tracker", now=NOW)

    assert entry is not None
    assert entry.total_count == 1
    assert entry.repos[0].name == "a/one"
    assert entry.repos[0].stars == 10
    assert entry.repos[0].pushed_at == NOW


def test_cache_hit_within_24_hours(isolated_dirs):
    write_cache("expense tracker", total_count=1, repos=[_repo()], now=NOW)

    entry = read_cache("expense tracker", now=NOW + timedelta(hours=23))

    assert entry is not None


def test_cache_expired_after_24_hours(isolated_dirs):
    write_cache("expense tracker", total_count=1, repos=[_repo()], now=NOW)

    entry = read_cache("expense tracker", now=NOW + timedelta(hours=25))

    assert entry is None


def test_missing_cache_file_is_a_miss(isolated_dirs):
    assert read_cache("never searched", now=NOW) is None


def test_corrupted_cache_file_is_treated_as_a_miss(isolated_dirs):
    path = cache_path("expense tracker")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json", encoding="utf-8")

    entry = read_cache("expense tracker", now=NOW)

    assert entry is None
