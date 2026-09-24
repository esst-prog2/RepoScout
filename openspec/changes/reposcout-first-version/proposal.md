# Proposal

## Why

Manually browsing GitHub's search results and eyeballing "updated X ago" across dozens of repos to judge which ones are actually active is slow, and GitHub's UI has no way to export the results for further comparison. RepoScout automates that triage into a single command that fetches, ranks, and classifies matching repos, and produces both a quick terminal summary and a CSV for offline analysis.

## What Changes

- Add a new installable Python CLI, `reposcout`, with a `search "<keyword>"` command.
- Query GitHub's repo Search API for a keyword and fetch the top 50 results by stars.
- Capture stars, last-commit proxy (`pushed_at`), and primary language per repo directly from the search response (no per-repo follow-up call).
- Classify each repo into an activity bucket: active (commit in last 3 months), slowing (3-12 months), stale (12+ months).
- Print a terminal table (rank, repo name, stars, last commit, language, bucket) and a one-line verdict summarizing counts and the most recently pushed repo; the verdict is honest about GitHub's total match count when it exceeds the 50 fetched.
- Export the full ranked, bucketed list to a CSV (same columns as the table, plus repo URL) in the current working directory, named from the slugified keyword.
- Cache search results per normalized keyword for 24 hours in the OS user cache directory, to avoid redundant GitHub API calls on repeat searches; add a `--refresh` flag to bypass the cache on demand.
- Add GitHub token handling: read from the `GITHUB_TOKEN` environment variable, fall back to a token saved from a prior run, and otherwise prompt interactively (masked, skippable, skip remembered) and persist the entered token to a local config file.
- Handle GitHub rate-limit and auth-error responses gracefully with clear, actionable messages instead of crashing.
- Package the project with `pyproject.toml` and a console-script entry point so `reposcout` works as a real command after `pip install .`.
- Add a user manual (`docs/USER_MANUAL.md`) covering installation, GitHub token setup, the `search` command and its `--refresh` flag, output format, and where cache/config files are stored.

## Capabilities

### New Capabilities
- `repo-search`: Querying GitHub for repos matching a keyword, capturing stars/last-commit/language per repo, ranking and bucketing by activity, and producing the terminal table, one-line verdict, and CSV export.
- `search-cache`: Caching search results per normalized keyword for 24 hours to avoid redundant GitHub API calls, including cache-key normalization, one-file-per-query storage, the `--refresh` bypass, and self-healing on a corrupted cache file.
- `github-auth`: Acquiring and persisting a GitHub personal access token (environment variable, saved config, or interactive prompt) and handling GitHub rate-limit and invalid-token responses gracefully.

### Modified Capabilities
None — this is a new project with no existing specs.

## Impact

- New Python project; no existing code is affected (repo currently contains only `README.md`, `AGENTS.md`, and OpenSpec/Claude scaffolding).
- New runtime dependencies: `requests`, `typer`, `tabulate`, `humanize`, `platformdirs`.
- New dev/test dependencies: `pytest`, `responses`.
- New files: `pyproject.toml`, a `reposcout` source package, and a test suite.
- Requires a GitHub personal access token (or accepting reduced unauthenticated rate limits) to be useful in practice.
