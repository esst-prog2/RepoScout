# Proposal

## Why

Multi-word searches return unrelated repositories. In HW5, `reposcout search "repo activity research"` was topped by `molyswu/hand_detection` (a TensorFlow hand detector) and `hackcrypto/fluxion` (a Wi-Fi phishing tool). The explore session (2026-10-25) tested this against live GitHub and found the cause is the **star sort, not the matching**. GitHub matches a repo when every word appears *somewhere* in its name, description or topics, in any order, at any distance, including word forms ("activities" for "activity"). Both junk repos pasted their whole README into the description, so the three words appear thousands of words apart. Because RepoScout asks for `sort=stars`, the most-starred of those loose matches come first. Without the star sort, GitHub ranks by its own relevance ("best match"). Tested: for the same 80 matches, none of the five junk repos from the HW5 run is in the relevance top 50, and for "expense tracker" the relevance top results are all real expense trackers. Open issue #5.

## What Changes

- RepoScout asks GitHub for the **50 best-matching** repositories (GitHub's relevance ranking) instead of the 50 most-starred, and still **displays them ranked by stars**. Which 50 are shown changes when a search has more than 50 matches. The match set, the total count, the table, the CSV columns and the display order do not change.
- When there are more than 50 matches, the verdict says `Showing the 50 best-matching of N repos, …` instead of `Showing top 50 of N matching repos, …` (which now reads as "top 50 by popularity"). The wording for 50 or fewer matches is unchanged.
- A cached result fetched the old way (by stars) is not reused. It's treated as a cache miss and refetched once. Old entries would expire within 24 hours anyway; this just avoids showing star-picked results right after the update.
- `docs/USER_MANUAL.md`: the descriptions of what is fetched are updated, plus a short tip that quotes force an exact phrase (`reposcout search '"expense tracker"'`, which can return 0 results for unusual phrases) and that GitHub qualifiers such as `language:python` work. Both already work today, since the keyword is passed to GitHub unchanged; they're just undocumented.

**Decided against (explore session):** exact-phrase search by default (`"repo activity research"` returns 0 results; for "expense tracker" it changes nothing visible), and a `--by-stars` option to keep the old selection (can be added later if needed).

**Left unchanged:** `README.md` ("top 50 results by stars", §3). It's the original course project spec, and like earlier changes this one leaves the README's plan narrative alone. The current behaviour is documented in the spec and the user manual.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `repo-search`: "Keyword search against GitHub" (which 50 are fetched: best match, not stars) and "One-line verdict summary" (wording when there are more than 50 matches).
- `search-cache`: "Cache hit avoids GitHub API calls" gains the rule that an entry fetched under the old selection is not reused.

## Impact

- **Code:** `reposcout/github.py` (drop `sort`/`order` from the request; docstring), `reposcout/output.py` (verdict wording), `reposcout/cache.py` (record and check how the entry was selected), `reposcout/bucketing.py` (comment on `rank_by_stars()` explaining the two orderings).
- **Tests:** `tests/test_github.py` (request has no star sort), `tests/test_output.py` (new verdict wording), `tests/test_cache.py` (old-format entry → miss).
- **Docs:** `docs/USER_MANUAL.md`.
- **Spike:** `spike/pushed_at_drift.py` reuses `search_repositories()`, so re-running it with `--fetch` would now sample a different 50 repos. The committed HW4 CSV and its analysis are unaffected (see design.md).
- No new dependencies; still exactly one API call per search.
