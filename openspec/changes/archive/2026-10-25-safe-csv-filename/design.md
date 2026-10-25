# Design

## Context

`output.slugify_keyword()` is `normalize_query(keyword).replace(" ", "-")`, and `csv_filename()` appends `-report.csv`. `cli._emit_results()` writes to `Path.cwd() / output.csv_filename(keyword)`, so a `/` or `\` in the name turns it into a subdirectory path. HW6 review 3 deliberately made `slugify_keyword()` build on `normalize_query()` so the filename and the cache key share one normalization rule, and this change keeps that. See proposal.md for the bug and the probe results.

## Goals / Non-Goals

**Goals:**
- One function decides the filename stem, and it can only return a single safe path component.
- `"expense tracker"` → `expense-tracker` stays byte-for-byte the same.

**Non-Goals:**
- Windows reserved device names (`CON`, `NUL`, `COM1`, …). They're reserved only as the whole base name (`con.csv`), and the `-report` suffix means the base name is never exactly one of them (`con-report.csv` is a normal file).
- Length limits. GitHub's search query limit (256 characters) keeps the filename well under the 255-character limit common to filesystems.
- Changing the cache key. `normalize_query()` is untouched.

## Decisions

**A deny-list of unsafe characters, not an allow-list.** One regex, `[<>:"/\\|?*\x00-\x1f\x7f\s]+` → `-`, applied to the normalized query. Then collapse `-{2,}` → `-` and strip leading/trailing `-` and `.`. Alternative considered: keep only `[a-z0-9-]`. Rejected (with the user) because it mangles realistic keywords (`c++` → `c`, `c#` → `c`) and drops non-ASCII letters like Hungarian `á`/`ő`, which every modern filesystem handles.

**Whitespace goes through the same regex as unsafe characters.** That way `"a / b"` gives `a-b` in one step, rather than `a---b` cleaned up afterwards. `normalize_query()` has already collapsed whitespace, so for keywords without unsafe characters the result is identical to today's `.replace(" ", "-")`.

**Trim dots as well as hyphens at the ends.** A leading dot would make the report a hidden file on macOS/Linux (`.env-report.csv`), and a keyword of only dots (`".."`) would otherwise leave a meaningless `..` stem.

**The fallback lives in `slugify_keyword()`.** It returns `"search"` when nothing is left, so `csv_filename()` stays a one-line suffix append and the rule "the stem is never empty" sits next to the rest of the stem logic.

## Risks / Trade-offs

- [Trade-off] More keywords now share a filename (`"c++/qt"`, `"c++ qt"` and `"c++-qt"` all give `c++-qt-report.csv`), and the later run silently overwrites the earlier one. → Accepted, matching the spec's existing "Filename collision between distinct keywords" scenario. Dated or versioned files are open issue #7.
- [Risk] Collapsing `--` also changes keywords that genuinely contain a double hyphen (`"a--b"` → `a-b-report.csv`). → Cosmetic only, since the cache key and the search itself still use the exact keyword.
