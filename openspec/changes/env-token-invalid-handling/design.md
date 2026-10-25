# Design

## Context

`auth.resolve_token()` returns only the token string, so `cli._fetch_with_token_recovery()` can't tell where it came from and always calls `auth.handle_invalid_token()` on a 401, the saved-token path. `resolve_token()` returns the env var's value whenever `GITHUB_TOKEN` is set and non-empty, before looking at the config. See proposal.md for the bug itself.

## Goals / Non-Goals

**Goals:**
- Route a rejected env-var token to a "fix your variable" message and exit `1`, through the existing `GitHubAPIError` handler in `search`.
- Leave the saved-token recovery path, its messages, and its tests unchanged.

**Non-Goals:**
- Changing the token resolution order (env var still wins).
- Offering a one-run replacement prompt for the env-var case (option B in the discussion; rejected because the user would be asked again every run until the variable is fixed).

## Decisions

**Tell the source apart with `auth.token_from_env()`, not by changing `resolve_token()`'s return type.** Because `resolve_token()` returns the env-var token exactly when `GITHUB_TOKEN` is set and non-empty, "the env var is set" is equivalent to "the token came from the env var". A small `token_from_env() -> bool` in `auth.py` expresses that with the same `os.environ.get(ENV_VAR)` truthiness check `resolve_token()` uses. Alternative considered: make `resolve_token()` return `(token, source)`. More explicit, but it changes a function called from `search` and patched in many tests (`monkeypatch.setattr("reposcout.cli.auth.resolve_token", lambda: "...")`) for no behavioural gain.

**Report through `GitHubAPIError`, not a new exception or exit code.** `_fetch_with_token_recovery()` already turns token failures into `GitHubAPIError`, which `search` prints and exits `1` with. The env-var case is raised the same way, with the message built by a new `auth.invalid_env_token_message()` (next to `rate_limit_message()` / `network_error_message()`), naming `GITHUB_TOKEN` and saying to update or unset it. Exit `1` matches the spec's code for an invalid token; no new code needed.

**Check order inside the 401 branch:** the existing `token is None` guard first (unauthenticated 401), then `token_from_env()`, then the saved-token recovery.

## Risks / Trade-offs

- [Risk] A test that patches `resolve_token` to return a token while `GITHUB_TOKEN` happens to be set in the developer's real environment would take the env-var branch. → Mitigation: the `isolated_dirs` fixture / CLI tests that exercise the 401 path must `monkeypatch.delenv("GITHUB_TOKEN", raising=False)` (or `setenv` for the new test) so the outcome doesn't depend on the machine running the tests.
- [Trade-off] A user with a bad env-var token gets no search result that run, where option B would have finished the search. Accepted: one clear instruction beats a prompt on every run.
