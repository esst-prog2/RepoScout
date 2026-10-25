# Design

## Context

`output.format_verdict()` computes `now - most_recent.pushed_at` and passes the timedelta to `humanize.naturaltime()`, which is the only use of `humanize` in the project. `bucketing.py` defines the active window as `ACTIVE_THRESHOLD_DAYS = 90`, and `active_window_text()` renders it as "3 months" using 30-day months. See proposal.md for the probe results.

## Goals / Non-Goals

**Goals:**
- One small, pure function, `time_ago(delta: timedelta) -> str`, in `output.py`. It floors at every unit and is unit-tested at each boundary.
- Use the same 30-day month as `active_window_text()`, so "3 months" means the same thing in both halves of the verdict.

**Non-Goals:**
- Localisation or calendar-accurate months (a month here is 30 days, a year 365 days, as everywhere else in RepoScout).
- Relative times anywhere else (the table and CSV show ISO dates).

## Decisions

**Write our own function instead of configuring `humanize`.** `naturaltime`/`naturaldelta` have no "round down" option: the nearest-unit rounding is built in, and it also rounds up under a day (119 s → "2 minutes", 23h59m → "a day"). `humanize.precisedelta` floors, but it prints multi-unit strings ("16 days and 3 hours") and has no weeks-then-months scheme. About 20 lines of our own code is simpler than bending either, and it removes a dependency. Alternative considered: keep `humanize` only for under a day. Rejected, because it rounds up there too.

**Unit boundaries:** under 60 s → "just now"; under 1 h → minutes; under 1 day → hours; under 14 days → days; under 90 days → weeks (`days // 7`, so 2–12); under 365 days → months (`days // 30`, so 3–12); from 365 days → `years = days // 365`, `months = (days % 365) // 30`, capped at 11 so 360–364 leftover days don't print "1 year, 12 months". Singular forms for 1 ("1 day ago", "1 year ago"). Months are omitted when zero ("2 years ago").

**Why weeks up to 90 days specifically.** It matches today's active threshold, so active repos (< 90 days) always show days or weeks, and "3 months" only ever appears for repos that really are 3+ months old. The boundary is a fixed unit choice rather than tied to `ACTIVE_THRESHOLD_DAYS`. Because every unit is floored, the shown time is never later than the real one, so the verdict stays consistent for any threshold. For example, with a 180-day window a 100-day repo shows "3 months ago" alongside "active in the last 6 months", which is still true.

**Negative deltas** (a `pushed_at` slightly in the future because of clock skew between GitHub and the local machine) are treated as zero → "just now", rather than crashing or printing a negative number.

## Risks / Trade-offs

- [Trade-off] Weeks up to 12 ("12 weeks ago") read slightly less naturally than "3 months ago". Accepted with the user (option A), because it never contradicts the active count.
- [Risk] Removing `humanize` from `pyproject.toml` leaves it installed in existing `.venv`s. → Harmless. A fresh `pip install .` no longer pulls it in. Verify with a grep that nothing imports it.
