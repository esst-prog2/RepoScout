# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary:** classmates and the instructor of the ELTE Advanced Programming course, who see the page in a five-minute presentation made of screenshots (1 and 8 Dec 2026), not a live run.
- **Also:** the author and a friend, who use it for real to check a topic on GitHub before starting or picking a project.

## Product Purpose

RepoScout searches GitHub for a topic, takes the 50 best-matching repositories, and shows how active they are: a one-sentence verdict, a "heartbeat strip" chart (each repo a dot placed by time since last push, sized by stars, shaded by activity bucket), a table ranked by stars, and a CSV download. The website is the friendly front end of the existing Python command-line tool (`reposcout search "<keyword>"`), which stays the tool underneath.

Success: one search gives a ranked list and a CSV quickly, and the screenshots read clearly in a presentation.

## Positioning

A fast GitHub topic search with export: type a topic, get the 50 best matches ranked by stars with last push, language and activity bucket, and download them as a CSV, with no sign-in or token.

## Operating Context

- Run locally: `cd site`, `python -m http.server`, open http://localhost:8000. GitHub Pages is a possible later step, not done yet.
- Calls GitHub's search API directly from the browser, unauthenticated: 10 searches a minute; when the limit is hit the page says when to try again.
- Results are cached in the browser for 24 hours per normalized keyword.
- Demo keywords: alive `mcp server`, graveyard `angularjs directive`, table/CSV `project management software`; `expense tracker` is the long-running example in the README and the project history.

## Capabilities and Constraints

- **Static, no build step:** plain HTML/CSS/JS in `site/`, no framework, libraries vendored at exact versions (d3 7.9.0, Observable Plot 0.6.17). Must keep working on localhost and be publishable as static files later.
- **Same rules as the CLI:** verdict wording, bucket thresholds (active < 90 days, slowing < 365 days, stale otherwise), ranking, `Last Push` date, CSV format and filename follow the Python CLI exactly; a shared test fixture (`tests/fixtures/rules.json`) is checked by `pytest` and `node --test "tests/js/*.test.mjs"`.
- **Works at phone width:** usable at 360 px, no sideways page scroll.
- Specified behaviour lives in `openspec/changes/website-heartbeat-ui/specs/web-ui/spec.md` (later `openspec/specs/web-ui/spec.md`); design changes must keep every scenario true (states: loading, empty input, zero results, incomplete results, rate limit, offline, HTTP error, unexpected response; chart fallback; latest search wins; text inserted as text).
- Terminology: "Last Push" (GitHub's `pushed_at`, a proxy, not the last commit), buckets "active / slowing / stale", "best-matching".

## Brand Commitments

- Name: RepoScout. Search button label: "Scout".
- Honest wording is part of the product: the verdict says "Showing the 50 best-matching of N repos" when there are more, and the page notes that Last Push is GitHub's `pushed_at`.

## Evidence on Hand

- Live results recorded in `README.md` §1 and `AGENTS.md`.
- HW4 spike data: `spike/pushed_at_drift.csv` (pushed_at vs real last commit for 50 repos; 5/50 change bucket).
- Demo screenshots in `docs/screenshots/`: 1 alive (`mcp server`), 2 graveyard (`angularjs directive`), 3–4 `project management software` (headline + strip, table + CSV).
- No users, testimonials or usage numbers exist; don't invent any.

## Product Principles

1. Answer first: the verdict and ranked list are on screen before anything decorative, and survive if the chart fails.
2. Honest over impressive: state the limits (top 50, `pushed_at` is a proxy) instead of hiding them.
3. One source of rules: the page never disagrees with the CLI.
4. Readable as a screenshot: every screen should make its point in a still image at presentation size.
