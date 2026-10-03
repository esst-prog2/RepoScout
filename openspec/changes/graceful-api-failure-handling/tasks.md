# Tasks

## 1. Network-failure detection (`reposcout/github.py`)

- [ ] 1.1 Add a `NetworkError(GitHubAPIError)` exception class alongside the existing `RateLimitExceeded`/`InvalidTokenError` — verify it imports and constructs with no errors
- [ ] 1.2 Wrap the `requests.get(...)` call in `search_repositories()` in a `try`/`except` catching `requests.exceptions.ConnectionError` and `requests.exceptions.Timeout` (named explicitly, not the broader `RequestException`) and re-raising as `NetworkError` — verify with a `responses`-mocked test that simulates a `ConnectionError` and asserts `NetworkError` is raised

## 2. Exit codes and messages (`reposcout/cli.py`, `reposcout/auth.py`)

- [ ] 2.1 Add named exit-code constants (`RATE_LIMIT_EXIT_CODE = 2`, `NETWORK_ERROR_EXIT_CODE = 3`) in `cli.py` and use them in place of the current generic `typer.Exit(code=1)` on `RateLimitExceeded` — verify the constant is referenced at every `RateLimitExceeded` catch site in `search`
- [ ] 2.2 Add a `network_error_message()` helper (in `auth.py`, alongside `rate_limit_message()`) returning a clear message (e.g. "Could not reach GitHub, check your internet connection") — verify with a unit test asserting the message mentions "GitHub" and "internet"/"connection"
- [ ] 2.3 Wire `NetworkError` into the `search` command's exception handling (alongside the existing `RateLimitExceeded`/`InvalidTokenError` handling) so it prints the network-error message and exits with `NETWORK_ERROR_EXIT_CODE` — verify no raw traceback reaches the user

## 3. Tests

- [ ] 3.1 CLI-level test: mock a rate-limited HTTP response (403 with `X-RateLimit-Remaining: 0`, or 429) via `responses`, run the `search` command via `typer.testing.CliRunner`, and assert both the printed message (mentions the reset time) and `result.exit_code == 2`
- [ ] 3.2 CLI-level test: mock a connection error via `responses` (e.g. `responses.add(responses.GET, SEARCH_URL, body=requests.exceptions.ConnectionError())`), run the `search` command via `CliRunner`, and assert both the printed message (mentions GitHub/connection) and `result.exit_code == 3`
- [ ] 3.3 Run the full existing test suite (`pytest tests/`) and confirm all prior tests still pass alongside the two new ones — verify via the test run's summary line
