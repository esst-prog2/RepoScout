# RepoScout
For Advanced Programming class

See [docs/USER_MANUAL.md](docs/USER_MANUAL.md) for installation, GitHub token setup, and usage instructions.

## 1. The demo

I open the RepoScout page in my browser (served from the `site/` folder with `python -m http.server`, no sign-in or token) and click the example topic `project management software`. RepoScout asks GitHub for the 50 best-matching repositories and answers in one headline: `Showing the 50 best-matching of 14,067 repos, 10 active among them — most recent entrant pushed 1 minute ago`. Below it, the **heartbeat strip** draws every repository as a dot on ECG-style chart paper, bigger for more stars and further right for a more recent push, with a trace along the bottom that spikes wherever repos were pushed. Two more searches show the contrast: `mcp server` is alive (37 of 50 active, the trace beating on the right), while `angularjs directive` is a graveyard (0 active, the trace flatlining across the whole active zone). Under the strip, a table ranks the same 50 repos by stars with last push date, language and activity bucket, and **Download CSV** saves `project-management-software-report.csv` with the same rows. The same search also runs on the command line (`reposcout search "project management software"`), which prints the same verdict sentence and writes the same CSV.

## 2. The shape

```
in a topic or keyword typed on the command line 
out a terminal summary + a CSV with the ranked repo list
in between query GitHub's search API for repos matching the keyword;
fetch each repo's stars, last commit date and language; bucket each
repo by recency of activity; rank and summarize
```

## 3. The size

**First useful version**

- keyword in → GitHub Search API query, top 50 results by stars
- per repo: stars, last commit date, primary language
- each repo bucketed by activity: active (commit in last 3 months), slowing (3–12 months), stale (12+ months)
- one-line terminal summary (repo count + how many are active + most recent entrant)
- CSV export of the full ranked list
- results cached per keyword for 24 hours, so repeat searches don't re-hit the API

**Not this term**

- a browser UI — command line only, for now
- an AI-generated written summary of the results
- tracking a saved search over time / alerting on new entrants
- cross-referencing with other sources (Product Hunt, npm, etc.)
- cloning repos to inspect code quality or real commit history in depth
- authentication flows beyond a single personal access token read from an environment variable

## 4. How we would know it works

- Given a keyword with zero matching repos, it prints "0 repos found" and writes a CSV with headers only, not an error.
- Given a repo with no commits in the last 3 months, it is bucketed as "slowing" or "stale," not "active," in the summary line.
- Given the same keyword run twice within 24 hours, the second run makes zero GitHub API calls — verified by a logged call count.

## 5. What could stop this

- **Rate limits.** GitHub's *search* endpoint — the one this tool actually calls — allows only 10 requests/minute unauthenticated, not the 60/hour figure often quoted for GitHub's other API endpoints — nowhere near enough, since a single search can require one call for the search results plus one follow-up call per repo to get commit/language detail. A free personal access token raises this to 30 requests/minute (not 5,000/hour, which is also a different endpoint's limit), but the tool still has to track remaining quota, stop before hitting zero, and fail with a clear message rather than a crash mid-run.
- **Pagination.** The Search API returns results in pages of up to 100, and caps total results at 1,000 regardless of how many actually match. For a 50-result first version this is manageable, but the code has to request pages correctly rather than assuming everything arrives in one call — and has to say plainly when a keyword is broad enough that the true count is unknown, not just report 1,000 as if it were exhaustive.
- **Caching correctness, not just presence.** "Cache the result" sounds simple but raises real decisions: what counts as the same query (`"expense tracker"` vs `"Expense Tracker"` vs `"expense-tracker"`), what the expiry window should be, and what happens if the cache file is read while a new search is still being written to it. Getting this wrong either serves stale data silently or defeats the point of caching altogether.
- **Activity is a proxy, not a fact.** A recent commit can come from an automated dependency-update bot rather than real development, and a well-maintained repo can go quiet for months without being abandoned. The bucketing logic (active/slowing/stale) will sometimes mislabel repos, and that's a known, stated limitation rather than something the first version tries to fully solve. It's also not just theoretical: `pushed_at` (what the tool reads) reflects a push to *any* branch, not necessarily the default branch a user would actually look at. A 50-repo spike (`spike/pushed_at_drift.py`) found `pushed_at` matches the real default-branch commit almost exactly for most repos, but diverges by months or years for others — not a smooth spread, just near-zero or large — changing the activity bucket for 5 of the 50 repos sampled.
