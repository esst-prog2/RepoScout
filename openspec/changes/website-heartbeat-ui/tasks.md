# Tasks

## 1. Thin path first: keyword in, verdict on screen

- [ ] 1.1 Verify Node 24 can `import` an ES-module `.js` file without a `package.json` (a throwaway check in the scratchpad); if not, plan the one-line `site/package.json` `{"type": "module"}` fallback. Verify by the check's output.
- [ ] 1.2 Create `site/index.html` (title, one-line promise, search form, verdict area), `site/style.css` (minimal), `site/app.js` (form submit → `fetch` GitHub search with `per_page=50`, no `sort`, `encodeURIComponent` → verdict text), and `site/rules.js` with `bucketFor`, `timeAgo`, `activeWindowText`, `formatVerdict` ported from `bucketing.py`/`output.py`. Verify by serving `site/` with `python -m http.server` and loading the page without console errors.
- [ ] 1.3 Live walk-through of the thin path (run by the user in their own browser, since the agent sandbox can't reach GitHub from Python): search "expense tracker" and see a verdict line. Verify by the user's report.

## 2. Shared rules fixture (two implementations, one fixture)

- [ ] 2.1 Create `tests/fixtures/rules.json` with a fixed `now` and cases for: buckets at 89/90/364/365 days; verdict for >50 matches, ≤50 matches and zero; `time_ago` across every unit (just now, minutes, hours, days, 14 days → 2 weeks, 89 → 12 weeks, 90 → 3 months, 365 → 1 year, 729 → 1 year 11 months); normalization (`"  Expense   Tracker "`, `költség követő`, `Straße`); slug/filename (`c++/qt`, `c#: tools`, `???`); CSV text for a name containing a comma and a repo with no language. Expected values are computed from the current Python functions, not hand-guessed. Verify the JSON parses.
- [ ] 2.2 Add `tests/test_rules_fixture.py` running every fixture case through the real Python functions (`classify_bucket`, `format_verdict`, `time_ago`, `normalize_query`, `slugify_keyword`, `csv_filename`, and the CSV writer). Verify `pytest` passes (119 existing + new).
- [ ] 2.3 Add `tests/js/rules.test.mjs` (`node:test`, no npm packages) running the same cases through `site/rules.js`; extend `rules.js` with `normalizeQuery`, `slugifyKeyword`, `csvFilename`, `csvRows` as needed. Verify `node --test tests/js/` passes.
- [ ] 2.4 Drift check: temporarily change the active threshold in `site/rules.js` only, confirm the JS fixture test fails, revert; do the same in `reposcout/bucketing.py` and confirm the Python fixture test fails, revert. Never commit the broken values. Verify by the two failing runs and the green runs after reverting.

## 3. Results table and CSV

- [ ] 3.1 Render the ranked table (CLI columns, `-` for no language, `Last Push` as a date), sorted by stars descending regardless of GitHub's order. Verify with a recorded response in the browser (stars 5/300/40 → 300/40/5).
- [ ] 3.2 Add the Download CSV button using `csvRows`/`csvFilename` (CRLF, minimal quoting, UTF-8 without BOM, `<slug>-report.csv`). Verify by downloading for `c++/qt` → `c++-qt-report.csv`, opening it, and comparing it with the CLI's CSV for the same recorded data.

## 4. Heartbeat strip

- [ ] 4.1 Vendor `d3` and `@observablehq/plot` UMD builds at exact versions into `site/vendor/` with their licence files (download via PowerShell from jsDelivr's npm mirror); load them as classic scripts before `app.js`. Verify the files exist and `Plot`/`d3` are defined in the page.
- [ ] 4.2 Add `xPosition(days)` to `rules.js` (equal-thirds piecewise mapping, clamp at 5+ years) with fixture cases (0, 45, 90, 200, 365, 1000, 3000 days). Verify both fixture test runs pass.
- [ ] 4.3 Draw the strip: zone backgrounds and labels, custom ticks ("5+ years", "1 year", "90 days", "now"), `Plot.dodgeY` dots with a capped square-root radius by stars, shade by bucket, tooltip with name/stars/last push, the one-line "Last push = GitHub's pushed_at" note, and the "chart unavailable" fallback when `Plot` is missing. Verify the fallback by temporarily renaming the vendor file.
- [ ] 4.4 Check the strip against a real "expense tracker" result (user's browser) and a graveyard-ish topic; adjust the radius cap or height if dots are unreadable. Verify by the user's screenshot or report.

## 5. States and browser cache

- [ ] 5.1 Implement `isRateLimited` and `resetSeconds` in `rules.js` (non-OK only; 403/429 with remaining 0 or `Retry-After`; `Retry-After` first, then `X-RateLimit-Reset`, else no countdown), with fixture cases including "200 with remaining 0 → not limited". Verify both fixture test runs pass.
- [ ] 5.2 Wire every state into `app.js`: loading; empty/whitespace input blocked; zero results; incomplete-results warning; rate-limited countdown that re-enables Scout at zero (no auto-retry) or "no reset time given"; offline ("Could not reach GitHub"); other errors naming the HTTP status (e.g. 422). Verify each state with a recorded/forced response in the browser.
- [ ] 5.3 Add the `localStorage` cache (24h, `reposcout:<normalized key>`, stores `incomplete`, entries without it are a miss, every access in `try/catch`). Verify: a repeat search makes no request (browser network tab), and the page still works with storage blocked.

## 6. Phone width

- [ ] 6.1 Add responsive CSS: stacked layout under ~600 px, the table scrolls inside its own box (or hides `Language`/`Last Push`), a taller strip on narrow screens, no horizontal page scroll at 360 px. Verify at 360 px width (browser device mode, or gstack `/qa` at a phone viewport).

## 7. Docs (includes HW8)

- [ ] 7.1 Rewrite README §1 "The demo" for the website demo (open the page, search a topic, read the verdict, point at the heartbeat strip, show the table and CSV), keeping the CLI as the tool underneath. Verify by reading it against the actual page.
- [ ] 7.2 Add a "Website" section to `docs/USER_MANUAL.md`: how to start it (`cd site`, `python -m http.server`, open `http://localhost:8000`), that it needs no token (10 searches/minute limit, countdown), what the strip shows, and the full test command `pytest && node --test tests/js/`. Verify by following the steps from a fresh terminal.

## 8. Verification

- [ ] 8.1 Run `pytest && node --test tests/js/` and `openspec validate website-heartbeat-ui --strict`; verify all pass.
- [ ] 8.2 Run gstack `/qa` against the locally served page (desktop and 360 px) and fix anything it finds that breaks a spec scenario; verify by its report.
- [ ] 8.3 Take the three demo screenshots (alive topic strip, graveyard topic strip, table/CSV) and save them under `docs/screenshots/`; verify the files exist and read clearly.
