# Proposal

## Why

The CSV report's filename is the normalized keyword with spaces turned into hyphens, so any character that isn't allowed in a filename ends up in it. Probed on the current code (Windows): `reposcout search "c++/qt"` builds `c++/qt-report.csv` and crashes with a raw `FileNotFoundError` traceback, because `/` makes it a path into a `c++/` folder that doesn't exist. Worse, `reposcout search "c#: tools"` appears to succeed, but `:` makes Windows write the CSV into a hidden NTFS "alternate data stream" of a file named `c#`, so the report can't be found. Programming-language keywords like `c++`, `c#`, or `node/express` are realistic searches, so this could easily come up in the December demo. Found during HW6 review 1 and carried forward as open issue #2.

## What Changes

- Characters that are invalid in filenames on Windows (`< > : " / \ | ? *`) and control characters are no longer kept in the CSV filename. `/` is also the one character invalid on macOS/Linux, so the same rule covers every OS.
- Each run of such characters and/or whitespace becomes a single hyphen, repeated hyphens collapse to one, and leading/trailing hyphens and dots are trimmed. Example: `"c++/qt"` → `c++-qt-report.csv`, `"a / b"` → `a-b-report.csv`. A leading dot is trimmed so the report never becomes a hidden file on macOS/Linux.
- Letters (including non-ASCII, e.g. Hungarian `á`, `ő`), digits, and `+ . _ -` are kept, so filenames stay readable.
- If nothing is left after this (e.g. keyword `"???"`), the filename falls back to `search-report.csv`.
- Unchanged: `"expense tracker"` still gives `expense-tracker-report.csv` (README demo and acceptance criteria), and two keywords that produce the same filename still silently overwrite each other (already accepted by the spec).
- Unchanged: the cache. Cache files are already named by a SHA-256 digest of the query, so they never had this problem.

**Out of scope:** dated or versioned report files (so re-runs don't overwrite earlier reports). That's a separate design question, logged as open issue #7 in AGENTS.md.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `repo-search`: the "CSV export" requirement's filename rule now states how filename-unsafe characters are replaced, and what happens when nothing usable is left.

## Impact

- **Code:** `reposcout/output.py` (`slugify_keyword()`; `csv_filename()` for the fallback).
- **Tests:** `tests/test_output.py` (unit tests for the new cases), `tests/test_cli.py` (an end-to-end run with `"c++/qt"` that currently crashes).
- **Docs:** `docs/USER_MANUAL.md`, where the CSV filename is described.
- No new dependencies.
