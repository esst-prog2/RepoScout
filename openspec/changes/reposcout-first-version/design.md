# Design

## Context

Greenfield project — no existing code, only `README.md` (the original spec) and `AGENTS.md` (a planning log recording the decisions this design formalizes). See `proposal.md` for motivation. This document exists because the change touches several cross-cutting concerns (a new external API integration, a new local data store, and a new local secret store) and pulls in five new runtime dependencies, all of which benefit from being decided explicitly before coding starts.

## Goals / Non-Goals

**Goals:**
- Deliver a working, installable `reposcout` CLI implementing the three capabilities in `proposal.md` (repo-search, search-cache, github-auth).
- Keep GitHub API usage minimal and observable, so caching correctness and rate-limit behavior are both easy to verify and easy to test without real network calls.
- Make the tool pleasant enough for a non-technical friend to install and use, not just functional enough to satisfy the class assignment.

**Non-Goals** (in addition to the ones already listed in the README's "Not this term" section):
- OS keychain / credential-manager integration for the saved GitHub token (plain local file with best-effort permissions only).
- `.xlsx` export or any styled/colored output format — CSV only.
- Publishing the package to PyPI — local install via `pip install .` only.
- Proactive GitHub rate-limit quota tracking — failures are handled reactively when they occur, not pre-empted.
- Collision-proof CSV filenames (e.g. via a hash suffix) — a rare filename collision between two distinct queries is accepted as a low-stakes, documented trade-off.

## Decisions

**Language & minimum version: Python 3.10+.** Old enough to be broadly available on a friend's machine, new enough to use clean type-hint syntax (e.g. `str | None`) that `typer` relies on without workarounds.

**GitHub access: raw `requests` calls against the REST API, not a wrapper library (e.g. PyGithub).** Alternative considered: PyGithub, rejected because its internal call pattern would make it hard to guarantee and test "zero GitHub API calls on a cache hit," and would obscure exact rate-limit-response handling.

**Last-commit proxy: `pushed_at` from the Search API response itself, not a per-repository commits-endpoint call.** This was originally assumed necessary (per the README's risk section) but reduces API usage from ~51 calls/search to ~1, which also substantially de-risks the rate-limit concern the README raises. Trade-off: `pushed_at` is "last pushed to," not literally "last commit," which is accepted as adequate precision for a 3/12-month bucketing scheme.

**CLI framework: `typer`.** Alternatives considered: stdlib `argparse` (zero dependency, but more boilerplate and weaker `--help` output) and `click` (typer's own foundation, more verbose than typer's type-hint-driven style). Typer chosen for ergonomics and to make adding a future subcommand (e.g. a `config` command) low-friction.

**Terminal table rendering: `tabulate`.** Handles column alignment/padding without pulling in a full styling framework like `rich`.

**Relative time phrasing (e.g. "2 weeks ago") in the verdict line: `humanize`.** Avoids hand-rolling date-rounding rules (is 29 days "1 month" or "4 weeks"?).

**Cross-platform cache/config directory resolution: `platformdirs`.** Used by `pip` itself internally; avoids hand-rolling per-OS path logic (Windows `%LOCALAPPDATA%`, macOS `~/Library/Caches`, Linux `~/.cache` respecting `$XDG_CACHE_HOME`).

**Packaging: `pyproject.toml` with a console-script entry point (`reposcout = reposcout.cli:app`), using `setuptools` as the build backend.** Alternative considered: a plain script invoked via `python reposcout.py` — rejected because the goal is a real installed command usable from any directory, matching how tools like `black`/`poetry`/`httpie` work.

**Cache storage shape: one JSON file per normalized query, in `platformdirs.user_cache_dir("reposcout")`.** Each file stores the *raw* fetched per-repo fields (name, url, stars, `pushed_at`, language) plus a `fetched_at` timestamp — not precomputed bucket labels or rankings. Bucketing and ranking are recomputed on every read. Rationale: decouples "what GitHub returned" from "how we currently interpret it," so a future change to bucket thresholds applies automatically to old cache entries without needing a cache-format migration. Alternative considered: a single shared JSON file (rejected — one corrupted write would risk every cached query, not just one) and SQLite (rejected — heavier than needed for ~40-row result sets and less transparent to a grader/reader).

**Cache key normalization:** casefold, trim, collapse internal whitespace to one space. Deliberately does *not* normalize hyphens to/from spaces, so `"expense tracker"` and `"expense-tracker"` remain distinct cache entries (see `search-cache` spec).

**Token storage:** a small JSON file in `platformdirs.user_config_dir("reposcout")`, written after an interactive `getpass`-masked prompt. File permissions are set to `0600` via `os.chmod` where the OS supports it (POSIX); Windows has no direct stdlib equivalent, so it relies on normal per-account file protection there, consistent with how most cross-platform CLI tools handle this. Plaintext-with-restricted-permissions is the same baseline approach used by `gh`, `aws`, and `docker` CLIs.

**Error handling for GitHub API responses:** HTTP client code inspects response status codes and headers directly (401/403, rate-limit headers) and raises typed exceptions that the CLI layer catches and translates into short, friendly `typer` error output — never letting a raw `requests` exception or stack trace reach the user.

**Testing: `pytest` + `responses` (mocks the `requests` layer, and asserts exact call counts) + `typer.testing.CliRunner`.** This combination maps directly onto the README's own acceptance criteria (§4): zero-match handling, correct bucketing, and a verifiable zero-API-call cache hit.

**Proposed module layout** (illustrative, not binding at the file-name level):
```
reposcout/
  cli.py         # typer app; wires the `search` command together
  github.py      # raw requests calls, response parsing, rate-limit/auth error handling
  cache.py       # key normalization, read/write, 24h expiry, corruption handling
  auth.py        # token resolution order, interactive prompt, config save/load
  bucketing.py   # activity classification + ranking
  output.py      # terminal table (tabulate), verdict line (humanize), CSV export
pyproject.toml
tests/
```

## Risks / Trade-offs

- **[Risk]** `pushed_at` is a proxy for "last commit," not a literal commit timestamp (e.g. it reflects push timing, not authorship timing). → **Mitigation:** Accepted as consistent with the README's own stated limitation (§5, "activity is a proxy, not a fact"); precision loss is negligible at 3/12-month bucket granularity.
- **[Risk]** GitHub's Search API caps retrievable results at 1,000 even when `total_count` reports more, and very broad queries could make `total_count` itself imprecise. → **Mitigation:** The verdict line only claims an exact, exhaustive count when the reported total is ≤ 50 (our own fetch cap); above that it always states "top 50 of N" rather than implying completeness.
- **[Risk]** Two distinct, differently-cached queries (e.g. `"expense tracker"` vs `"expense-tracker"`) can produce the same CSV filename and silently overwrite each other. → **Mitigation:** Explicitly accepted as a rare, low-stakes edge case (an export file is trivially regenerated by re-running the search); documented behavior rather than solved with a filename hash, to keep filenames clean and matching the README's demo.
- **[Risk]** Storing the GitHub token as a local plaintext file, even with restricted permissions, is weaker than OS-keychain-backed storage. → **Mitigation:** Explicitly out of scope for this version (see Non-Goals); this matches the baseline approach of comparable real-world CLI tools, and the token can always be supplied via `GITHUB_TOKEN` instead for anyone who wants to avoid the file entirely.
- **[Risk]** A user who skips the token prompt gets a degraded unauthenticated experience that could resurface confusingly much later. → **Mitigation:** The rate-limit failure message explicitly names the fix at the moment it becomes relevant, rather than requiring the user to remember or discover it separately.

## Migration Plan

Greenfield project — no existing users, data, or deployed version to migrate from. "Install" is simply `pip install .` (documented in the eventual user manual, tracked separately in `AGENTS.md`). "Rollback" is `pip uninstall reposcout`, optionally followed by manually deleting the `reposcout` cache/config directories `platformdirs` resolved — no data migration is needed either way.
