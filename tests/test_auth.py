import json
import os

import pytest

from reposcout import auth
from reposcout.github import RateLimitExceeded


def _no_prompt(*args, **kwargs):
    raise AssertionError("prompt should not have been invoked")


def test_env_var_takes_precedence_and_skips_config(isolated_dirs, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "env-token")
    monkeypatch.setattr("pwinput.pwinput", _no_prompt)

    token = auth.resolve_token()

    assert token == "env-token"
    assert not auth.config_path().exists()


def test_saved_token_used_without_prompting(isolated_dirs, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr("pwinput.pwinput", _no_prompt)
    auth.config_path().parent.mkdir(parents=True, exist_ok=True)
    auth.config_path().write_text(json.dumps({"token": "saved-token"}), encoding="utf-8")

    token = auth.resolve_token()

    assert token == "saved-token"


def test_prompt_entered_token_is_saved(isolated_dirs, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr("pwinput.pwinput", lambda prompt="", mask="*": "typed-token")

    token = auth.resolve_token()

    assert token == "typed-token"
    saved = json.loads(auth.config_path().read_text(encoding="utf-8"))
    assert saved["token"] == "typed-token"
    if os.name == "posix":
        mode = auth.config_path().stat().st_mode & 0o777
        assert mode == 0o600


def test_skipping_prompt_is_remembered(isolated_dirs, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr("pwinput.pwinput", lambda prompt="", mask="*": "")

    first = auth.resolve_token()
    assert first is None
    saved = json.loads(auth.config_path().read_text(encoding="utf-8"))
    assert saved["skipped"] is True

    monkeypatch.setattr("pwinput.pwinput", _no_prompt)
    second = auth.resolve_token()
    assert second is None


def test_unauthenticated_rate_limit_message_mentions_token():
    from datetime import datetime, timezone

    error = RateLimitExceeded(datetime.now(timezone.utc), authenticated=False)

    message = auth.rate_limit_message(error)

    assert "token" in message.lower()
    assert "GITHUB_TOKEN" in message


def test_authenticated_rate_limit_message_states_reset_time():
    from datetime import datetime, timezone

    error = RateLimitExceeded(datetime(2026, 9, 24, 15, 0, tzinfo=timezone.utc), authenticated=True)

    message = auth.rate_limit_message(error)

    assert "2026-09-24 15:00" in message


def test_handle_invalid_token_saves_replacement(isolated_dirs, monkeypatch, capsys):
    auth.config_path().parent.mkdir(parents=True, exist_ok=True)
    auth.config_path().write_text(json.dumps({"token": "bad-token"}), encoding="utf-8")
    monkeypatch.setattr("pwinput.pwinput", lambda prompt="", mask="*": "new-token")

    token = auth.handle_invalid_token()

    assert token == "new-token"
    saved = json.loads(auth.config_path().read_text(encoding="utf-8"))
    assert saved["token"] == "new-token"
    assert "skipped" not in saved
    assert "invalid" in capsys.readouterr().out.lower()


def test_handle_invalid_token_blank_response_skips(isolated_dirs, monkeypatch):
    auth.config_path().parent.mkdir(parents=True, exist_ok=True)
    auth.config_path().write_text(json.dumps({"token": "bad-token"}), encoding="utf-8")
    monkeypatch.setattr("pwinput.pwinput", lambda prompt="", mask="*": "")

    token = auth.handle_invalid_token()

    assert token is None
    saved = json.loads(auth.config_path().read_text(encoding="utf-8"))
    assert "token" not in saved
    assert saved["skipped"] is True
