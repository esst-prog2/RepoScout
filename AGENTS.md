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

## 2026-10-03 (later) — HW4 spike: question and answer criteria (before running it)

On branch `hw4-spike`, created from `main` after the rate-limit fix above. Recording the question and what counts as an answer before doing the work, per the assignment's own instruction.

**Question:** How often does `pushed_at` (what `github.py` fetches and `output.py` labels "Last Commit") disagree with a repository's real last commit on its default branch, and how many repositories change activity bucket (active/slowing/stale, using the existing 90/365-day thresholds in `bucketing.py`) as a result of that disagreement?

**Method:** Take 50 repositories from one live GitHub search (reusing `reposcout`'s own search call). For each, fetch the real last commit via `GET /repos/{owner}/{repo}/commits?per_page=1` and record its commit date (using the committer date, i.e. `commit.committer.date` — the date the commit entered the branch — as the "real last commit" reference, rather than the author date, which can differ for rebased/amended commits). Record both `pushed_at` and the real last-commit date for every repo.

**What counts as an answer:** the median drift in days across the 50 repos (|pushed_at − real last commit|), and the count of repos (out of 50) whose activity bucket differs depending on which date is used.

**Evidence type (per the issue):** measured over data — commit the script and the 50 rows it produces.

This is not run yet. The actual numbers will be logged as a separate decision once the script has been run against live data.

## 2026-10-03 (later) — HW4 spike: the answer

Ran `spike/pushed_at_drift.py --fetch` against a live search for `"expense tracker"` (50 repos, `total_count=237753`), then analyzed the committed `spike/pushed_at_drift.csv`.

**Answer: median drift = 0.00 days. Bucket flips = 5/50.**

The distribution is bimodal, not smooth: 29/50 repos have `pushed_at` within seconds of the real default-branch last commit (a normal direct push), while 20/50 diverge by more than a day — and every one of those 20 diverges by more than 5 days, several by hundreds or thousands of days (worst case: `shamahoque/mern-expense-tracker`, 2,057 days ≈ 5.6 years). Nothing sits in between. The median lands at 0 because the near-zero cluster is the larger of the two, but that doesn't mean the field is reliable — it means a slim majority happen to push straight to their default branch, while a substantial minority have `pushed_at` reflecting push activity elsewhere in the repo (another branch, a bot, a tag) that has nothing to do with the default branch's real state.

This confirms the concern: `pushed_at` is not the same thing as "last commit," and for 10% of this sample the difference is large enough to flip the activity-bucket verdict RepoScout prints.

**Decision on what changes:** not the fetch strategy (switching to a real per-repo commit call would reintroduce the N+1-call cost the project deliberately avoided, and the drift pattern being bimodal — near-zero or huge — means no bucket-threshold tuning would catch the 5 flipped repos anyway). Instead, the measured number was added to README.md's existing "Activity is a proxy, not a fact" caveat, turning a previously vague acknowledgment into an evidenced one.

**Next step:** push `hw4-spike` and open the PR (merge commit, keep the branch).

**Follow-up considered and deferred:** whether to switch from `pushed_at` to a real per-repo commit-date fetch outright, now that it's clear the commits endpoint is a *core* API call (60/hour unauthenticated, 5,000/hour authenticated) rather than governed by the tight *search* API limits (10-30/minute). For authenticated users the extra 50 calls/search would be trivial (~1% of budget); for unauthenticated users it would consume ~83% of their hourly core budget in a single search, and every search would get noticeably slower (51 sequential calls vs. 1) regardless of auth. Decided this is a real architecture trade-off deserving its own separate, properly-weighed decision later — not something a single 50-repo sample should settle on its own — so it's noted as an open question in the PR rather than acted on now.

## 2026-10-09 — HW4 grading feedback: the spike exposed a labeling bug too

The spike PR was graded "Complete" — numbers reproduced exactly from the committed CSV. The feedback also flagged a real inconsistency the spike itself had surfaced but not fixed: `output.py` still labeled the `pushed_at` column "Last Commit," even though the spike had just proven that's often not true. Two fixes were offered (rename the column, or compute the real date); chose the rename (Option A) — the bigger fix (Option B, discussed above) stays deferred for the reasons already logged.

Renamed the column from "Last Commit" to "Last Push" in `output.py` (flows into both the terminal table and the CSV automatically, since the CSV headers are derived from the same list). Updated the matching test assertion (`tests/test_output.py`), the example output in `docs/USER_MANUAL.md`, and the "Terminal results table" requirement in the current main spec (`openspec/specs/repo-search/spec.md`) to say "last push date" instead of "last commit date" — edited that main spec file directly rather than going through a formal OpenSpec change/sync cycle, since this is a small accuracy correction to existing behavior, not new behavior, consistent with how the earlier README/docs rate-limit corrections were handled. Left the original README's narrative demo text (§1/§3) untouched, since "last commit date" there is colloquial description of the original plan, not the literal column header. 47/47 tests still passing.

Committed directly to `main` (no branch/PR) per the user's choice, matching how the earlier rate-limit fix was handled — the grading feedback didn't call for a formal branch workflow the way the original spike assignment did.

Final step per the feedback ("check one repo you know well against it"): verifying the displayed "Last Push" date for `EnhancedJax/Bagels` (a repo from the spike's own sample) against GitHub's own UI.

## 2026-10-09 — HW5: the sentence and the expected value (before the test)

On branch `hw5-usable`. Per the session-5 slide for this project ("What you found in Homework 4... 5 of 50 landed in the wrong group... A few projects it calls active may not really have changed lately. A test would go red if...").

**Finished sentence:** A test would go red if RepoScout labels a repo "active" while its real last commit is actually more than 90 days old.

**Expected value, decided before any test runs:** `wisnukurniawan/Compose-Expense`, one of the 50 repos from the HW4 spike sample.
- `pushed_at` (what RepoScout actually displays/uses) = `2026-09-23T23:48:39+00:00` — under 90 days before the spike's `fetched_at` reference (`2026-10-03T10:42:05.733837+00:00`), so RepoScout currently buckets it **active**.
- Real last commit (what's actually true) = `2026-05-05T04:09:48+00:00` — about 151 days before that same reference, so the correct bucket is **slowing**.

**Where this came from:** both dates are recorded verbatim in `spike/pushed_at_drift.csv`, fetched live from GitHub's API during the HW4 spike (`pushed_at` from the search response, the real commit date from `/commits?per_page=1`) — not computed or guessed from RepoScout's own code. The day counts (~10 and ~151) and resulting buckets (active, slowing) were worked out by hand from those two recorded dates, not by running `classify_bucket()` and reading off its answer.

**Next step:** write a test asserting that classifying this repo's real last-commit date (not its `pushed_at`) correctly returns "slowing" — this is the test that currently doesn't exist anywhere in the suite.

## 2026-10-09 (later) — HW5: red, then green

Added `test_real_repo_compose_expense_is_slowing_not_active` to `tests/test_bucketing.py`, encoding the expected value logged above. Ran it once as written first — passed cleanly (8/8 in `test_bucketing.py`), confirming the test is correctly written against today's code.

**Red:** changed one line in `reposcout/bucketing.py` — `ACTIVE_THRESHOLD_DAYS = 90` → `ACTIVE_THRESHOLD_DAYS = 200` — then ran `pytest tests/test_bucketing.py -v`:
```
FAILED tests/test_bucketing.py::test_classify_bucket_boundaries[90-slowing]
FAILED tests/test_bucketing.py::test_real_repo_compose_expense_is_slowing_not_active
  AssertionError: assert 'active' == 'slowing'
2 failed, 6 passed in 0.22s
```
The new test failed exactly as expected (real last commit, at ~151 days, now falls under the widened 200-day "active" window). One existing boundary test failed too as expected collateral, since it shares the same constant.

**Green:** reverted the line back to `ACTIVE_THRESHOLD_DAYS = 90`, ran the full suite:
```
48 passed in 0.34s
```
The broken value was never committed — only the before/after test runs are recorded here, per this step's instruction.

**Next step:** step 6 — use the program once for real, on a keyword the user actually cares about; write the expectation before running, then what actually happened.

**Ideas noted for later (not acted on now):**
- GitHub's search matches keywords loosely (space-separated words, not an exact phrase), so multi-word searches can return loosely-related repos rather than close matches — worth tightening later.
- Interest in a more user-friendly interface eventually, possibly accessible as a web page rather than CLI-only.

## 2026-10-09 (later still) — HW5 step 6: expectation, before running

About to run `reposcout search "repo activity research"` for real, on a topic the user actually cares about (tied to the research direction noted in the 2026-09-24 explore-session entry).

**Expectation, written before running:**
- Total matches: likely under 50 — a niche, academic-sounding phrase, not a common project category.
- Activity mix: likely mostly **stale or slowing**, not active — phrases like this tend to match one-off research/thesis/course projects rather than actively maintained tools, unlike "expense tracker," which matched many actively-developed apps.
- Top result: probably not a polished, high-star mainstream tool — more likely something academic or experimental.

**Next step:** run it for real, then log what actually came out.

## 2026-10-09 (later still) — HW5 step 6: what actually happened

Ran `reposcout search "repo activity research"` for real (no `--refresh`, fresh query). Result: `total_count=76`, 50 repos fetched and shown, bucketed **9 active / 5 slowing / 36 stale**. Top result: `molyswu/hand_detection` (282 stars, stale).

**Comparison against the expectation logged above:**
- Total matches (expected under 50): **wrong** — actual was 76. Not a code bug — several of the 50 results (`hand_detection`, the `fluxion` wifi-cracking tools, etc.) are clearly unrelated to "repo activity research" as a topic, matching only on stray individual words. This is the exact "GitHub matches loosely" issue already noted above as deferred work, now with concrete real-world evidence behind it.
- Activity mix (expected mostly stale/slowing): **correct** — 82% of results (41/50) were stale or slowing, only 9/50 active.
- Top result (expected not polished/mainstream): **correct** — 282 stars, stale, a research-adjacent tool, not a popular actively-maintained project.

Two of three predictions held; the one miss reinforces an already-known, already-deferred issue rather than surfacing a new one. Nothing about this run suggested a RepoScout bug — the tool behaved exactly as designed, the mismatch is in GitHub's search semantics vs. a strict phrase match, which this project doesn't currently try to fix.

**HW5 is now functionally complete** (steps 2-6 all done and logged in order). Remaining: push `hw5-usable` and open the PR.

## 2026-10-17 — HW6: whole-repo review, review 1 of N ("names that aren't in the spec")

On branch `hw6-review`. HW6 asks for specialised reviews of the whole repository (not a diff), one kind of problem per review, each review plus its fix in its own commit. Starting list = the session-6 slides.

**Review 1 — names that aren't in the spec.** Went through every module-level name, constant, exception, and user-visible behaviour in `reposcout/*.py` and checked each against `openspec/specs/*/spec.md` (then the archived `design.md` where the spec was silent).

Findings and what was done:
- **`NetworkError`, `RATE_LIMIT_EXIT_CODE = 2`, `NETWORK_ERROR_EXIT_CODE = 3`** were in the code but not in the main specs. Cause: the `graceful-api-failure-handling` change was fully implemented (8/8 tasks) but never archived, so its delta spec never reached `openspec/specs/github-auth/spec.md`. Fixed by archiving it (`openspec archive graceful-api-failure-handling -y` → `openspec/changes/archive/2026-10-17-graceful-api-failure-handling/`), which synced the exit-code-2 rate-limit requirement and the new network-failure requirement into the main spec.
- **SHA-256-hashed cache filenames** (`cache.py` `cache_path()`) — an agent-invented detail that's in neither the spec nor the design ("one JSON file per normalized query" said nothing about naming). Kept it, since using the raw keyword as the filename would break for keywords with `/`, `:`, `?` etc. (especially on Windows). Written into the `search-cache` spec's "Cache storage isolation per query" requirement so the behaviour is now specified instead of implicit.
- Checked and fine (already covered by spec or design): `PER_PAGE`, the thresholds, `BucketedRepo`/`CacheEntry`/`SearchResult`, `GitHubAPIError`, the `"skipped"` config key, `slugify_keyword`, 429 treated as rate limit.
- Left as-is (minor, not worth spec text): `timeout=30` in `github.py`, and the "GitHub rejected the request as unauthorized" branch for a 401 with no token.

**Noticed during this review but belonging to later reviews (not fixed here):**
- An invalid `GITHUB_TOKEN` *env var* goes through the "saved token" recovery path: the message says "Your saved GitHub token…", the replacement is saved to config, but the env var still wins on the next run, so the user is re-prompted every time. The spec only covers recovery for a *saved* token.
- `handle_invalid_token()` prints "Your saved GitHub token appears invalid or expired." and then the prompt repeats the same sentence.
- `slugify_keyword()` doesn't strip filename-unsafe characters, so e.g. `reposcout search "c++/qt"` would try to write `c++/qt-report.csv` into a non-existent subdirectory and crash.

Specs validate (`openspec validate --specs --strict`), 48/48 tests passing. No code changed in this review.

## 2026-10-17 — HW6 review 2: "patched where it broke, not where it's wrong"

**Looked at:** the git history first — no fix-on-fix chains (only five code commits, and each earlier fix, e.g. the rate-limit numbers and the "Last Push" rename, was made at the root and everywhere at once). The pattern was in the code instead: `github.py`'s error handling enumerated exactly the failure cases that had come up so far (401; 403 with `X-RateLimit-Remaining: 0`; 429; then `ConnectionError` and `Timeout` added by the graceful-failure change), and anything else fell through to `response.raise_for_status()` / `response.json()`. The actual rule, written in the first-version `design.md`, is "never let a raw `requests` exception or stack trace reach the user" — the code never implemented that rule, only its known instances.

**Evidence (probe run through the real CLI, HTTP mocked):** HTTP 422, HTTP 500, a 403 *secondary* rate limit (`Retry-After` header, remaining ≠ 0 — a real GitHub behaviour, plausible during a live demo), and a 200 with a non-JSON body (e.g. a captive-portal page) — all four crashed with a raw `HTTPError` / `JSONDecodeError` traceback.

**Fix (at the rule, not a fifth special case):**
- `_handle_error_response()` now translates *every* non-OK response into a typed error: 401 → `InvalidTokenError`, rate limit → `RateLimitExceeded`, anything else → base `GitHubAPIError("GitHub returned an error (HTTP <status>): <message>")`. No more `raise_for_status()`.
- Rate-limit detection moved into `_is_rate_limited()`, which states GitHub's actual rule: primary (remaining = 0) or secondary (403/429 with `Retry-After`). `_parse_reset_time()` uses `Retry-After` when present.
- A non-JSON success body raises `GitHubAPIError` too.
- `cli.py` catches `GitHubAPIError` (after the specific subclasses) → prints the message, exit code `1`.
- Network-error catching left as `ConnectionError` + `Timeout` (not broadened to `RequestException`) — that was a deliberate, documented decision in the graceful-failure design, not a symptom patch.
- Added the rule to `openspec/specs/github-auth/spec.md` as a new requirement.

Tests: +7 (secondary limit; 422/500/403/502 → `GitHubAPIError`; non-JSON body; CLI-level 422 → clean message, exit 1). 55/55 passing. Probe re-run: all four cases now end cleanly (secondary limit → exit 2, others → exit 1).

Note: the fix added a second copy of the `GitHubAPIError` handler to `cli.py`'s nested retry block, which already duplicated the rate-limit/network handlers — that duplication is for review 3 ("a copy instead of a change").

## 2026-10-17 — HW6 review 3: "a copy instead of a change"

**Looked for:** units that do almost the same job under different names, across all of `reposcout/`, `tests/`, and `spike/`.

**Found and merged (one kept, the copy removed):**
- **The CLI's error handling, twice.** `cli.py` handled `RateLimitExceeded` and `NetworkError` once for the first search and again, copied, in a nested `try` for the retry after a rejected token (and review 2 had just added a second copy of the `GitHubAPIError` handler there too). Moved the "search, and on a rejected token offer re-entry once and retry" logic into `_fetch_with_token_recovery()`, which turns both token failures into a `GitHubAPIError` with the same messages as before. `search` now has one set of handlers.
- **`APP_NAME = "reposcout"`** was defined separately in `auth.py` and `cache.py` (if one ever changed, the cache and config would land in differently named directories). Now defined once in `reposcout/__init__.py` and imported.
- **Keyword normalization, twice.** `output.slugify_keyword()` had its own regex for strip + collapse whitespace + `lower()`, next to `cache.normalize_query()` doing the same with `casefold()`. The `repo-search` spec says the CSV filename comes from the *normalized* keyword, so `slugify_keyword()` is now `normalize_query(keyword).replace(" ", "-")`. Only visible difference is casefold vs. lower for a few non-ASCII letters (e.g. `ß` → `ss`), which now matches the cache key's rule.
- **Table row vs. CSV row.** `render_table()` and `write_csv()` built the same six-field row separately (only the missing-language placeholder `-` vs. empty differs, plus the CSV's extra URL). Both now use one `_row()` helper, so a column change can't land in only one of them, which would have mattered for the "Last Commit" → "Last Push" rename.
- **Saving the token choice, twice.** `resolve_token()` and `handle_invalid_token()` each had their own "save the token, or remember the skip" code. Now one `_remember_choice()` does it.
- **The "invalid or expired" sentence, twice.** `handle_invalid_token()` printed it and then the prompt text repeated it, so users saw it twice in a row. The prompt now just says "Enter a replacement token (leave blank to skip): ".
- **Test fixtures, three copies.** `_search_payload`/`_payload` and `_item` were defined separately in `test_cli.py`, `test_github.py`, and `test_acceptance.py`. Now one copy in `tests/helpers.py`.

**Checked and deliberately left:** `spike/pushed_at_drift.py`'s `_fetch_real_last_commit()` builds its own auth headers and parses dates like `github.py` does. Left alone because it's the frozen HW4 evidence script that produced the committed CSV, and it already reuses `search_repositories()` and `classify_bucket()` for everything that touches RepoScout's own logic.

The rejected-token retry path in `cli.py` had no CLI-level test, so before refactoring it I ran a probe and then added 2 tests: replacement accepted (retried with the new token, message shown once) and replacement rejected (clean exit 1). 57/57 passing.

## 2026-10-17 — HW6 review 4: "errors that disappear"

**Looked for:** `except Exception`, bare `except: pass`, and code that returns `None` or `{}`, or falls back to a default, after something went wrong, across `reposcout/` and `spike/`. There's no `except Exception` or bare `except` anywhere. Every `except` names specific exception types, so the search turned to *fallbacks*: places where a failure quietly becomes a normal-looking value.

**Confirmed by probe through the real CLI (HTTP mocked) before fixing:**
1. **Corrupted config file → the saved token silently disappears.** `auth._load_config()` returned `{}` on any parse or read error. The user was then told "No GitHub token found", and if they pressed Enter, `{"skipped": true}` permanently overwrote the token they thought was saved. A config file holding valid JSON that isn't an object (e.g. `["x"]`) crashed on `.get`. **Fix:** still continue with an empty config, but print a warning to stderr naming the file and the reason. Non-object JSON is treated the same way.
2. **A 200 response without `items` → "0 repos found".** `github.py` read `payload.get("items", [])` and `payload.get("total_count", len(repos))`, so any unexpected success body looked like a real empty search (plus a header-only CSV). This is the slide's example almost exactly. **Fix:** the required fields are read with `[...]`, and a missing or wrong-typed field raises `GitHubAPIError("...response RepoScout doesn't understand...")`, which exits with 1. `item.get("language")` stays, because `null` is GitHub's normal value for "no language detected".
3. **GitHub's `incomplete_results: true` was dropped.** GitHub sets it when its search times out partway through. RepoScout showed the partial results as if complete. **Fix:** `SearchResult.incomplete` → a warning line after the verdict. The flag is stored in the cache entry (old entries without it read as complete), so the warning also appears on cache hits.
4. **A rate limit with no reset headers invented a reset time.** `_parse_reset_time()` fell back to `now`, so the message said "Resets at <right now>". **Fix:** `reset_at` is `None` when unknown, and the message says GitHub didn't say when it resets.

**Checked and deliberately kept:**
- `cache.read_cache()` returning `None` on a corrupted cache file. The `search-cache` spec *requires* this to be silent ("self-heals"). It loses nothing, since the data is just refetched.
- `_handle_error_response()` falling back to an empty detail when an error body isn't JSON. The error is still raised, with the HTTP status.
- The spike script crashes loudly on any error (`raise_for_status()`, `[0]`), which is correct for a one-off measurement.

Specs updated: `github-auth` (config warning; unknown reset time; malformed response counts as an API error) and `repo-search` (new "Incomplete search results are flagged" requirement). Tests: +9, 66/66 passing.

**Seen while probing, for a later review:** `humanize.naturaltime` rounds 16 days to "a month ago" in the verdict line.

## 2026-10-17 — HW6 review 5: "things nobody chose" — dependencies

The three questions from the slide, asked of every package in `pyproject.toml` (6 runtime, 2 dev, plus the `setuptools` build backend).

**1. Does it exist, and is it the real package?** Checked each name against PyPI's JSON API (`https://pypi.org/pypi/<name>/json`): all 9 exist and are the long-established projects their names suggest. Each has years of releases and a source repo under the expected owner: `psf/requests`, `fastapi/typer`, `astanin/python-tabulate`, `python-humanize/humanize`, `tox-dev/platformdirs`, `asweigart/pwinput`, `pytest-dev/pytest`, `getsentry/responses`, `pypa/setuptools`. None is a look-alike name.
- `pwinput` got a closer look: it's the smallest (4 releases), it was added by the agent mid-project (the `getpass` → `pwinput` switch), and it handles the GitHub token. Its author, Al Sweigart (*Automate the Boring Stuff*), is well known. Read the installed source (one 154-line file): it imports only `sys`, `msvcrt` / `tty` + `termios`, and `getpass`, and writes only to `sys.stdout`. No network, files, or subprocesses, so the token goes nowhere but back to RepoScout.

**2. Is it used?** Yes, all 8 non-build packages are imported by our code (`requests` in `github.py` and the spike, `typer` in `cli.py`, `tabulate` + `humanize` in `output.py`, `platformdirs` in `auth.py` + `cache.py`, `pwinput` in `auth.py`, `pytest` + `responses` in `tests/`). Nothing imported is undeclared: every other import is stdlib, `reposcout` itself, or the local `tests/helpers.py`.

**3. Is it pinned to one exact version?** **No** — every entry was `>=` (a minimum only), so a fresh `pip install .` would take whatever was newest that day: an untested version, or a compromised new release. **Fix:** pinned each with `==` to the exact version in the dev `.venv` that the 66 tests pass on: `requests==2.34.2`, `typer==0.27.2`, `tabulate==0.10.0`, `humanize==4.16.0`, `platformdirs==4.11.12`, `pwinput==1.0.3`, `pytest==9.1.1`, `responses==0.26.3`, and the build backend `setuptools==84.0.0`. Verified in a brand-new, throwaway venv: `pip install ".[dev]"` installed exactly those versions, 66/66 tests passed there, and the installed `reposcout --help` command ran.

**Not done, noted:** the packages *our* dependencies pull in (`urllib3`, `certifi`, `idna`, `charset-normalizer`, `rich`, `shellingham`, `colorama`, `markdown-it-py`, `mdurl`, `Pygments`, `annotated-doc`, …) are still chosen by those packages' own version ranges, not by us. Pinning those too means a lock file (ideally with hashes, e.g. via `pip-tools`' `pip-compile --generate-hashes`), which would add a new tool and a new install step. Left as a decision for later rather than slipped in here.

## 2026-10-17 — HW6 review 6: dead code

**Method:** listed every function, class, method, and module-level constant in `reposcout/`, `spike/`, and `tests/helpers.py`, and counted references to each name in app code and in tests separately. Since dead code also hides in fields nobody reads, parameters nobody passes, and files that no longer do anything, those were checked too.

**Only name with zero callers: `cli._main`. Not dead.** It's the empty `@app.callback()` that Typer calls itself. It keeps `search` an explicit subcommand (see the 2026-09-24 implementation entry). Every other name is used by app code, or by tests only where the name is itself a test helper.

**Removed:**
- **`__version__ = "0.1.0"`** in `reposcout/__init__.py`: read by nothing (no `--version` flag, `pyproject.toml` hardcodes its own `version = "0.1.0"`). Worse than unused, because it was a second copy of the version that would silently drift on the next release.
- **`CacheEntry.fetched_at`**: set on every cache read, never read by anyone. The `fetched_at` stored in the cache *file* is still used (the 24h expiry check inside `read_cache()`); only the dataclass field that passed it outward was dead.
- **`bucket_repos(..., now=...)` parameter**: never passed, by app or tests. (`classify_bucket`, `read_cache`, `write_cache`, and `format_verdict` keep their `now` parameters, because tests use them to pin the clock.)
- **`repo_item(..., language=...)` parameter** in `tests/helpers.py`: introduced in review 3 when merging the three copies, but no test passes it, so a dead option I'd just created.
- **`openspec/specs/.gitkeep` and `openspec/changes/archive/.gitkeep`**: placeholders `openspec init` creates so git keeps empty directories. Both directories now hold real content, so the files did nothing. (`openspec validate` / `openspec list` still work.)

**Checked and kept:**
- `if __name__ == "__main__": app()` in `cli.py`: nothing documents `python -m reposcout.cli` (the installed `reposcout` command is the entry point), but it's the standard two lines that make the module runnable directly. Harmless.
- The `token is None` branch in `_fetch_with_token_recovery()` (a 401 with no token sent): GitHub's search shouldn't return that, but it's a 2-line guard on an external API we don't control, and it produces a clean message instead of a confusing re-prompt.
- Exception message strings on `RateLimitExceeded` / `InvalidTokenError` / `NetworkError`: the CLI prints its own messages for these, so the strings aren't shown to users. They still appear in a traceback or a debugger, which is what exception messages are for.

66/66 tests passing, specs validate.

## 2026-10-17 — HW6 review 7: the same feature, built twice under different names

Review 3 merged *copied code* (near-identical functions). This review looked one level up: the same *behaviour or rule* implemented in two places, even where the code doesn't look alike.

**Found and fixed:**
- **The "active" rule, stated twice.** `bucketing.py` defines it as `ACTIVE_THRESHOLD_DAYS = 90`. `output.py` restated it in words, hardcoded, in the verdict: "active in the last 3 months". Evidence: re-ran the HW5 red experiment (threshold → 200) and the verdict read "1 repos found, 1 active in the last 3 months — most recent entrant pushed 5 months ago", contradicting itself. **Fix:** `bucketing.active_window_text()` derives the wording from the threshold ("3 months" for 90, "6 months" for 180, "200 days" when it isn't a whole number of 30-day months), and the verdict uses it. The README/spec demo wording ("active in the last 3 months") is unchanged at today's value. +3 tests.
- **Two README §4 acceptance criteria tested twice.** `tests/test_cli.py` had `test_second_search_within_cache_window_makes_zero_api_calls` and `test_zero_match_search_prints_message_and_writes_headers_only_csv`, which test exactly what `tests/test_acceptance.py` already tests (same CLI invocation, same mocks, same assertions) under different names. Kept the `test_acceptance.py` versions, because they quote the README criterion they encode, and removed the `test_cli.py` copies.

**Two implementations, deliberately both kept (now documented):**
- **Sorting by stars happens twice:** GitHub's `sort=stars&order=desc` in `github.py`, and `rank_by_stars()` locally. They aren't the same job. GitHub's sort decides *which* 50 repos are fetched (it can't be dropped). The local sort owns the *display* order, so the ranks shown always agree with the star counts shown, whatever order the API or an old cache entry returned. Added that explanation to `rank_by_stars()`'s docstring so the next reader doesn't "fix" it.
- **Two error texts per API error** (each exception's own message vs. `auth.rate_limit_message()` / `auth.network_error_message()`): one is for debugging/tracebacks, the other for users. Reviewed in review 6, not repeated here.
- **The spike's own commit fetch** (`spike/pushed_at_drift.py`): calls a different endpoint (`/commits`), and it's frozen HW4 evidence (see review 3).

Test count: 66 − 2 duplicates + 3 new = 67, all passing.

## 2026-10-17 — HW6 review 8: the quiet default

**Looked for:** every `.get(key, default)`, `x or default`, default parameter value, and `os.environ` lookup in `reposcout/`. For each one, asked: is a missing value really allowed here, or is it a bug that the default turns into a decision nobody made?

**Fixed (default → required, so a mistake becomes an error):**
- **`search_repositories(keyword, token=None)`**: a caller that forgot the token silently ran *unauthenticated*, at GitHub's 10-requests-per-minute limit instead of 30, with no sign of why. All app callers passed it, but 5 tests relied on the default without saying so. Now `token` must be passed (still `str | None`: `None` means "deliberately unauthenticated", stated by the caller). The tests now say `token=None` explicitly, and a test checks that omitting it is a `TypeError`.
- **`payload.get("incomplete_results", False)`** and **`item.get("language")`**: GitHub's search schema always sends both keys (`language` is *null* when no language is detected, which stays allowed). A missing key means the response isn't what we think it is, so both are now read with `[...]` and fall into review 4's "response RepoScout doesn't understand" error. Tests: missing key → `GitHubAPIError`; `language: null` → still fine.
- **`incomplete` defaulting to `False` in four places**, all added by me in review 4: `SearchResult.incomplete`, `CacheEntry.incomplete`, `write_cache(..., incomplete=False)`, `_emit_results(..., incomplete=False)`. Each default meant a future caller that forgot the flag would silently report partial results as complete, the exact silence review 4 removed. All four are now required. Also `raw.get("incomplete", False)` when reading the cache: an entry missing the key was *assumed* complete. Now that's a cache miss, so the entry is refetched instead of guessed (costs at most one API call per pre-today entry, and those expire within 24h anyway). +1 test.
- While in the error path: `response.json().get("message", "")` would crash with `AttributeError` if an error body was JSON but not an object (e.g. a list). Now guarded. The message stays optional, since the HTTP status is the actual error. +1 test.

**Checked and kept, because the value really is optional:**
- `os.environ.get("GITHUB_TOKEN")`, `config.get("token")`, `config.get("skipped")`: the spec defines "not set" as a normal state for each.
- `response.headers.get("Retry-After" / "X-RateLimit-Reset" / "X-RateLimit-Remaining")`: GitHub sends these only sometimes. Missing → reset time reported as unknown (review 4), never invented.
- `now = now or datetime.now(timezone.utc)` (4 places): `None` explicitly means "the real clock". Tests pass a fixed time.
- `b.repo.language or missing_language`: a display placeholder for a legitimately null value, and the placeholder is a required keyword argument.
- `prompt_for_token(prompt_text=PROMPT_TEXT)`, `--refresh` defaulting to off: ordinary, intended defaults.
- `timeout=30` in `requests.get`: an explicit value, not a fallback (the opposite of the slide's `timeout=0` example).

73/73 tests passing.

## 2026-10-17 — HW6 review 9: what should not be in git

Checked the **whole history** (all branches, every commit), not just the current tree, because a `git rm` leaves a file in every earlier commit and getting it out means rewriting history (e.g. `git filter-repo`).

**Findings: nothing that shouldn't be there was ever committed, so no history rewrite was needed.**
- **Large / raw data files:** listed every path ever added and the size of every blob in history. The biggest object is `AGENTS.md` itself (~52 KB). Never committed: `.venv/`, `__pycache__/`, `*.egg-info/`, `build/`, the generated `*-report.csv` files (all were already in `.gitignore`), and RepoScout's cache and token config (which by design live outside the repo, in the OS user cache/config dirs via `platformdirs`).
- **Keys / tokens:** searched every diff in history for GitHub token formats (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`, `github_pat_`), other common key shapes (`sk-…`, AWS `AKIA…`, `BEGIN … PRIVATE KEY`), and any `token`/`password`/`secret`/`api_key` assigned a literal. No match for a real key. The only literals are test fakes (`"bad-token"`, `"ghp_abc"`, `"saved-token"`) and the placeholder `ghp_your_token_here` in the manual. The real token the user created for the HW1 smoke test was entered only through the interactive prompt, never typed into a file or this conversation (see the 2026-09-24 entry), and it isn't in history.
- **Real people's data:** no email addresses in any file content. Commit authors use GitHub `noreply` addresses. No personal file paths (`C:\Users\…`, `/home/…`). `spike/pushed_at_drift.csv` contains 50 public GitHub repo names (`owner/repo`) and their public push/commit dates. Kept: it's public metadata, it's the HW4 evidence the grader re-runs, and it holds nothing beyond what github.com shows anyone. `AGENTS.md` mentions the user's possible master's-thesis direction, which is project context the user chose to record, not personal data.

**Fixed, as prevention:** `.gitignore` only covered build output and reports. A `.env`, a private key, or Claude Code's per-user `.claude/settings.local.json` (created when permissions are approved locally) would have been picked up by an ordinary `git add -A`, as used throughout this project. Added `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa*`, `id_ed25519*`, `.claude/settings.local.json`. Verified with `git check-ignore` that these are now ignored, that files which belong in git (`spike/pushed_at_drift.csv`, `openspec/config.yaml`, the shared `.claude/skills/…`) are not, and (`git ls-files -ci --exclude-standard` → empty) that no already-tracked file is newly matched.

## 2026-10-17 (later) — HW6: pushed, PR opened by the user

All 9 reviews done (one commit each, `23a34d4` … `4180892`). Final state: 73/73 tests passing (up from 48), `openspec validate --specs --strict` passes, no active OpenSpec changes.

Pushed `hw6-review` to `origin`. The PR couldn't be opened from this session because the GitHub CLI (`gh`) isn't installed on this machine. The user opens it in the browser (title "HW6: whole-repo review", with a description table summarising the 9 reviews) and merges it themselves with **"Create a merge commit"**, keeping the branch, as with HW4/HW5. (Optional for next time: `winget install GitHub.cli` + `gh auth login` would let the agent open PRs directly.)

**Open issues carried forward (found during the reviews, outside their scope, not fixed):**
- An invalid `GITHUB_TOKEN` env var goes through the *saved*-token recovery: the message says "saved", the replacement is saved to config, but the env var still wins next run, so the user is re-prompted every time.
- `slugify_keyword()` doesn't strip filename-unsafe characters: `reposcout search "c++/qt"` tries to write into a non-existent `c++/` directory and crashes.
- `humanize.naturaltime` rounds 16 days to "a month ago" in the verdict.
- Transitive dependencies (`urllib3`, `rich`, `certifi`, …) aren't locked. That would need a lock file, e.g. `pip-compile --generate-hashes`.
- Still open from HW5: GitHub's loose (non-phrase) keyword matching, and the idea of a friendlier/web interface.

**Next step:** user opens and merges the PR. Then pick from the open issues above.

## 2026-10-25 — Proposed: invalid `GITHUB_TOKEN` env var handling (open issue #1 from HW6)

HW6 PR merged into `main`. New branch `fix-env-token-recovery` from the updated `main`.

Fixing the first carried-forward issue: a rejected token from the `GITHUB_TOKEN` env var went through the *saved*-token recovery (wrong "saved" message, replacement saved to config, env var still wins next run → re-prompted every run). The fix changes specified behaviour, so it goes through a full OpenSpec loop (propose → apply → archive), unlike the earlier no-behaviour-change corrections (rate-limit numbers, "Last Push" rename) that edited the spec directly. No explore step: the only open decision was settled in conversation.

**Decision (user chose option A):** when the rejected token came from `GITHUB_TOKEN`, don't prompt and don't save anything. Print that the token in `GITHUB_TOKEN` is invalid or expired and to update or unset it, then exit `1`. Rejected: B (prompt for a one-run replacement, which would still ask every run until the variable is fixed) and C (make the saved token outrank the env var, which reverses the spec's resolution order, more than this bug needs). Saved-token recovery stays as is.

Ran `/opsx:propose` → change `env-token-invalid-handling` with `proposal.md`, a MODIFIED `github-auth` delta (new scenario on the "Invalid or expired saved token recovery" requirement), `design.md` (`auth.token_from_env()` instead of changing `resolve_token()`'s return type; report via the existing `GitHubAPIError` → exit `1` path), and `tasks.md` (reproduce with a failing test first). `openspec validate --strict` passes. Nothing implemented yet.

**Next step:** `/opsx:apply`.

## 2026-10-25 (later) — Implemented: invalid `GITHUB_TOKEN` env var handling

`/opsx:apply` completed all 6 tasks for `env-token-invalid-handling`.

**Red first:** added `test_rejected_env_var_token_says_fix_the_variable_without_prompting` (`tests/test_cli.py`) and ran it on the unchanged code. It failed for the expected reason: the prompt was invoked (`AssertionError('prompt should not have been invoked')`).

**Fix:** `auth.token_from_env()` + `auth.invalid_env_token_message()`, and one branch in `cli._fetch_with_token_recovery()` that raises `GitHubAPIError` with that message when the rejected token came from the env var (→ exit `1`, no prompt, nothing written to config, one API call). The two existing saved-token recovery CLI tests now clear `GITHUB_TOKEN` so they don't depend on the machine's environment. One paragraph added to `docs/USER_MANUAL.md`.

76/76 tests passing (+3), `openspec validate --strict` passes.

**Next step:** `/opsx:archive` (writes the new scenario into `openspec/specs/github-auth/spec.md`), then push and open a PR.

## 2026-10-25 (later) — Archived: `env-token-invalid-handling`

`/opsx:archive`: all 4 artifacts and 6/6 tasks done. Synced the delta into `openspec/specs/github-auth/spec.md` (the "Invalid or expired saved token recovery" requirement now covers the env-var case, with a new scenario). Verified the main spec's requirement matches the delta exactly, and `openspec validate --specs --strict` passes. Change moved to `openspec/changes/archive/2026-10-25-env-token-invalid-handling/`. No active changes left.

Open issue #1 from the HW6 list is closed. Remaining: #2 `slugify_keyword()` unsafe filename characters, #3 `naturaltime` rounding, #4 transitive-dependency lock file, #5 loose keyword matching, #6 friendlier/web interface.

**Next step:** push `fix-env-token-recovery` and open a PR.

## 2026-10-25 (later) — Proposed: safe CSV filenames (open issue #2)

PR #7 (`fix-env-token-recovery`) merged by the user. New branch `fix-csv-filename-chars` from the updated `main`. Going forward: one branch and one PR per issue, each branched from `main` after the previous PR is merged (both append to `AGENTS.md`, so parallel branches would conflict there).

**Probe on the current code (Windows), before planning:** `csv_filename("c++/qt")` → `c++/qt-report.csv` → `FileNotFoundError` (raw traceback). `csv_filename("c#: tools")` → `c#:-tools-report.csv`, which "succeeds" but leaves only a file named `c#`: the `:` makes NTFS write the CSV into a hidden alternate data stream.

**Decisions (agreed with the user, no explore needed):** (1) unsafe = characters invalid on Windows (`< > : " / \ | ? *`) + control characters; letters (incl. non-ASCII), digits, `+ . _ -` kept. (2) Each run of unsafe characters/whitespace → one hyphen, collapse `--`, trim `-`/`.` at the ends (`"c++/qt"` → `c++-qt-report.csv`). (3) Nothing left (`"???"`) → `search-report.csv`. Silent overwrite on filename collision stays, as the spec already accepts.

Ran `/opsx:propose` → change `safe-csv-filename` (MODIFIED `repo-search` "CSV export" requirement with 3 new scenarios). `openspec validate --strict` passes. Nothing implemented yet.

**New open issue #7 (raised by the user, deliberately not part of #2):** dated or versioned report files, so re-running a search doesn't overwrite the earlier report. The user suggested `v1`/`v2`. Suggested instead: a date stamp (`expense-tracker-report-2026-10-25.csv`), possibly behind an opt-in flag so the README's default `expense-tracker-report.csv` stays. Trade-offs: files pile up in the working directory; it changes spec/README-defined behaviour; re-runs within 24h come from the cache, so a new file would often duplicate the last one. It would also suit the thesis idea (snapshots over time). A good candidate for `/opsx:explore`, since there's a real design question.

**Next step:** `/opsx:apply`.

## 2026-10-25 (later) — Implemented: safe CSV filenames

`/opsx:apply` completed all 5 tasks for `safe-csv-filename`.

**Red first:** a CLI test (`"c++/qt"` → `c++-qt-report.csv` in the working directory, no `c++/` folder) failed with the same `FileNotFoundError` as the probe, and 6 of the 8 new `slugify_keyword()`/`csv_filename()` unit cases failed. The tab and Hungarian cases already passed; they're kept as guards so the fix can't break them.

**Fix:** `slugify_keyword()` in `reposcout/output.py` still builds on `normalize_query()`, then replaces each run of Windows-invalid characters, control characters, and whitespace with one hyphen, collapses `--`, trims `-`/`.` at the ends, and falls back to `"search"`. One sentence added to the CSV paragraph of `docs/USER_MANUAL.md`.

Re-ran the Windows probe: `c++-qt-report.csv`, `c#-tools-report.csv`, `search-report.csv` are all written as normal visible files (no more hidden NTFS stream for `:`). 85/85 tests passing (+9), `openspec validate --strict` passes.

**Next step:** `/opsx:archive`, then push and open a PR.

## 2026-10-25 (later) — Archived: `safe-csv-filename`

`/opsx:archive`: all 4 artifacts and 5/5 tasks done. Synced the delta into `openspec/specs/repo-search/spec.md` (the "CSV export" requirement now states the filename-safety rule and the `search-report.csv` fallback, with 3 new scenarios). Verified the main spec's requirement matches the delta exactly, and `openspec validate --specs --strict` passes. Change moved to `openspec/changes/archive/2026-10-25-safe-csv-filename/`. No active changes left.

Open issue #2 closed. Remaining: #3 `naturaltime` rounding, #4 transitive-dependency lock file, #5 loose keyword matching, #6 friendlier/web interface, #7 dated/versioned report files.

**Next step:** push `fix-csv-filename-chars` and open a PR.

## 2026-10-25 (later) — Proposed: verdict time rounded down (open issue #3)

PR #8 (`fix-csv-filename-chars`) merged by the user. New branch `fix-verdict-time-rounding` from the updated `main`.

**Probe on the current code:** `humanize.naturaltime` rounds to the *nearest* unit, often up: 15 days → "15 days", 16 days → "a month ago", 46 days → "2 months", 89 days → "3 months", 364 days → "a year", and under a day too (119 s → "2 minutes", 23h59m → "a day"). Two consequences beyond inexactness: (a) the verdict can contradict itself, since an 89-day-old repo is *active* and a 100-day-old one isn't, but both print "3 months ago" (so `0 active in the last 3 months — most recent entrant pushed 3 months ago` is possible); (b) the spec/manual example "pushed 2 weeks ago" can't happen, because humanize never says weeks.

**Decision (user chose option A, no explore needed):** always round down, with natural units: "just now" < 1 min, minutes, hours, days < 14 days, weeks < 90 days, 30-day months < 365 days, then years + months. Rejected B: exact days under a year (precise but less natural). Because it never rounds up, an active repo never shows "3 months". Our own ~20-line function replaces humanize (it has no round-down option), so `humanize` is removed from the dependencies.

Ran `/opsx:propose` → change `verdict-time-round-down` (MODIFIED `repo-search` "One-line verdict summary" requirement, 3 new scenarios). `openspec validate --strict` passes. Nothing implemented yet.

Side question from the user, answered in conversation: subagents can be used as small "teams" (each reports back to the main agent; they don't freely discuss). Most useful here: a fresh reviewer agent for a finished change, a spec-only test writer, parallel research on independent questions (e.g. #4 and #5), a devil's advocate during explore (#7). Not worth it for small, clear fixes.

**Next step:** `/opsx:apply`.

## 2026-10-25 (later) — Independent review of the plan, then implemented: verdict time rounded down

**First use of a reviewer subagent.** At the user's request, before applying, a fresh general-purpose agent (no access to this conversation, read-only) reviewed the `verdict-time-round-down` plan and searched the repo for anything else the change must touch. It found no blocking problems and verified every expected value in `tasks.md` by hand. Its findings, all folded into the plan before applying (commit `061fc67`):
- The spec said "years plus any remaining whole months" while design/tasks capped the months at 11 → spec now says "(at most 11)", with a new 729-day scenario.
- `format_verdict()` already had a local variable named `time_ago`, which would shadow the new function (`UnboundLocalError`) → renamed to `pushed_ago`.
- The proposal didn't mention the smaller wording changes ("a day ago" → "1 day ago"; 14–15 days → "2 weeks ago") → added.
- Missing boundary tests (plurals for minutes/hours, flooring inside an hour, a 395-day month boundary, −1 s, 13 d 23 h) → added. The 400-day case already passed under humanize, so it's noted as a guard, not evidence.
- Singular forms and the clock-skew → "just now" rule were only in design.md → added to the spec.
- Outside the plan: the gitignored `reposcout.egg-info/` still listed humanize, and a stale gitignored `build/` copy still imported it → refreshed with `pip install -e ".[dev]"` and removed `build/`.

**Implementation (`/opsx:apply`, 6/6 tasks):** red first. The 16- and 89-day verdict tests failed on the old code ("a month ago" / "3 months ago"; 100 days already read "3 months ago" and stays as a guard), and the boundary tests failed at import. Added `time_ago()` (+ a `_count()` singular/plural helper) in `reposcout/output.py`, removed `humanize` from `output.py` and `pyproject.toml`, and added one note to `docs/USER_MANUAL.md`. A whole-repo grep finds `humanize` only in this change's planning docs. The installed `reposcout --help` works. 115/115 tests passing (+30), `openspec validate --strict` passes.

**Next step:** `/opsx:archive`, then push and open a PR.

## 2026-10-25 (later) — Archived: `verdict-time-round-down`

`/opsx:archive`: all 4 artifacts and 6/6 tasks done. Synced the delta into `openspec/specs/repo-search/spec.md` (the "One-line verdict summary" requirement now states the round-down rule, singular forms, and clock skew → "just now", with 4 new scenarios). Verified the main spec's requirement matches the delta exactly, and `openspec validate --specs --strict` passes. Change moved to `openspec/changes/archive/2026-10-25-verdict-time-round-down/`. No active changes left.

Open issue #3 closed. Remaining: #4 transitive-dependency lock file, #5 loose keyword matching, #6 friendlier/web interface, #7 dated/versioned report files.

**Next step:** push `fix-verdict-time-rounding` and open a PR.

## 2026-10-25 (later) — Decision: open issue #4 (lock file) deferred

PR #9 (`fix-verdict-time-rounding`) merged by the user. New branch `fix-keyword-matching` from the updated `main`.

Discussed #4 (indirect dependencies aren't locked) with the user. The direct dependencies are pinned with `==`, but they declare ranges for their own dependencies (e.g. `requests` → `urllib3>=1.26,<3`, `certifi>=2023.5.7`; `typer` → `rich>=13.8.0`), so a fresh install takes the newest allowed versions on that day (today's `.venv`: `urllib3 2.8.0`, `certifi 2026.7.22`, `rich 15.0.0`, not recorded anywhere). A lock file (`pip-compile --generate-hashes` from `pip-tools`) would pin every package with hashes. Only the developer needs `pip-tools`; users would run plain `pip install -r requirements.lock`. That makes the environment match the lock exactly (downgrading e.g. a newer `rich`), which is fine in a project-specific venv but intrusive in a system-wide Python.

**Decision (user): deferred.** Benefit small for a project this size (direct deps pinned; indirect ones are large, well-maintained packages) vs. a new tool, an extra install step, and a file to regenerate on every update. Ranked below #5 and #7, which change what users actually see. Stays on the open-issues list. The user also asked whether an agent could help decide. Not needed here, since the answer was already clear; debate-style agents are better spent on #5/#7.

Remaining open issues: #4 (deferred), #5 loose keyword matching (next, starting with `/opsx:explore`), #6 friendlier/web interface, #7 dated/versioned report files.

## 2026-10-25 (later) — Explore + propose: search by relevance (open issue #5)

**Clarification from the user (important for future sessions):** RepoScout is a class project, not thesis work. The 2026-09-24 entry's note about a *possible future* thesis use was over-weighted in this session's reasoning (it was cited as a reason for decisions). Don't treat it as a goal or a constraint.

**Explore findings (live GitHub probes via PowerShell; Python `requests` in the agent's sandbox fails TLS verification, likely the sandbox proxy):**
- GitHub repo search matches when every word appears *somewhere* in name/description/topics: any order, any distance, word forms too ("activities" for "activity"). It is **not** phrase matching.
- `"repo activity research"` (exact phrase) → **0** results; `"expense tracker"` → 232,773 vs 244,832 without quotes, identical top 5. So phrase-by-default fails on the motivating case.
- The junk repos (`molyswu/hand_detection`, a TensorFlow hand detector; `hackcrypto/fluxion`, a Wi-Fi phishing tool) pasted their whole README into the description, so the three words appear thousands of words apart.
- Root cause: `sort=stars` picks the most-starred loose matches. Without `sort`, GitHub's relevance ("best match") ranking applies: for "repo activity research" (80 matches) **none of the five junk repos from the HW5 run is in the relevance top 50**; for "expense tracker" the relevance top results are all real expense trackers.
- Quotes and qualifiers (`language:python`) already work today, since the keyword is passed through unchanged; they're just undocumented.

**Decisions (user):** default = the 50 most on-topic matches (GitHub relevance), displayed ranked by stars ("most-on-topic matches by default and among those the most popular ones"). No exact phrase by default. No `--by-stars` flag for now. More-than-50 verdict wording becomes "Showing the 50 best-matching of N repos, …". The manual gets a tip on quotes/qualifiers. README left unchanged (original course spec).

Ran `/opsx:propose` → change `search-by-relevance`: MODIFIED `repo-search` ("Keyword search against GitHub", "One-line verdict summary") and `search-cache` ("Cache hit avoids GitHub API calls": entries without `"selection": "best-match"` are a miss, so no star-picked results are served after the update). Design: omit `sort`/`order` (the documented default) rather than send an undocumented `sort=best-match`. `openspec validate --strict` passes. Nothing implemented yet.

**Next step:** `/opsx:apply`. Task 3.4 is a live smoke test the user runs in their own terminal.

## 2026-10-25 (later) — Implemented: search by relevance (11/12 tasks, live smoke test pending)

`/opsx:apply` for `search-by-relevance`. **Red first:** the request-params test (no `sort`/`order`), the new verdict wording, and the old-format cache entry → miss all failed on the old code. The display-order guard (GitHub returns 5/300/40 stars → table shows 300, 40, 5) already passed, confirming `rank_by_stars()` owns the display order.

**Implementation:** `github.py` drops `sort`/`order` (GitHub's documented default is best match); `cache.py` writes `"selection": "best-match"` and treats entries without it as a miss; `output.py`'s more-than-50 verdict says "Showing the 50 best-matching of N repos"; `bucketing.py`'s `rank_by_stars()` docstring updated. Found during implementation: the new `raw.get(...)` check would raise `AttributeError` on a cache file holding non-object JSON (previously a caught `TypeError`), breaking the "corrupted cache self-heals" spec. Added `AttributeError` to the caught exceptions, plus a test.

**User manual:** fetch description, verdict example, and a tip on exact phrases / qualifiers. The exact-phrase quoting was **verified per shell** before documenting, because the first draft was wrong: in Windows PowerShell 5.1, `'"expense tracker"'` loses the quotes and `'\"expense tracker\"'` splits into two arguments. Working forms: bash/zsh/Git Bash `'"expense tracker"'`; PowerShell `--% "\"expense tracker\""`; Command Prompt `"\"expense tracker\""`.

119/119 tests passing (+4), `openspec validate --strict` passes. A grep finds no remaining claims that the 50 are chosen by stars outside the main spec lines the archive step will replace.

**Pending:** task 3.4, a live smoke test the user runs in their own terminal (the agent's Python can't verify GitHub's TLS certificate in its sandbox).

## 2026-10-25 (later) — Live smoke test passed: search by relevance (12/12 tasks)

The user ran `.\.venv\Scripts\reposcout search "repo activity research" --refresh` in their own PowerShell (first attempt without the leading `.\` failed: PowerShell treats `.venv\...` as a module name; explained). Result: `Showing the 50 best-matching of 80 repos, 14 active among them — most recent entrant pushed 1 day ago`.
- None of the five HW5 junk repos (`molyswu/hand_detection`, `hackcrypto/fluxion`, `82goober82/fluxionwpacrack`, `Sfedfcv/redesigned-pancake`, `ManojKumarPatnaik/Major-project-list`) appears.
- Stars column descending (13, 7, 6, 5, 2, 1…, then 0s); 14 `active` rows match the verdict; newest push 2026-10-24 → "1 day ago" is correct.
- Honest limit, noted to the user: results now have the words close together (e.g. `human-walking-activities`, `my_research_activity`), but keyword search still can't tell meanings apart (e.g. `Sportswear_Market_to_Reach_Research_Report`). Exact phrases and qualifiers (documented in the manual) are the remaining tools.

Task 3.4 done; 12/12. **Next step:** `/opsx:archive`, then push and open a PR.

## 2026-10-25 (later) — Archived: `search-by-relevance`

`/opsx:archive`: all 4 artifacts and 12/12 tasks done. Synced 3 MODIFIED requirements into the main specs: `repo-search` "Keyword search against GitHub" (50 best-matching by GitHub relevance; keyword passed through unchanged) and "One-line verdict summary" (best-matching wording), and `search-cache` "Cache hit avoids GitHub API calls" (entries without the relevance-selection marker aren't served). Verified each matches its delta exactly, requirement counts unchanged (6 and 5), and `openspec validate --specs --strict` passes. Change moved to `openspec/changes/archive/2026-10-25-search-by-relevance/`. No active changes left.

Side note from the user's live run: a third-party repo `ly5566lyui/repo-scout` appeared in the results. Checked it out of curiosity: an AI "Agent Skill" (`SKILL.md`, no program code) that researches one given repo in depth. Same name, different problem (RepoScout scans many repos by keyword); complementary, not overlapping.

Open issue #5 closed. Remaining: #4 lock file (deferred), #6 friendlier/web interface, #7 dated/versioned report files.

**Next step:** push `fix-keyword-matching` and open a PR.

## 2026-10-25 (later) — Session 7 halftime: website UI explored, gstack installed, design approved

PR #10 (`fix-keyword-matching`) merged by the user. New branch `website-ui` from the updated `main`.

**Context (session 7 slides, 20 Oct):** halftime, "if you're done, make it bigger"; the project is the homework until the demos (1 and 8 Dec). HW7 (what moved forward, linked commits, + one question) and HW8 (re-read README §1 "The demo", update it via `propose` if it no longer fits) are both due 7 Nov; slides in the repo by 28 Nov. Course rules: plan with OpenSpec `propose`, a thin end-to-end path first, `main` never broken. The user later clarified the demo format: **a five-minute presentation with screenshots, not a live run.**

**Tools:** the user asked to install gstack (the slides recommend it). Installed globally only (not in the repo, no team mode): Bun 1.4.4 via `npm install -g bun`, gstack v1.91.216.0 cloned to `~/.claude/skills/gstack` (the sandbox's git needed `-c http.sslBackend=schannel`; `setup.ps1` reported a spurious PowerShell 5.1 stderr "error", but `./setup --status` and `gstack-doctor` confirmed 11 ok / 0 fail). Added the README's gstack section to the user's *global* `~/.claude/CLAUDE.md`. The user asked whether gstack is needed. Answer: not strictly (OpenSpec + agent cover planning/review); the useful pieces for this project are `/office-hours` (once) and `/qa` (drives a real browser) later. The user kept it for other projects. Impeccable not installed.

**Explore + `/office-hours` (builder mode, goal: class demo):**
- GitHub Pages hosts static files only; GitHub's search API allows browser calls (`Access-Control-Allow-Origin: *`; `Retry-After` and `X-RateLimit-*` exposed). Verified live.
- Ideas: the "heartbeat strip" (every repo a dot on a last-push axis, size = stars, shade = bucket) was chosen as the hero. Topic-vs-topic is a later "could".
- First direction (classmates on phones → prebaked JSON via a nightly GitHub Action + live box) was **dropped** when the user checked the assignment: the demo is screenshots.
- **Decision (user, D2): a static HTML+JS page in `site/`, run on localhost (`python -m http.server`), Pages-ready later; tokenless on the web; the CLI keeps its token.** Rejected: a Flask/FastAPI app (GitHub Pages can't run Python, so publishing later would mean a rewrite).
- Wireframe approved (title, search, verdict, heartbeat strip, table + CSV, state messages). It was first "approved" without the user seeing it (the image only rendered on the agent's side), so it was opened in their browser and re-confirmed.
- An independent second-opinion subagent flagged: the course org repo may not allow Pages/Actions; JS/Python rule drift (needs one shared test fixture); explain "Last Push" on the page. Rejected its "hollow dots for unreliable pushed_at" idea (the HW4 spike gives a rate, not which repos).
- gstack's adversarial spec review: round 1 = 7/10 with 5 blocking (dropped `incomplete_results`; only one rate-limit kind; linear time axis would shrink the 90-day zone to ~2%; CDN failure; Pages can't serve `site/` via the settings switch). All fixed (piecewise axis by bucket, vendored Plot+d3, CLI's rate-limit rule, incomplete warning + cache flag, publish via `docs/` move or a Pages workflow). Round 2 = PASS, 8/10, 10 minor points left for the OpenSpec tasks.
- Design doc **APPROVED**: `docs/designs/reposcout-website.md`.

**Next step:** `/opsx:propose` (includes the README §1 rewrite for HW8).

## 2026-10-25 (later) — Proposed: website-heartbeat-ui

Phone-width usability added to the approved design doc as a "should" (user decision, after asking whether the site would look good on phones: it wouldn't have by default, since the requirement had dropped out when the demo became screenshots).

Ran `/opsx:propose` → change `website-heartbeat-ui` with a **new capability `web-ui`** (9 requirements: static tokenless page; same selection/ranking as the CLI; verdict wording; heartbeat strip with piecewise axis + fallback; table + CSV; states incl. rate-limit rules and incomplete warning; browser cache; rules parity via a shared fixture; usable at 360 px). No existing capability is modified; the CLI is untouched. The 10 minor spec-review points from office hours are folded into the spec, design and tasks (rate-limit only on non-OK responses, Distribution wording, piecewise axis as a precomputed 0-3 position with custom ticks, dodge + capped sqrt radius, fuller fixture incl. normalization/slug/CSV, parity via recorded inputs, the exact test command `pytest && node --test tests/js/`, input handling, "two implementations, one shared test fixture"). 30 tasks in 8 groups, thin path (keyword → verdict on screen) first. `openspec validate --strict` passes.

**Next step:** `/opsx:apply`. Live checks (tasks 1.3, 4.4) are run by the user in their own browser.

## 2026-10-25 (later) — gstack /plan-ceo-review on website-heartbeat-ui (SCOPE REDUCTION)

The user ran gstack `/plan-ceo-review` (asked earlier whether 30 tasks was too much; the real count was 22, I had misreported it). Telemetry for gstack set to "community" at the user's choice.

Mode chosen: **SCOPE REDUCTION** (~17 files). Decisions (all by the user, one question each):
- R1: README §1 rewrite moved to task 1.4 (right after the thin path) so HW8 doesn't depend on the chart work.
- R2: browser cache **kept**. R7: phone width **kept**. R8: gstack `/qa` pass **kept**.
- R6: live rate-limit countdown replaced by a static "try again after HH:MM:SS" message (no timer).
- R3: "unexpected response" state for a garbage 200 (e.g. captive-portal HTML). R9: plus item-level checks like the CLI (`github.py:124-136`).
- R4: GitHub text and the keyword always inserted as plain text (`textContent`, never `innerHTML`).
- R5: latest search wins (an older, slower response can't overwrite newer results).

Outside voice: Codex not installed, so a native Plan subagent (5-minute bound) reviewed the plan: 12 findings. Verified before acting: the plan stated the CLI's rate-limit rule three different ways (any 429; 403 with Remaining 0 or Retry-After); `&&` is a parse error in PowerShell 5.1 and `node --test tests/js/` fails on Node 24 (the glob `"tests/js/*.test.mjs"` works); `.js` maps to `text/javascript` on this machine (check kept anyway). Nine findings applied as corrections (exact CLI rate-limit rule + fixture cases, two separate test commands, MIME check, UTC `Last Push` date, chart can't take the table down, `tip` mark tooltips, frozen fixture, verdict wording, push checkpoints for HW7 + graveyard keyword choice, normalization parity limited to fixture cases); three were scope questions (R6-R8) and one behaviour (R9).

Result: 24 tasks, 9 requirements, 19 scenarios; `openspec validate --strict` passes. Review report: CEO CLEAR, 0 critical gaps, 0 unresolved; gstack notes "eng review required" (its default gate). Report saved in `~/.gstack/projects/esst-prog2-RepoScout/ceo-plans/2026-10-25-website-heartbeat-ui-ceo-review.md`.

**Next step:** `/opsx:apply` (optionally gstack `/plan-eng-review` first).

## 2026-10-25 (later) — Implemented: website-heartbeat-ui (22/24 tasks)

The user skipped gstack's `/plan-eng-review` (rejected the target prompt) and ran `/opsx:apply`.

**Built:** `site/` = `index.html`, `style.css`, `app.js` (DOM, fetch, browser cache, chart), `rules.js` (pure rules ported from the CLI), vendored **d3 7.9.0** + **Observable Plot 0.6.17** with licences (ISC). Shared fixture `tests/fixtures/rules.json` (values computed once from the real Python functions, then frozen; the computing script stayed in the scratchpad), checked by `tests/test_rules_fixture.py` (Python CLI, incl. `_is_rate_limited`/`_parse_reset_time` and payload validation via `responses`) and `tests/js/rules.test.mjs` (site/rules.js). **175 pytest + 63 node tests passing.** Drift check: threshold changed in JS only → 5 JS failures; in Python only → 3 Python failures; reverted, never committed.

**Verified in a real (headless) browser** via gstack `browse` with `tests/browser/harness.html` (recorded GitHub answers per `?case=`): ranking by stars, `-` for no language, `<img onerror>` repo name shown as text (no alert), every state (zero, incomplete, both rate-limit forms, 422, HTML 200, `pushed_at: null`, offline), latest-search-wins race, spaces-only input blocked, cache (no second request; normalized key), storage blocked, chart fallback, CSV download (`c++-qt-report.csv`, CRLF, no BOM), 360 px (no sideways scroll, optional columns hidden).

**Found and fixed while building:**
- Zone labels overlapped at phone width → short labels on narrow screens.
- **The harness polluted the real page's cache** (same address → the real page showed the harness's fake "5 repos found"). Harness now uses in-memory storage.
- With live data, `Plot.dodgeY` stacked 30-40 dots in one column and spilled out of the chart → replaced by a fixed vertical spread inside the frame (design.md updated).
- A `text/plain` Content-Type reading for `.js` came from the headless browser's tooling, not the server: `curl` and Python's mimetypes both give `text/javascript`, so no `serve.py` was needed.

**Live (gstack's browser can reach GitHub from the sandbox):** "expense tracker" → 50 of 245015, 4 active; graveyard keyword **"angularjs directive"** (0 active, 48 stale); alive keyword **"mcp server"** (37 active, pushed minutes ago). Three demo screenshots in `docs/screenshots/`. README §1 (HW8) rewritten for the website; USER_MANUAL gets a "Website" section. Branch `website-ui` pushed (HW7 checkpoint).

**Remaining:** 1.3 (user's own live walk-through in their browser) and 8.2 (gstack `/qa` pass).
