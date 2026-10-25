# Design

## Context

`github.search_repositories()` sends `q=<keyword>&sort=stars&order=desc&per_page=50`. `bucketing.rank_by_stars()` already re-sorts whatever comes back by stars for display; its docstring explains that GitHub's sort decides *which* 50 and the local sort owns the *display* order. `cache.py` stores `fetched_at`, `total_count`, `incomplete` and the raw repo fields per normalized keyword, and since HW6 review 8 treats an entry missing a required field (`incomplete`) as a miss rather than guessing. See proposal.md for the evidence from the explore session.

## Goals / Non-Goals

**Goals:**
- Let GitHub's relevance ranking choose the 50, and keep the star-ranked display.
- No result selected the old way is shown after the update, not even from the cache.

**Non-Goals:**
- Our own relevance filtering or scoring (option D in explore; guessy and it would break `total_count`).
- Changing what counts as a match (exact phrase by default was rejected in explore).
- A `--by-stars` option (deferred).

## Decisions

**Omit `sort` and `order` rather than send `sort=best-match`.** GitHub's REST search documents relevance ("best match") as the default when `sort` is absent; `best-match` is not a documented `sort` value for repository search, so sending it relies on undocumented behaviour. Omitting both parameters is the documented way. The explore probes used exactly this request (no `sort`) and got the relevance ordering. The test asserts the request has neither parameter.

**Display order stays with `rank_by_stars()`, unchanged.** Its docstring is updated: GitHub's *relevance* ranking now decides which 50; the local sort still owns the display order. This makes the two-sorts design more important, not less: without it the table would appear in GitHub's relevance order.

**Mark cache entries with how they were selected.** `write_cache()` stores `"selection": "best-match"`; `read_cache()` returns a miss unless that field equals `"best-match"`. This reuses the review-8 pattern ("missing field = older format: refetch, don't guess"). Alternatives considered:
- *Do nothing*: old entries expire within 24 h, but for up to a day a user could see star-picked junk for a query they'd just searched, right after updating. Cheap to avoid.
- *Change the cache directory or key*: works, but leaves orphaned files in the user's cache directory and is less explicit than a field.

The field records a fact about the data, not a version number, so a future selection mode (e.g. a `--by-stars` option) could store `"stars"` and be checked the same way.

**Verdict wording lives in `format_verdict()` only.** Only the more-than-50 branch changes: `Showing the 50 best-matching of {total} repos, {active} active among them — most recent entrant pushed …`. The "50" stays derived from `len(bucketed)`, as today.

**Spike script left as it is.** `spike/pushed_at_drift.py` (frozen HW4 evidence) calls `search_repositories()`. Its committed CSV and the analysis mode that reads it are unaffected; only a fresh `--fetch` would now draw a different 50-repo sample. Freezing a copy of the old request inside the spike would be code nobody runs. Noted in the proposal's Impact instead.

## Risks / Trade-offs

- [Trade-off] For broad searches, the shown 50 are no longer the 50 most popular matches, so a very popular but tangential repo may now be missing. → Accepted (user's choice: "most on-topic by default, and among those the most popular"). Popular on-topic repos still rank at the top of the table.
- [Risk] GitHub's relevance formula is unpublished and could change. → It's GitHub's job to rank relevance well, and the alternative (stars) demonstrably produced junk. Behaviour is still one documented API request.
- [Risk] Tests can't check GitHub's ranking itself (HTTP is mocked). → Tests check what RepoScout controls: the request carries no star sort, and whatever order GitHub returns, the display is by stars. The live evidence is recorded in proposal.md and AGENTS.md.
