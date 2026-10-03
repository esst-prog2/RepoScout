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

## 2026-09-24 (later) — Proposal generated, then updated to include a user manual

Ran `/opsx:propose`, which created the OpenSpec change `reposcout-first-version` (`openspec/changes/reposcout-first-version/`) with `proposal.md`, three spec deltas (`repo-search`, `search-cache`, `github-auth`), `design.md`, and `tasks.md` — all validated (`openspec validate --strict` passes). Committed as `62c1442`.

Decided not to push to `origin/main` yet — will push once the first working version exists, rather than syncing partial/planning-only state.

The user then asked for a user manual to be built alongside the code, which had been deliberately deferred during the explore session (see the previous entry's "Noted but deliberately out of scope" note). Ran `/opsx:update` to fold this back in before implementation starts: added task group 9 (`docs/USER_MANUAL.md`, covering install/token setup/search command/`--refresh`/output/cache-config locations, plus linking it from `README.md`) to `tasks.md`, a matching bullet to `proposal.md`'s "What Changes", and corrected a now-stale line in `design.md`'s Migration Plan that had said the manual was tracked separately. Re-validated successfully after the edit.

**Next step:** run `/opsx:apply` to start implementation.

## 2026-09-24 (later) — First version implemented (33/33 tasks)

Ran `/opsx:apply`. Built the full `reposcout` package (`cli.py`, `github.py`, `cache.py`, `auth.py`, `bucketing.py`, `output.py`), `pyproject.toml` with a console-script entry point, and a 43-test `pytest` suite (including explicit acceptance tests mapping to README §4). Set up a local `.venv` for development and added `.gitignore`. Wrote `docs/USER_MANUAL.md` and linked it from `README.md`.

One real implementation finding along the way: Typer collapses a single-command app so it drops the subcommand name — fixed by adding an empty `@app.callback()`, which is Typer's documented way to keep `search` as an explicit subcommand (matching `reposcout search "<keyword>"` from the spec) instead of letting it collapse to `reposcout "<keyword>"`.

All 33 tasks passed except 8.4 (the manual live-API smoke test), which needed a real GitHub token I didn't have. The user generated a fine-grained personal access token (Public Repositories: read-only, no other permissions needed) and ran the smoke test themselves in their own terminal — using the interactive token prompt so the token was never typed into this conversation. It worked: a real search for "expense tracker" correctly returned "Showing top 50 of 234450 matching repos, 10 active among them — most recent entrant pushed 40 minutes ago", confirming the "top 50 of N" honesty wording works against live data. Task 8.4 marked done.

That live test also surfaced a genuine usability problem: the token prompt used stdlib `getpass`, which shows nothing at all while typing/pasting — giving no feedback on whether a paste worked. This directly caused a real paste-truncation issue during testing (the user's first two token attempts were silently corrupted and got rejected by GitHub as invalid). Fixed by switching to `pwinput`, a small drop-in replacement that echoes `*` per character (still never reveals the token) — updated `design.md`'s token-prompt decision, `proposal.md`'s dependency list, `docs/USER_MANUAL.md`'s wording, `auth.py`, and the corresponding tests. Full suite re-verified at 43/43 passing after the change.

Change `openspec validate --strict` still passes. Nothing pushed to `origin/main` yet (still deliberately deferred, per the earlier decision to push once a working version exists) — worth revisiting now that the tool is actually working end-to-end.

**Next step:** commit the implementation, consider pushing, and whenever ready, `/opsx:archive` to close out the change.

## 2026-10-03 — Housekeeping: first change archived (via a separate session)

A separate Claude Code session (running Claude Opus 5.5, outside this conversation) made two commits while this session was open: `8c3f964` ("Update user manual" — picked up this session's uncommitted Quick Start addition to `docs/USER_MANUAL.md` and committed it) and `a5dab7f` ("Archive reposcout-first-version and sync its specs" — ran `/opsx:archive`, moved the change to `openspec/changes/archive/2026-10-03-reposcout-first-version/`, and synced its three delta specs into `openspec/specs/github-auth/spec.md`, `openspec/specs/repo-search/spec.md`, and `openspec/specs/search-cache/spec.md`). Both commits are local only (not yet pushed to `origin/main`) as of this note.

This reverses the earlier decision (recorded above) to skip archiving since the assignment didn't require it — apparently decided otherwise in that other session. Noted here so this session's own record stays accurate; no action taken on it from here, just documented for continuity.

## 2026-10-03 (later) — Proposed: graceful API failure handling

The course instructor reviewed the project and suggested hardening it before the December demo: right now a GitHub rate-limit response or a network failure (no internet, DNS failure, timeout) hits code that expects a successful result, risking a crash with a raw traceback during a live, uncontrolled-network demo.

Ran `/opsx:propose` for a new, separate change `graceful-api-failure-handling` (deliberately not reopening the already-archived `reposcout-first-version`). Since the main specs now exist (per the housekeeping note above), this proposal correctly targets them as **Modified Capabilities** rather than writing fresh delta specs from scratch:
- MODIFIED the existing `github-auth` "Graceful rate-limit-exceeded handling" requirement to add a dedicated exit code (`2`), replacing the generic `1` it shared with other errors.
- ADDED a new `github-auth` requirement for network-failure handling (connection error or timeout, both explicitly — `requests.exceptions.Timeout` is not a subclass of `ConnectionError`, a real pitfall flagged in `design.md`), with its own exit code (`3`).
- Decided (user-approved) exit code scheme: `1` = generic error (e.g. invalid token), `2` = rate limit, `3` = network failure.

All 4 artifacts (`proposal.md`, `specs/github-auth/spec.md`, `design.md`, `tasks.md`) created and validated (`openspec validate --strict` passes). Nothing implemented yet.

**Next step:** run `/opsx:apply` to implement.

## 2026-10-03 (later, after apply) — Implemented, and HW4 begins

`/opsx:apply` completed all 8 tasks for `graceful-api-failure-handling`: added `NetworkError`, named exit codes (`2` rate-limit, `3` network failure, `1` generic), `network_error_message()`, wired both into `search`, and added CLI-level tests asserting the exact exit code for each. 47/47 tests passing. Committed (`e8fec34`) and pushed to `origin/main`.

A new assignment (HW4) followed: a "spike" — a time-boxed investigation producing an answer, not a feature — defined in a GitHub Issue titled "Your spike" in this repo. Before starting the formal spike work, the issue also flagged a real, separate bug worth a quick fix first:

**Rate-limit numbers were wrong in three places.** RepoScout only ever calls GitHub's *Search* endpoint, which has its own stricter, per-minute limits (10/minute unauthenticated, 30/minute authenticated) — distinct from the general "core" API's 60/hour and 5,000/hour limits, which RepoScout never actually hits. The code and docs had been using the core-API figures by mistake, meaning the unauthenticated rate-limit error message was telling users to go get a token when, since the real limit resets every minute, often just waiting briefly would have fixed it faster. Corrected in:
- `reposcout/auth.py`'s `rate_limit_message()` — unauthenticated branch now states 10/30 requests-per-minute correctly, and mentions that waiting briefly often resolves it, alongside the token option.
- `docs/USER_MANUAL.md`'s token section — same correction.
- `README.md` §5's "Rate limits" risk note — numbers corrected to the per-minute search-endpoint figures; left the rest of that paragraph (including the already-superseded "one follow-up call per repo" framing) untouched, since that reflects what was anticipated at the time the original spec was written, not a claim about the final build.

47/47 tests still passing after the fix.

**The actual spike** (separate from the above): "is `pushed_at` the last commit?" — `github.py` reads a repo's `pushed_at` from the Search API response and `output.py` prints it as "Last Commit," but these aren't guaranteed to be the same thing (the issue cites `twbs/bootstrap`, where `pushed_at` was 5 days newer than the actual last default-branch commit). Since the entire active/slowing/stale verdict rests on this field, the spike asks: across 50 repos from one live search, how often does `pushed_at` disagree with the real last-commit date (fetched via `/commits?per_page=1` per repo), and how many of those 50 change activity bucket as a result? Answer format: median drift in days + count of bucket flips. Evidence type: commit the script and the 50 rows of data.

**Next step:** fix committed, then start the formal spike workflow — `git switch -c hw4-spike`, log the question/answer-criteria, run the real experiment.
