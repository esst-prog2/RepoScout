# Tasks

## 1. Reproduce first

- [ ] 1.1 Add a CLI-level test in `tests/test_cli.py`: search `"c++/qt"` with GitHub mocked to return one repo; assert exit code `0`, `c++-qt-report.csv` exists directly in the working directory, and no `c++` subdirectory was created. Run it and verify it fails against the current code (`FileNotFoundError`).
- [ ] 1.2 Add unit tests in `tests/test_output.py` for `slugify_keyword()`/`csv_filename()`: `"c++/qt"` → `c++-qt`, `"c#: tools"` → `c#-tools`, `"a / b"` → `a-b`, `"???"` → `search-report.csv`, `".hidden"` → `hidden`, `'a\\b|c*d"e<f>g'` → `a-b-c-d-e-f-g`, Hungarian `"költség követő"` → `költség-követő`, and `"expense tracker"` still → `expense-tracker-report.csv`. Verify the new cases fail on the current code.

## 2. Implementation

- [ ] 2.1 Rewrite `slugify_keyword()` in `reposcout/output.py` per design.md (unsafe/whitespace runs → `-`, collapse `--`, strip `-`/`.` at the ends, fall back to `"search"`), still building on `normalize_query()`; verify the tests from 1.1 and 1.2 pass.

## 3. Docs and verification

- [ ] 3.1 Update the CSV export paragraph in `docs/USER_MANUAL.md`: characters that can't be used in filenames are replaced with hyphens (e.g. `"c++/qt"` → `c++-qt-report.csv`), and a keyword with nothing usable gives `search-report.csv`. Verify by reading the section.
- [ ] 3.2 Run the full suite (`pytest`) and `openspec validate safe-csv-filename --strict`; verify both pass.
