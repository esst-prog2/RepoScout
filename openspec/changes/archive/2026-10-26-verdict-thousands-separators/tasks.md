# Tasks

## 1. Red first: expected values

- [x] 1.1 In `tests/fixtures/rules.json`, change the "total larger than fetched" verdict to `… of 244,832 repos …` and add verdict cases for totals 999, 1000 and 1000000 (expected "999", "1,000", "1,000,000"), worked out by hand. Verify the JSON parses, and that both `pytest` and `node --test "tests/js/*.test.mjs"` now fail on exactly these cases.
- [x] 1.2 In `tests/test_output.py`, update the 3241 assertion to `"Showing the 50 best-matching of 3,241 repos, …"` and add a test that `format_verdict` still writes "244,832" with the process locale set to Hungarian (`hu_HU`, skipped if that locale isn't installed). Verify it fails before the code change.

## 2. Both implementations

- [x] 2.1 `reposcout/output.py`: format the counts in `format_verdict` with `{:,}`. Verify `pytest` passes (all existing + new cases).
- [x] 2.2 `site/rules.js`: add `groupThousands(n)` (regex, no `toLocaleString`) and use it for every count in `formatVerdict`. Verify `node --test "tests/js/*.test.mjs"` passes.
- [x] 2.3 `site/app.js`: use `groupThousands` for the total in the printout line. Verify in the recorded-data harness (a new `big` case reporting 177455 total matches shows "177,455" in both the verdict and the printout line) and with one live search (e.g. "mcp server") that both lines show the comma.

## 3. Docs and examples

- [x] 3.1 Update the verdict example in `docs/USER_MANUAL.md` ("Showing the 50 best-matching of 3,241 repos…") and the `web-ui` scenario example in `openspec/changes/website-heartbeat-ui/specs/web-ui/spec.md` ("244,832"); the README §1 numbers are rewritten with the new screenshots (task 8.3 of `website-heartbeat-ui`). Verify with a repo-wide search that no remaining doc example shows an unseparated count above 999 (archived changes excepted).
- [x] 3.2 Run `pytest`, `node --test "tests/js/*.test.mjs"` and `openspec validate verdict-thousands-separators --strict`; verify all pass.
