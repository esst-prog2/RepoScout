# Proposal

## Why

RepoScout will be demonstrated live, on a network and with API quota the presenter doesn't control. Today, a GitHub rate-limit response is only partially distinguished from other failures (exit code is the same generic `1` used elsewhere), and a network failure (no internet, DNS failure, timeout) isn't caught at all — it would crash with a raw Python traceback mid-demo. This change makes both failure modes degrade gracefully with a clear, distinct message, so a "bad network day" during the demo looks intentional instead of broken.

## What Changes

- Tighten the existing rate-limit handling: the CLI prints a message naming the reset time and exits with a dedicated code (`2`), instead of the generic `1` used for other errors.
- Add network-failure handling (connection error or timeout reaching GitHub) — currently unhandled anywhere in the codebase. The CLI prints a clear message and exits with a dedicated code (`3`), distinct from both the rate-limit code and the generic `1`.
- Add two new automated tests (HTTP mocked, no real network): one driving the rate-limited path and asserting the message and exit code `2`; one driving a connection-error/timeout path and asserting the message and exit code `3`.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `github-auth`: the existing "Graceful rate-limit-exceeded handling" requirement gains a specific exit code; a new requirement is added for graceful network-failure handling (connection error or timeout), with its own distinct exit code.

## Impact

- Affected code: `reposcout/github.py` (new exception type for network failures, catching `requests.exceptions.ConnectionError` and `requests.exceptions.Timeout` around the HTTP call), `reposcout/cli.py` (exit codes `2` and `3`, wiring the new exception), `reposcout/auth.py` (if a network-failure message helper is added alongside the existing `rate_limit_message`).
- Affected tests: `tests/test_github.py` and/or `tests/test_cli.py` gain the two new failure-path tests.
- No new dependencies, no changes to the cache, search, or token-storage behavior.
