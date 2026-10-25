"""GitHub token resolution: env var, saved config, or interactive skippable prompt."""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

import platformdirs
import pwinput

from reposcout import APP_NAME
from reposcout.github import RateLimitExceeded

ENV_VAR = "GITHUB_TOKEN"

PROMPT_TEXT = (
    "No GitHub token found. Enter a GitHub personal access token to raise your "
    "rate limit (leave blank to skip): "
)
INVALID_TOKEN_TEXT = "Enter a replacement token (leave blank to skip): "


def config_path() -> Path:
    return Path(platformdirs.user_config_dir(APP_NAME)) / "config.json"


def _load_config() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("not a JSON object")
        return data
    except (ValueError, OSError) as exc:
        # Say so instead of acting as if no token was ever saved: the user may
        # otherwise skip the prompt and overwrite a token they thought was kept.
        print(
            f"Warning: could not read saved settings at {path} ({exc}); ignoring them.",
            file=sys.stderr,
            flush=True,
        )
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

    return _remember_choice(config, prompt_for_token())


def token_from_env() -> bool:
    """True when the token in use came from GITHUB_TOKEN (resolve_token checks it first)."""
    return bool(os.environ.get(ENV_VAR))


def handle_invalid_token() -> str | None:
    """Called when a saved token is rejected by GitHub; offers immediate re-entry."""
    print(
        "Your saved GitHub token appears invalid or expired.", flush=True
    )
    return _remember_choice(_load_config(), prompt_for_token(INVALID_TOKEN_TEXT))


def _remember_choice(config: dict, token: str | None) -> str | None:
    """Save an entered token, or remember that the user chose to skip."""
    if token:
        config["token"] = token
        config.pop("skipped", None)
    else:
        config.pop("token", None)
        config["skipped"] = True
    _save_config(config)
    return token


def rate_limit_message(error: RateLimitExceeded) -> str:
    if error.reset_at is not None:
        when = f"after {error.reset_at.strftime('%Y-%m-%d %H:%M UTC')}"
    else:
        when = "in a minute or two; GitHub did not say when it resets"
    if not error.authenticated:
        return (
            "GitHub's unauthenticated search rate limit (10 requests/minute) was "
            "reached. This resets within a minute, so waiting briefly often works — "
            "or provide a GitHub personal access token to raise it to 30 requests/"
            f"minute (run reposcout again to be prompted, or set {ENV_VAR}). "
            f"(Try again {when}.)"
        )
    return f"GitHub API rate limit reached, try again {when}."


def invalid_env_token_message() -> str:
    return (
        f"The GitHub token in your {ENV_VAR} environment variable appears invalid or "
        f"expired. Please update or unset {ENV_VAR} and try again."
    )


def network_error_message() -> str:
    return "Could not reach GitHub, check your internet connection."
