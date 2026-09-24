# AGENTS.md — Planning Log

This file tracks planning decisions and progress for RepoScout across sessions. Append new entries at the bottom; don't rewrite history.

## 2026-09-22

- Repo currently contains only `README.md` (the project spec) — no code yet.
- README defines the first-useful-version scope: a CLI (`reposcout search "<keyword>"`) that queries GitHub's Search API, fetches stars/last-commit-date/primary-language per repo, buckets repos by activity (active/slowing/stale), prints a terminal summary, exports a CSV, and caches results per keyword for 24 hours.
- Explicitly out of scope this term: browser UI, AI-generated summaries, saved-search tracking/alerts, cross-referencing other sources, cloning repos, multi-user auth.
- Next step (not yet started): scaffold the project (language/framework choice, GitHub API client, CLI entrypoint, cache layer, CSV writer).

## 2026-09-22 (later)

- Verified Node.js (v24.21.0) and npm (11.19.0) were already installed — no install needed.
- Installed [OpenSpec](https://openspec.dev) CLI globally via npm. First attempt (`npm install -g openspec`) pulled an unrelated placeholder package (empty, v0.0.0, no binary) — uninstalled it. Correct package is `@fission-ai/openspec@latest`; installed that instead (CLI v1.13.1).
- Ran `openspec init --tools claude` in the repo root. This created:
  - `openspec/config.yaml` (schema: spec-driven) plus `openspec/specs/` and `openspec/changes/archive/` directories
  - `.claude/commands/opsx/*.md` and `.claude/skills/openspec-*/SKILL.md` — Claude Code slash commands/skills for the OpenSpec workflow (propose, update, apply, archive, explore, sync)
- Nothing committed yet — `openspec/`, `.claude/`, and `AGENTS.md` are untracked in git.
- Next step: decide whether to start the actual project scaffold via OpenSpec's proposal workflow (`/opsx:propose`) or scaffold directly, then commit the OpenSpec setup files.

## 2026-09-24 — Design decisions from `/opsx:explore` session

Worked through the full design for the first-useful-version tool (README §3), plus a deliberate set of extras beyond the README's literal wording, chosen because the goal is a tool the user and a friend will actually keep using, not just a one-off class submission. Nothing has been built yet — this is a decision record to carry into `/opsx:propose`.

**Language & core libraries**
- Python (required by the course), minimum version **3.10+**.
- GitHub API access via raw `requests` calls directly against the REST API — no wrapper library (e.g. not PyGithub) — chosen so API call counts are fully controllable and observable (needed to satisfy the README's "verified by a logged call count" cache test).
- Per-repo "last commit date" uses the `pushed_at` field already returned by GitHub's Search API response, **not** a separate per-repo commits-endpoint call. This cuts API usage from ~51 calls/search down to ~1, which also defuses most of the README's rate-limit risk (§5).
- CLI argument parsing: **typer**.
- Terminal table rendering: **tabulate**.
- Relative time phrasing (e.g. "2 weeks ago") for the verdict line: **humanize**.
- Cross-platform user cache/config directory resolution: **platformdirs**.
- Testing: **pytest** + **responses** (mocks GitHub API responses in tests, and lets tests assert exact call counts) + typer's built-in `CliRunner` (no extra dependency) for invoking the CLI in tests.
- Distribution: installable via `pyproject.toml` with a console-script entry point, so `reposcout search "..."` works as a real command from any directory after `pip install .` — not a plain script invoked via `python reposcout.py`.
- Package/command name: `reposcout` (matches the README's demo command).

**Caching**
- Cache key = normalized query string: casefold + trim + collapse internal whitespace. Deliberately does *not* collapse hyphens and spaces together (e.g. `"expense tracker"` and `"expense-tracker"` stay distinct cache entries), to avoid silently merging searches that could be meaningfully different.
- Storage: **one JSON file per query** (not a single shared file, not SQLite), in the **OS user-level cache directory** (via `platformdirs`) — not a project-local folder — so the cache works consistently no matter what directory the command is run from.
- Each cache file stores the **raw fetched fields per repo** (stars, `pushed_at`, language, name, url) plus a `fetched_at` timestamp. Activity bucketing (active/slowing/stale) and ranking are recomputed fresh on every read, not stored pre-computed — keeps "what we fetched" separate from "how we currently interpret it."
- A `--refresh` CLI flag bypasses the cache read on demand and overwrites the entry, for when a user wants current data before the 24h window expires.
- A corrupted/unreadable cache file is treated as a cache miss (silently refetch and overwrite) rather than surfaced as an error — self-healing, since it's an internal implementation detail the user shouldn't have to deal with.

**GitHub token handling** (extends beyond the README's literal "read from an environment variable" wording)
- Checked in order: `GITHUB_TOKEN` env var first, then a token saved from a prior run.
- If neither is present, the CLI prompts interactively (masked input via stdlib `getpass`, not echoed, not saved to shell history) and saves the token to a config file in the OS user-level config directory (via `platformdirs`), with file permissions set to `0600` on Unix where supported.
- The prompt can be **skipped** (left blank) — the tool then proceeds using GitHub's unauthenticated rate limits. This choice is **remembered**, so the user isn't asked again on every run.
- If/when an unauthenticated rate limit is actually hit, the error message explicitly tells the user to provide a token to raise the limit.
- If a saved token turns out to be invalid/expired (GitHub returns an auth error), the CLI offers to re-enter a new token on the spot, overwriting the bad one, rather than requiring the user to find and edit the config file manually.
- Any GitHub rate-limit-exceeded response is caught and reported with a clear message (including when the limit resets), rather than crashing with a raw stack trace.

**Output shape**
- Terminal table columns: `# | repo name | stars | last commit | language | bucket`. URL is deliberately dropped from the terminal view for readability.
- CSV columns: same as above, plus `url`.
- CSV filename: normalized keyword slugified (lowercase, spaces → hyphens) + `-report.csv`, written to the current working directory. Note: this slugification means `"expense tracker"` and `"expense-tracker"` would produce the *same* filename even though they're distinct cache entries — accepted as a rare, low-stakes edge case; the second write silently overwrites the first.
- Verdict line honesty: when the total matching repos is ≤ 50, the count shown is exact and exhaustive (matches the README's demo wording). When GitHub reports more than 50 total matches, the wording switches to make the cap explicit (e.g. "Showing top 50 of 3,241 matching repos") rather than implying the 50 shown is the full result set. The active/slowing/stale counts in the verdict are always scoped to only the repos actually fetched, never extrapolated to the full match count.
- Export format stays **CSV**, not `.xlsx` — matches the README's explicit spec and acceptance criteria (§3, §4), and CSV already opens natively in Excel/Sheets/Numbers, so the main practical benefit of `.xlsx` (native spreadsheet double-click) is already covered without an extra dependency.

**Noted but deliberately out of scope for this build**
- A proper user manual / usage documentation doesn't exist yet — flagged during the session as something to write once the tool is built, not before.
- The user mentioned a possible future direction of using this tool as a data-collection instrument for a master's thesis in Survey Statistics and Data Analytics (e.g. survival-analysis-style research on repo activity/abandonment patterns). Noted as context for why raw fetched data is kept rather than only computed summaries, but this is not part of the current build scope.

**Next step:** run `/opsx:propose` to turn this decision record into buildable OpenSpec artifacts (proposal, design, specs, tasks).
