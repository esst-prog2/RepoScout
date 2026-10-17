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
