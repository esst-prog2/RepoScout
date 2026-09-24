import pytest


@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    """Redirect the cache and config directories to a temp path for the test."""
    cache_dir = tmp_path / "cache"
    config_dir = tmp_path / "config"
    monkeypatch.setattr("reposcout.cache._cache_dir", lambda: cache_dir)
    monkeypatch.setattr("reposcout.auth.config_path", lambda: config_dir / "config.json")
    return cache_dir, config_dir
