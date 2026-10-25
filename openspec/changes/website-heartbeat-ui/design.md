# Design

## Context

The approved design doc (`docs/designs/reposcout-website.md`, including its spec-review findings) is the source for this change; see proposal.md for why. Relevant facts from the codebase and live checks:
- The rules to mirror live in `reposcout/bucketing.py` (`ACTIVE_THRESHOLD_DAYS = 90`, `STALE_THRESHOLD_DAYS = 365`, `active_window_text()`), `reposcout/output.py` (`format_verdict`, `time_ago`, `slugify_keyword`, `csv_filename`, `_row`, `CSV_HEADERS`; `Last Push` is `pushed_at.date().isoformat()`, missing language is `"-"` in the table and `""` in the CSV; the CSV uses Python's `csv` module, so CRLF line endings and minimal quoting) and `reposcout/cache.py` (`normalize_query`: trim, collapse whitespace, `casefold()`).
- GitHub's search API answers browsers with `Access-Control-Allow-Origin: *` and exposes `Retry-After`, `X-RateLimit-Remaining` and `X-RateLimit-Reset` (probed 2026-10-25).
- Node.js v24 is installed; Python's `http.server` is available with no extra dependency.
- In the agent's sandbox, Python/Git TLS to GitHub fails (proxy); live checks go through PowerShell or the user's own terminal and browser.

## Goals / Non-Goals

**Goals:**
- A page that produces three clean demo screenshots: an alive topic, a graveyard topic, the table/CSV.
- No silent drift between the Python and JavaScript rules.
- `main` stays working: the CLI and its 119 tests are untouched.

**Non-Goals:**
- Publishing on GitHub Pages in this change.
- Topic-vs-topic, theming beyond a clean default, a service worker, any backend or token.
- Making the CLI read the fixture at runtime (the fixture is test data only).

## Decisions

**File split: pure rules vs. page code.** `site/rules.js` is an ES module of pure functions with no DOM access (`bucketFor`, `timeAgo`, `activeWindowText`, `formatVerdict`, `normalizeQuery`, `slugifyKeyword`, `csvFilename`, `csvRows`, `xPosition`, `isRateLimited`, `resetSeconds`), each taking "now" as a parameter. `site/app.js` handles the DOM, `fetch`, cache and chart, and imports `rules.js`. This lets `node --test` exercise every rule without a browser. Alternative considered: a single `app.js`. Rejected, because the rules would then only be testable through a browser.

**Module loading.** The browser loads `app.js` with `<script type="module">`, which requires an HTTP server (not `file://`); `python -m http.server` covers that and is what the docs say. Node imports `site/rules.js` directly. Node 24 detects ES module syntax in a `.js` file without a `package.json`; task 1.1 verifies this first, and the fallback is a one-line `site/package.json` with `{"type": "module"}`.

**Chart: Observable Plot + d3, vendored.** The UMD builds (`d3.min.js`, `plot.umd.min.js`) are downloaded once at exact versions into `site/vendor/` with their licence files, and loaded as classic `<script>` tags before `app.js`, which exposes the globals `d3` and `Plot`. `app.js` checks `typeof Plot` and falls back to the "chart unavailable" note. Alternatives: CDN (rejected: fails offline, flagged by spec review R1-4) and a hand-written SVG (rejected: tooltips, dodging and responsive sizing come free with Plot).

**Piecewise x-axis as a precomputed position.** Plot has no scale with different units per segment, so `rules.xPosition(days)` maps days since last push to 0-3: stale 365d-5y maps to 0-1 (older than 5 years is clamped to 0), slowing 90-365 days to 1-2, active 0-90 days to 2-3, each linear inside its zone (equal thirds). The chart uses `x` = that position with domain [0, 3], custom ticks at 0, 1, 2, 3 labelled "5+ years", "1 year", "90 days", "now", and three background rects for the zones. Dots use `Plot.dodgeY` (vertical separation) and Plot's default square-root `r` scale for stars, with a max radius cap. This addresses spec-review findings R1-3, R2-4 and R2-9.

**Keyword normalization in JS.** Python's `casefold()` has no exact JS equivalent. `normalizeQuery` uses `trim()`, collapses `\s+` to one space, then `toLowerCase()` plus `ß` → `ss` (the case-folding difference relevant to European keywords). The fixture covers ASCII, Hungarian (`költség`) and `Straße`; other exotic case-folds may differ, which is acceptable because the key only affects the browser's own cache and filenames.

**CSV built in the browser to match Python's `csv` module.** CRLF line endings; a field is wrapped in double quotes only if it contains a comma, a double quote, CR or LF, with inner quotes doubled; UTF-8 without BOM; download via a `Blob` and a temporary `<a download>`. The fixture holds expected CSV text for a repo name with a comma and a repo with no language.

**Rate-limit detection only on non-OK responses** (spec-review R2-1). `isRateLimited(status, headers)` is true for (status 403 or 429) and (`X-RateLimit-Remaining` = "0" or a `Retry-After` header present), mirroring `github.py`'s `_is_rate_limited`. `resetSeconds` prefers `Retry-After`, then `X-RateLimit-Reset` minus now, otherwise `null` (meaning no countdown is shown). A 200 is always rendered as results.

**Browser cache entry** `{v: 1, fetched_at, total_count, incomplete, repos: [{name, url, stars, pushed_at, language}]}` under `reposcout:<normalized key>`; an entry missing `incomplete` or older than 24h is a miss; every `localStorage` access is wrapped in `try/catch`.

**Shared fixture, two runners** (spec-review R2-5..R2-7, R2-10). `tests/fixtures/rules.json` holds inputs and expected outputs plus a fixed `now`. `tests/test_rules_fixture.py` runs them through the real Python functions; `tests/js/rules.test.mjs` runs them through `site/rules.js` with `node:test`. The thresholds are *not* read from the fixture at runtime by either side: two implementations, one shared test fixture. The documented full test command is `pytest && node --test tests/js/`.

## Risks / Trade-offs

- [Risk] Live GitHub behaviour can't be exercised in the agent's sandbox. → Unit tests use recorded responses; the user runs the live smoke test in their own browser, as for earlier changes.
- [Risk] Vendored minified libraries are third-party code in the repo. → Exact versions, licence files kept, downloaded from the official npm packages via jsDelivr, nothing executed at download time.
- [Trade-off] Rules exist twice. → Guarded by the shared fixture in both test runs; accepted to keep the page Pages-ready without a server.
- [Risk] The piecewise axis may still look crowded for some topics. → Checked against a real "expense tracker" result during implementation (task 4.4) before it's final.

## Open Questions

- GitHub Pages / Actions availability in the `esst-prog2` org: only relevant when publishing later; doesn't change this change's specs or tasks.
