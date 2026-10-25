# Tasks

## 1. Reproduce first

- [ ] 1.1 Add a verdict-level test in `tests/test_output.py`: with the most recent repo pushed 16 days before `NOW`, `format_verdict()` ends with "pushed 2 weeks ago"; with 89 days it ends with "pushed 12 weeks ago". Run it and verify it fails against the current code ("a month ago" / "3 months ago").
- [ ] 1.2 Add parametrized unit tests for `time_ago(timedelta)` at every boundary: 0 s and a negative delta → "just now", 59 s → "just now", 60 s → "1 minute ago", 119 s → "1 minute ago", 59 min → "59 minutes ago", 1 h → "1 hour ago", 23h59m → "23 hours ago", 1 day → "1 day ago", 13 days → "13 days ago", 14 days → "2 weeks ago", 16 days → "2 weeks ago", 89 days → "12 weeks ago", 90 days → "3 months ago", 100 days → "3 months ago", 364 days → "12 months ago", 365 days → "1 year ago", 400 days → "1 year, 1 month ago", 729 days → "1 year, 11 months ago", 730 days → "2 years ago", 2057 days → "5 years, 7 months ago".

## 2. Implementation

- [ ] 2.1 Add `time_ago()` to `reposcout/output.py` per design.md and use it in `format_verdict()` instead of `humanize.naturaltime`; verify the tests from 1.1 and 1.2 pass.
- [ ] 2.2 Remove `import humanize` from `output.py` and `humanize==4.16.0` from `pyproject.toml`; verify with a grep that nothing in `reposcout/`, `tests/`, or `spike/` imports `humanize`.

## 3. Docs and verification

- [ ] 3.1 In `docs/USER_MANUAL.md`, next to the example verdict, add that the "pushed … ago" time is always rounded down (e.g. 16 days shows as "2 weeks ago"); verify by reading the section.
- [ ] 3.2 Run the full suite (`pytest`) and `openspec validate verdict-time-round-down --strict`; verify both pass.
