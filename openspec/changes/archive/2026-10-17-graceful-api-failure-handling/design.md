# Design

## Context

`reposcout/github.py` already defines a `GitHubAPIError` base exception with `RateLimitExceeded` and `InvalidTokenError` subclasses, raised from `_handle_error_response()` after `requests.get(...)` returns an HTTP response. It does not currently wrap the `requests.get(...)` call itself in any `try`/`except` — if that call raises (no response at all, e.g. no network or a timeout), the exception propagates uncaught up through `cli.py` and crashes with a traceback. `cli.py`'s `search` command currently calls `raise typer.Exit(code=1)` on a caught `RateLimitExceeded`. See `proposal.md` for why this matters now (live demo robustness).

## Goals / Non-Goals

**Goals:**
- Make a GitHub rate-limit response and a network failure (no connection reaching GitHub at all) fully distinguishable from each other and from success, via message and exit code.
- Keep the fix localized to the existing `github.py` → `auth.py` → `cli.py` error-handling path already in place for `RateLimitExceeded`/`InvalidTokenError`, rather than restructuring it.

**Non-Goals:**
- Retrying failed requests automatically (out of scope — the ask is "fail clearly," not "recover").
- Distinguishing finer-grained network failure types (DNS failure vs. connection refused vs. TLS error) from each other — all are reported as one "could not reach GitHub" case.
- Changing behavior for `InvalidTokenError` (401) — unaffected by this change.

## Decisions

**New exception type: `NetworkError(GitHubAPIError)`, raised around the `requests.get(...)` call itself (not inside `_handle_error_response`, which only runs after a response is received).** `search_repositories()` wraps the request in `try: ... except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc: raise NetworkError() from exc`. These two are caught explicitly rather than the broader `requests.exceptions.RequestException` because `RequestException` would also catch things like `HTTPError` from `response.raise_for_status()` inside `_handle_error_response` — conflating "we got a response GitHub didn't like" with "we never got a response at all" would blur exactly the distinction this change exists to make.

**`requests.exceptions.Timeout` is not a subclass of `ConnectionError`** (both are direct subclasses of `RequestException`), so both must be named explicitly in the `except` clause — a plausible implementation mistake (assuming `ConnectionError` alone covers "no network") is called out here so it isn't made silently.

**Exit codes become explicit, named constants** (e.g. `RATE_LIMIT_EXIT_CODE = 2`, `NETWORK_ERROR_EXIT_CODE = 3`) in `cli.py` rather than inline magic numbers, so the two-test requirement (asserting specific codes) has a single source of truth to reference and codes can't silently drift apart from what's documented in the user-facing message.

**Message wording lives alongside the existing `rate_limit_message()` helper in `auth.py`** — add a sibling `network_error_message()` function there (or inline in `cli.py` if trivial) rather than putting user-facing strings in `github.py`, keeping `github.py` focused on detection/translation and `auth.py`/`cli.py` on presentation, matching the existing split.

## Risks / Trade-offs

- **[Risk]** A network failure could also theoretically occur mid-response-read (after headers arrive, during body streaming), which `requests.exceptions.ChunkedEncodingError` or similar would represent, and isn't covered by the two caught exception types. → **Mitigation:** Accepted as out of scope — this is a rare failure mode in practice for a small JSON response, and the two exceptions named cover the realistic "no network" and "timeout" cases the professor's note specifically describes.
- **[Risk]** Hardcoding exit codes 2 and 3 could collide with codes a future feature wants to use for something unrelated. → **Mitigation:** Low risk for a small CLI with few failure modes; named constants make any future collision easy to spot and renumber.
