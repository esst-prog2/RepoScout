# Proposal

## Why

The verdict prints large counts as one block of digits ("Showing the 50 best-matching of 177455 repos"), which is hard to read at a glance and harder still on a projected screenshot. The user asked for thousands separators (open issue #8). The website must say exactly what the CLI says (shared fixture), so the change has to land in both at once.

## What Changes

- The verdict writes counts with a comma every three digits: `Showing the 50 best-matching of 177,455 repos, 37 active among them — …`, `1,204 repos found, …` (only possible above 999, so in practice the "best-matching of N" total). Counts under 1,000 are unchanged.
- Always a comma, whatever the computer's language settings, so the CLI, the website and the tests agree everywhere.
- The CLI (`reposcout/output.py`) and the website (`site/rules.js`) change together; the shared fixture (`tests/fixtures/rules.json`) gets the new expected text and boundary cases (999, 1,000, 1,000,000).
- The website's printout line under the strip ("GitHub search · 50 of 177,455 repos · …") uses the same formatting, so one number never appears two ways on the page.
- Docs and examples updated: user manual, README §1 numbers (done with the screenshots), the `web-ui` scenario example in the still-open `website-heartbeat-ui` change.
- Not changed: the Stars column in the table and the CSV. The CSV stays plain digits so spreadsheets read numbers as numbers; the table keeps the CLI's column format.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `repo-search`: the "One-line verdict summary" requirement gains the thousands-separator rule, and its example uses it.

## Impact

- Code: `reposcout/output.py` (`format_verdict`), `site/rules.js` (`formatVerdict`, plus the printout line in `site/app.js`).
- Tests: `tests/test_output.py` verdict assertion, `tests/fixtures/rules.json` verdict cases (checked by both `pytest` and `node --test`).
- Docs: `docs/USER_MANUAL.md`, `openspec/changes/website-heartbeat-ui/specs/web-ui/spec.md` (example only; that capability isn't archived yet), README §1 later with the new screenshots.
- No dependency, cache-format or CSV change.
