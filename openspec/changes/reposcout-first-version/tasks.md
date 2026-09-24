# Tasks

## 1. Project setup

- [ ] 1.1 Create the `reposcout/` package skeleton (`cli.py`, `github.py`, `cache.py`, `auth.py`, `bucketing.py`, `output.py`, `__init__.py`) and verify the package imports without error (`python -c "import reposcout"`)
- [ ] 1.2 Create `pyproject.toml` (setuptools build backend) declaring runtime dependencies (`requests`, `typer`, `tabulate`, `humanize`, `platformdirs`), dev dependencies (`pytest`, `responses`), Python 3.10+ requirement, and a `reposcout` console-script entry point, and verify `pip install -e .` succeeds
- [ ] 1.3 Verify the installed command works end-to-end as a smoke test: `reposcout --help` runs and shows the `search` command

## 2. GitHub API client (`github.py`)

- [ ] 2.1 Implement a search function that calls GitHub's repo Search API for a keyword, requests up to 50 results ordered by stars, and returns each repo's name, url, stars, `pushed_at`, and language straight from the search response (no per-repo follow-up call) — verify with a `responses`-mocked test asserting exactly one HTTP call is made per fresh search
- [ ] 2.2 Implement `total_count` capture from the search response, distinct from the number of repos actually returned, for later use in the "top 50 of N" verdict wording — verify with a mocked response where `total_count` exceeds 50
- [ ] 2.3 Implement detection and translation of GitHub's rate-limit-exceeded response (authenticated and unauthenticated) into a typed exception carrying the reset time — verify with a `responses`-mocked 403/rate-limit response and an assertion on the parsed reset time
- [ ] 2.4 Implement detection and translation of an invalid/expired-token response (401) into a typed exception — verify with a `responses`-mocked 401 response

## 3. Activity bucketing (`bucketing.py`)

- [ ] 3.1 Implement bucket classification from a `pushed_at` timestamp into `active` (<3 months), `slowing` (3-12 months), or `stale` (12+ months) — verify with parametrized unit tests covering a value just inside and just outside each boundary
- [ ] 3.2 Implement ranking (sort by stars descending) over a list of fetched repos — verify with a unit test on an unsorted input list

## 4. Caching (`cache.py`)

- [ ] 4.1 Implement cache key normalization (casefold, trim, collapse internal whitespace, hyphens left distinct from spaces) — verify with unit tests for the `search-cache` spec's case/whitespace-equivalence and hyphen-distinctness scenarios
- [ ] 4.2 Implement per-query cache file read/write in `platformdirs.user_cache_dir("reposcout")`, storing raw per-repo fields plus a `fetched_at` timestamp — verify with a test that writes then reads back an entry and gets the same raw fields
- [ ] 4.3 Implement 24-hour expiry logic (an entry older than 24h is treated as a miss) — verify with a unit test using a stubbed/frozen clock
- [ ] 4.4 Implement corrupted/unreadable cache file handling as a silent cache miss (no error raised) — verify with a test that writes malformed JSON to a cache file path and asserts a fresh fetch occurs instead of a crash
- [ ] 4.5 Wire cache-hit short-circuiting into the search flow so a valid, unexpired entry results in zero GitHub API calls — verify with a `responses`-mocked test asserting zero calls on the second identical search within the cache window
- [ ] 4.6 Implement the `--refresh` bypass (skip cache read, always fetch, overwrite entry) — verify with a test asserting a GitHub call happens even when a valid cache entry exists, when `--refresh` is passed

## 5. GitHub token handling (`auth.py`)

- [ ] 5.1 Implement token resolution order: `GITHUB_TOKEN` env var, then saved config file, then interactive prompt (only if neither is present and the user hasn't previously skipped) — verify with unit tests for each precedence case
- [ ] 5.2 Implement the interactive masked prompt (via stdlib `getpass`) that saves an entered token to a config file in `platformdirs.user_config_dir("reposcout")`, setting `0600` permissions via `os.chmod` where supported — verify with a test that simulates prompt input and asserts the saved file's content and (on a POSIX-like test environment) permissions
- [ ] 5.3 Implement skip handling: an empty prompt response is saved as a persistent "skipped" marker so the prompt does not reappear on later runs — verify with a test asserting a second run does not invoke the prompt after a prior skip
- [ ] 5.4 Implement the unauthenticated-rate-limit message that tells the user to provide a token — verify with a test asserting the specific message text appears when the rate-limit exception from 2.3 occurs with no token in use
- [ ] 5.5 Implement invalid/expired saved-token recovery: on the 401 exception from 2.4, tell the user the saved token is invalid and immediately re-prompt, overwriting the saved config on a new entry — verify with a test simulating a 401 followed by prompt input and asserting the config file is overwritten

## 6. Output (`output.py`)

- [ ] 6.1 Implement the terminal table (via `tabulate`) with columns rank, repo name, stars, last commit date, language, bucket (no URL column), sorted by stars descending — verify with a snapshot/text-content test on sample data
- [ ] 6.2 Implement the one-line verdict: exact count and active-bucket count when `total_count` ≤ 50, "top 50 of N" phrasing when `total_count` > 50, most-recently-pushed repo phrased via `humanize` relative time, and bucket counts always scoped to fetched repos only — verify with unit tests for both the ≤50 and >50 cases
- [ ] 6.3 Implement CSV export (table columns plus `url`) to `<slugified-keyword>-report.csv` in the current working directory, including the zero-match case (header row only) — verify with a test asserting file contents for a populated result set and for an empty one
- [ ] 6.4 Verify filename slug derivation (lowercase, whitespace collapsed to hyphens) matches the README's demo example (`"expense tracker"` → `expense-tracker-report.csv`) with a unit test

## 7. CLI wiring (`cli.py`)

- [ ] 7.1 Implement the `search "<keyword>"` command (via `typer`) wiring together auth resolution, cache lookup, GitHub fetch, bucketing/ranking, and output, including the `--refresh` flag — verify with a `typer.testing.CliRunner` test running a full search against `responses`-mocked GitHub data
- [ ] 7.2 Wire rate-limit and invalid-token exceptions from `github.py`/`auth.py` into clean CLI-level error output (no raw traceback) — verify with a `CliRunner` test asserting exit code and message on a mocked rate-limit response
- [ ] 7.3 Verify the zero-match path end-to-end via `CliRunner`: "0 repos found" printed and a headers-only CSV written, no error raised

## 8. Acceptance verification (README §4)

- [ ] 8.1 Automated test: a keyword with zero matching repos prints "0 repos found" and writes a headers-only CSV, not an error
- [ ] 8.2 Automated test: a repo with no commits in the last 3 months is bucketed as `slowing` or `stale`, never `active`
- [ ] 8.3 Automated test: running the same keyword twice within 24 hours makes zero GitHub API calls on the second run, verified via the `responses` mock's logged call count
- [ ] 8.4 Manual smoke test: run `reposcout search "<some real keyword>"` against the live GitHub API with a real token and confirm the terminal table, verdict line, and CSV all look correct
