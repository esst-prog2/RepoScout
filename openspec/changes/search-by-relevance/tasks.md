# Tasks

## 1. Reproduce first

- [x] 1.1 Add a test in `tests/test_github.py` asserting the search request sends no `sort` and no `order` parameter (inspect `responses.calls[0].request.url`). Run it and verify it fails against the current code (`sort=stars&order=desc`).
- [x] 1.2 Add a CLI-level test in `tests/test_cli.py`: GitHub (mocked) returns items in relevance order with stars not descending (e.g. 5, 300, 40); assert the table lists them by stars (300, 40, 5), so display order doesn't depend on GitHub's order. (Expected to pass already; it's a guard for the two-sorts design.)
- [x] 1.3 Update `test_format_verdict_top_50_phrasing_when_total_exceeds_fetched` in `tests/test_output.py` to expect "Showing the 50 best-matching of 3241 repos"; verify it fails against the current code.
- [x] 1.4 Add a test in `tests/test_cache.py`: an unexpired cache file without a `"selection"` field (the current format) is a miss (`read_cache()` returns `None`); verify it fails against the current code. Update any existing cache tests that write cache files by hand to include `"selection": "best-match"`.

## 2. Implementation

- [x] 2.1 `reposcout/github.py`: remove `sort` and `order` from the request params and update `search_repositories()`'s docstring ("50 best-matching repos by GitHub's relevance ranking"); verify 1.1 passes.
- [x] 2.2 `reposcout/cache.py`: `write_cache()` stores `"selection": "best-match"`; `read_cache()` returns `None` unless the field equals `"best-match"`; verify 1.4 passes and the existing cache-hit tests still pass.
- [x] 2.3 `reposcout/output.py`: change the more-than-50 verdict branch to "Showing the 50 best-matching of {total} repos, {active} active among them — most recent entrant pushed …"; verify 1.3 passes.
- [x] 2.4 `reposcout/bucketing.py`: update `rank_by_stars()`'s docstring (GitHub's relevance ranking decides *which* 50; this sort owns the display order); verify 1.2 passes.

## 3. Docs and verification

- [x] 3.1 `docs/USER_MANUAL.md`: change "ranks them by stars" / "top 50 matching repositories (by stars)" to say RepoScout fetches the 50 best-matching repos and shows them ranked by stars; update the "Showing top 50 of 3,241…" example to the new wording; add a short tip that quotes force an exact phrase (`reposcout search '"expense tracker"'`, may return 0 results) and that GitHub qualifiers like `language:python` work. Verify by reading the sections.
- [x] 3.2 Search the repo (excluding `.venv/`, `openspec/changes/archive/`, `AGENTS.md`, and the frozen `spike/` and `README.md`) for remaining "by stars" / "sort=stars" / "top 50" claims about which repos are fetched, and fix any that are now wrong; verify the grep only finds display-order mentions.
- [x] 3.3 Run the full suite (`pytest`) and `openspec validate search-by-relevance --strict`; verify both pass.
- [ ] 3.4 Live smoke test with the installed CLI (`reposcout search "repo activity research" --refresh`, run by the user in their own terminal, since the agent's sandbox can't verify GitHub's TLS certificate from Python): verify none of `molyswu/hand_detection`, `hackcrypto/fluxion`, `82goober82/fluxionwpacrack`, `Sfedfcv/redesigned-pancake`, `ManojKumarPatnaik/Major-project-list` appears, and the table is ranked by stars.
