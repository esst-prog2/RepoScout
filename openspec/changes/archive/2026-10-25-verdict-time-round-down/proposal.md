# Proposal

## Why

The verdict line's "most recent entrant pushed …" uses `humanize.naturaltime`, which rounds to the *nearest* unit, often up. Probed on the current code: 16 days shows "a month ago", 46 days shows "2 months ago", 89 days shows "3 months ago", 364 days shows "a year ago", and even 23h59m shows "a day ago". Besides being inexact, this can contradict the bucket counts on the same line. A repo pushed 89 days ago is *active* and one pushed 100 days ago is not, yet both show "3 months ago", so a run can print `0 active in the last 3 months — most recent entrant pushed 3 months ago`. The spec's own example, "pushed 2 weeks ago", can't currently happen, because `humanize` never uses weeks. Found during HW6 review 4 and carried forward as open issue #3.

## What Changes

- The relative time in the verdict is always **rounded down**, never up, using the largest fitting unit: seconds as "just now" (under a minute), minutes (under an hour), hours (under a day), days (under 14 days), weeks (under 90 days), months of 30 days (under 365 days), then years plus months. Examples: 16 days → "2 weeks ago", 89 days → "12 weeks ago", 100 days → "3 months ago", 400 days → "1 year, 1 month ago".
- Smaller wording changes that come with this: a count of one is written as a number ("1 day ago", "1 hour ago", "1 minute ago" instead of humanize's "a day ago", "an hour ago", "a minute ago"), and 14–15 days now read "2 weeks ago" instead of "14 days ago" / "15 days ago".
- So an `active` repo (pushed under 90 days ago) never shows "3 months", and the shown time is never later than the real one.
- `humanize` is no longer used anywhere, so it is removed from `pyproject.toml`'s dependencies.
- Unchanged: the verdict's structure, the bucket thresholds, the table and the CSV (they show dates, not relative times).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `repo-search`: the "One-line verdict summary" requirement now states how the relative time is phrased and that it is always rounded down.

## Impact

- **Code:** `reposcout/output.py` (a new relative-time function replaces `humanize.naturaltime` in `format_verdict()`).
- **Dependencies:** `humanize==4.16.0` removed from `pyproject.toml`. One fewer third-party package to install and trust.
- **Tests:** `tests/test_output.py` (unit tests for every unit boundary, plus a verdict-level test of the 89/100-day contradiction).
- **Docs:** `docs/USER_MANUAL.md`'s example verdict ("2 weeks ago") becomes accurate. Add one line saying times are rounded down.
