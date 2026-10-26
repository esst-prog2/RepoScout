# Design

## Context

The verdict is built in two places that must agree word for word: `format_verdict()` in `reposcout/output.py` (CLI) and `formatVerdict()` in `site/rules.js` (website). Both are checked against `tests/fixtures/rules.json` (pytest and `node --test`); the fixture is hand-edited reference data, never regenerated from either side. The website also prints the total in its printout line (`printoutLine()` in `site/app.js`), which currently copies the verdict's plain digits on purpose. See proposal.md for why.

## Goals / Non-Goals

**Goals:**
- One formatting rule, identical output in Python and JavaScript on any machine.

**Non-Goals:**
- Locale-aware formatting (Hungarian "244 832", German "244.832").
- Separators in the Stars column or the CSV.

## Decisions

**A fixed comma, not the locale's separator.** Python: `f"{n:,}"` (always a comma, independent of `locale`). JavaScript: a small `groupThousands(n)` helper using a regex on the digit string (`String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",")`), not `toLocaleString`, whose output depends on the runtime's ICU data and the browser's language. Alternative considered: locale-aware formatting on both sides. Rejected: the CLI and the page would disagree on the same machine (Python ignores the OS locale for `{:,}`, the browser doesn't), the fixture couldn't pin one expected string, and the verdict wording is English anyway.

**Format every count in the verdict.** Fetched and active counts can't exceed 50 today, so only the total is visibly affected; formatting all of them keeps the rule simple and future-proof (e.g. if the fetch limit ever grows). Applied at the point where the sentence is built, not in the data, so the cache and CSV keep raw integers.

**Printout line uses the same helper,** so the page never shows "177,455" in one line and "177455" in another.

**Fixture first.** Update the expected verdict strings and add boundary cases (999, 1000, 1000000) by hand before touching code, run both suites and see them fail, then change both implementations.

## Risks / Trade-offs

- [Risk] Someone parsing the CLI's verdict line with a script would now see commas. → The verdict is for people; machine-readable output is the CSV, which is unchanged.
- [Trade-off] A Hungarian reader sees an English-style comma. → The whole interface is in English; consistency with the CLI and tests wins.
