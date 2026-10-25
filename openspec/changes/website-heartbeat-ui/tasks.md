# Tasks

## 1. Thin path first: keyword in, verdict on screen

- [ ] 1.1 Verify Node 24 can `import` an ES-module `.js` file without a `package.json` (a throwaway check in the scratchpad); if not, plan the one-line `site/package.json` `{"type": "module"}` fallback. Also confirm the test command form `node --test "tests/js/*.test.mjs"` (Node 24 rejects a bare folder). Verify by the check's output.
- [ ] 1.2 Create `site/index.html` (title, one-line promise, search form, verdict area), `site/style.css` (minimal), `site/app.js` (form submit → `fetch` GitHub search with `per_page=50`, no `sort`, `encodeURIComponent` → verdict text), and `site/rules.js` with `bucketFor`, `timeAgo`, `activeWindowText`, `formatVerdict` ported from `bucketing.py`/`output.py`. Verify by serving `site/` with `python -m http.server` and loading the page without console errors, and check in the browser's Network tab that `.js` files arrive as `text/javascript` (Windows can map `.js` to `text/plain` via the registry; fallback: a few-line `site/serve.py` forcing the type).
- [ ] 1.3 Live walk-through of the thin path (run by the user in their own browser, since the agent sandbox can't reach GitHub from Python): search "expense tracker" and see a verdict line. Verify by the user's report.
- [ ] 1.4 Rewrite README §1 "The demo" for the website demo (open the page, search a topic, read the verdict, point at the heartbeat strip, show the table and CSV), keeping the CLI as the tool underneath. Done here, right after the thin path, so HW8 (due 7 Nov) doesn't depend on the rest of the build; touch it up at the end if the page changes. Verify by reading it against the planned page.
- [ ] 1.5 Push checkpoint for HW7 (due 7 Nov; "what is not pushed does not exist"): commit and push the `website-ui` branch after 1.4, and again after group 2. Verify the commits are visible on GitHub.

## 2. Shared rules fixture (two implementations, one fixture)

- [ ] 2.1 Create `tests/fixtures/rules.json` with a fixed `now` and cases for: buckets at 89/90/364/365 days; verdict for total > fetched, total ≤ fetched, zero, and incomplete (30 fetched of 60 reported); `time_ago` across every unit (just now, minutes, hours, days, 14 days → 2 weeks, 89 → 12 weeks, 90 → 3 months, 365 → 1 year, 729 → 1 year 11 months); normalization (`"  Expense   Tracker "`, `költség követő`, `Straße`); slug/filename (`c++/qt`, `c#: tools`, `???`); CSV text for a name containing a comma, a repo with no language, and a `pushed_at` of `…T23:30:00Z` (UTC date, not local); rate-limit cases (429 with no headers → limited; 403 with remaining 0 → limited; 403 with `Retry-After` → limited; 422 with remaining 0 → not limited; 200 with remaining 0 → not limited; non-numeric `Retry-After` → falls back to `X-RateLimit-Reset`). Expected values are checked once against the current Python output and then frozen as hand-maintained reference data (no generator script committed). Verify the JSON parses.
- [ ] 2.2 Add `tests/test_rules_fixture.py` running every fixture case through the real Python functions (`classify_bucket`, `format_verdict`, `time_ago`, `normalize_query`, `slugify_keyword`, `csv_filename`, the CSV writer, and `github._is_rate_limited`/`_parse_reset_time` via `requests.Response` objects built from the fixture). Verify `pytest` passes (119 existing + new).
- [ ] 2.3 Add `tests/js/rules.test.mjs` (`node:test`, no npm packages) running the same cases through `site/rules.js`; extend `rules.js` with `normalizeQuery`, `slugifyKeyword`, `csvFilename`, `csvRows` as needed. Verify `node --test "tests/js/*.test.mjs"` passes.
- [ ] 2.4 Drift check: temporarily change the active threshold in `site/rules.js` only, confirm the JS fixture test fails, revert; do the same in `reposcout/bucketing.py` and confirm the Python fixture test fails, revert. Never commit the broken values. Verify by the two failing runs and the green runs after reverting.

## 3. Results table and CSV

- [ ] 3.1 Render the ranked table (CLI columns, `-` for no language, `Last Push` as a date), sorted by stars descending regardless of GitHub's order. Insert all GitHub-supplied text and the keyword with `textContent`/DOM APIs, never `innerHTML`. Verify with a recorded response in the browser (stars 5/300/40 → 300/40/5), including a repo named `<img src=x onerror=alert(1)>` that must show as plain text with no alert.
- [ ] 3.2 Add the Download CSV button using `csvRows`/`csvFilename` (CRLF, minimal quoting, UTF-8 without BOM, `<slug>-report.csv`). Verify by downloading for `c++/qt` → `c++-qt-report.csv`, opening it, and comparing it with the CLI's CSV for the same recorded data.

## 4. Heartbeat strip

- [ ] 4.1 Vendor `d3` and `@observablehq/plot` UMD builds at exact versions into `site/vendor/` with their licence files (download via PowerShell from jsDelivr's npm mirror); load them as classic scripts before `app.js`. Verify the files exist and `Plot`/`d3` are defined in the page.
- [ ] 4.2 Add `xPosition(days)` to `rules.js` (equal-thirds piecewise mapping, clamp at 5+ years) with fixture cases (0, 45, 90, 200, 365, 1000, 3000 days). Verify both fixture test runs pass.
- [ ] 4.3 Draw the strip: zone backgrounds and labels, custom ticks ("5+ years", "1 year", "90 days", "now"), `Plot.dodgeY` dots with a capped square-root radius by stars, shade by bucket, tooltip via Plot's `tip` mark (hover and tap) with name/stars/last push, the one-line "Last push = GitHub's pushed_at" note, and the "chart unavailable" fallback (verdict and table drawn first; chart only if `d3` and `Plot` exist, wrapped in try/catch). Verify the fallback by temporarily renaming the vendor file.
- [ ] 4.4 Check the strip against a real "expense tracker" result (user's browser) and pick and record the "graveyard" keyword for screenshot 8.3 (a topic whose dots cluster in the stale zone); adjust the radius cap or height if dots are unreadable. Verify by the user's screenshot or report.

## 5. States and browser cache

- [ ] 5.1 Implement `isRateLimited` and `resetSeconds` in `rules.js` copying `github.py` exactly (non-OK only; any 429; 403 with remaining 0 or `Retry-After`; numeric `Retry-After` first, then `X-RateLimit-Reset`, else no countdown), using the rate-limit fixture cases from 2.1. Verify both fixture test runs pass.
- [ ] 5.2 Wire every state into `app.js`: loading; empty/whitespace input blocked; zero results; incomplete-results warning; rate-limited static message "try again after HH:MM:SS" (no timer, no auto-retry) or "no reset time given"; offline ("Could not reach GitHub"); other errors naming the HTTP status (e.g. 422); unexpected response (a 200 that isn't JSON, lacks `total_count`/`items`/`incomplete_results`, or has an item missing `full_name`/`html_url`/`stargazers_count`/`pushed_at`/the `language` key or with an unreadable `pushed_at`, shows "GitHub sent a response RepoScout doesn't understand"; item check as in `github.py:124-136`, including a recorded item with `pushed_at: null`). Latest search wins: each search gets an increasing id and only the latest id may render (Scout stays enabled). Verify each state, including a recorded HTML-body 200 and a controlled slow-`react`-then-fast-`vue` pair where the late `react` answer must not render, with a recorded/forced response in the browser.
- [ ] 5.3 Add the `localStorage` cache (24h, `reposcout:<normalized key>`, stores `incomplete`, entries without it are a miss, every access in `try/catch`). Verify: a repeat search makes no request (browser network tab), and the page still works with storage blocked.

## 6. Phone width

- [ ] 6.1 Add responsive CSS: stacked layout under ~600 px, the table scrolls inside its own box (or hides `Language`/`Last Push`), a taller strip on narrow screens, no horizontal page scroll at 360 px. Verify at 360 px width (browser device mode, or gstack `/qa` at a phone viewport).

## 7. Docs

- [ ] 7.1 Re-read README §1 (written in task 1.4) against the finished page and correct anything that changed. Verify by reading it against the actual page.
- [ ] 7.2 Add a "Website" section to `docs/USER_MANUAL.md`: how to start it (`cd site`, `python -m http.server`, open `http://localhost:8000`), that it needs no token (10 searches/minute limit; when reached, the page says when to try again), what the strip shows, and the two test commands `pytest` and `node --test "tests/js/*.test.mjs"` (run separately; both must pass). Verify by following the steps from a fresh PowerShell terminal.

## 8. Verification

- [ ] 8.1 Run `pytest`, `node --test "tests/js/*.test.mjs"` and `openspec validate website-heartbeat-ui --strict`; verify all pass.
- [ ] 8.2 Run gstack `/qa` against the locally served page (desktop and 360 px) and fix anything it finds that breaks a spec scenario; verify by its report.
- [ ] 8.3 Take the three demo screenshots (alive topic strip, graveyard topic strip, table/CSV) and save them under `docs/screenshots/`; verify the files exist and read clearly.
