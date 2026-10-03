"""GitHub token resolution: env var, saved config, or interactive skippable prompt."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import platformdirs
import pwinput

from reposcout.github import RateLimitExceeded

APP_NAME = "reposcout"
ENV_VAR = "GITHUB_TOKEN"

PROMPT_TEXT = (
    "No GitHub token found. Enter a GitHub personal access token to raise your "
    "rate limit (leave blank to skip): "
)
INVALID_TOKEN_TEXT = (
    "Your saved GitHub token appears invalid or expired. Enter a replacement "
    "(leave blank to skip): "
)


def config_path() -> Path:
    return Path(platformdirs.user_config_dir(APP_NAME)) / "config.json"


def _load_config() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_config(data: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    if os.name == "posix":
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def prompt_for_token(prompt_text: str = PROMPT_TEXT) -> str | None:
    """Prompt for a token with `*` feedback per character (not the token itself)."""
    entered = pwinput.pwinput(prompt=prompt_text, mask="*")
    entered = entered.strip()
    return entered or None


def resolve_token() -> str | None:
    """Resolve a token: env var, then saved config, then an interactive prompt."""
    env_token = os.environ.get(ENV_VAR)
    if env_token:
        return env_token

    config = _load_config()
    if config.get("token"):
        return config["token"]
    if config.get("skipped"):
        return None

    token = prompt_for_token()
    if token:
        config["token"] = token
        _save_config(config)
        return token

    config["skipped"] = True
    _save_config(config)
    return None


def handle_invalid_token() -> str | None:
    """Called when a saved token is rejected by GitHub; offers immediate re-entry."""
    print(
        "Your saved GitHub token appears invalid or expired.", flush=True
    )
    token = prompt_for_token(INVALID_TOKEN_TEXT)
    config = _load_config()
    if token:
        config["token"] = token
        config.pop("skipped", None)
        _save_config(config)
        return token

    config.pop("token", None)
    config["skipped"] = True
    _save_config(config)
    return None


def rate_limit_message(error: RateLimitExceeded) -> str:
    reset_str = error.reset_at.strftime("%Y-%m-%d %H:%M UTC")
    if not error.authenticated:
        return (
            "GitHub's unauthenticated rate limit was reached. Provide a GitHub "
            "personal access token to raise this limit to 5,000 requests/hour — "
            f"run reposcout again to be prompted, or set {ENV_VAR}. "
            f"(Resets at {reset_str}.)"
        )
    return f"GitHub API rate limit reached, try again after {reset_str}."


def network_error_message() -> str:
    return "Could not reach GitHub, check your internet connection."
