# Spec Delta

## Purpose

A static, tokenless web page that searches GitHub by keyword with the same rules as the RepoScout CLI and shows a topic's health at a glance as a heartbeat strip, plus the verdict, a ranked table and a CSV download.

## ADDED Requirements

### Requirement: Static, tokenless page
The web interface SHALL consist only of static files (HTML, CSS, JavaScript and vendored libraries) that work when served by any static file server, with no build step and no server-side code. The page SHALL call GitHub's repository search API directly from the browser and SHALL NOT use, ask for, or contain a GitHub token. Third-party libraries SHALL be loaded from files inside the project at pinned versions, not from a CDN. Text that comes from GitHub (repository names, languages, URLs) and the user's keyword SHALL be inserted into the page as plain text, never interpreted as HTML.

#### Scenario: HTML-looking data stays text
- **WHEN** a (recorded) response contains a repository named `<img src=x onerror=alert(1)>`
- **THEN** the table and tooltip show those characters literally and no script runs

#### Scenario: Served locally
- **WHEN** the user runs `python -m http.server` in the `site/` folder and opens the page in a browser
- **THEN** the page loads and can run a search, with no token prompt and no request to any host other than the local server and `api.github.com`

#### Scenario: No token anywhere
- **WHEN** the page's files are inspected
- **THEN** they contain no GitHub token and no field or prompt that asks for one

### Requirement: Same selection and ranking as the CLI
For a keyword, the page SHALL request the 50 best-matching repositories by GitHub's relevance ranking (no `sort` parameter), passing the keyword to GitHub unchanged apart from URL-encoding, and SHALL display the fetched repositories ranked by stars, descending. Each repository SHALL be bucketed `active` (last push under 90 days ago), `slowing` (under 365 days) or `stale` (365 days or more), using GitHub's `pushed_at`.

#### Scenario: Search request
- **WHEN** the user searches for `expense tracker`
- **THEN** the page requests `https://api.github.com/search/repositories` with `q=expense%20tracker` (or equivalent encoding) and `per_page=50`, and without a `sort` parameter

#### Scenario: Display order independent of GitHub's order
- **WHEN** GitHub returns repositories with 5, 300 and 40 stars, in that order
- **THEN** the table and strip list them as 300, 40, 5

### Requirement: Verdict line matches the CLI
The page SHALL show a one-line verdict with the same wording rules as the CLI: `<N> repos found, <A> active in the last <window> — most recent entrant pushed <time>` when GitHub's reported total is not larger than the number of repositories fetched, and `Showing the <n> best-matching of <N> repos, <A> active among them — most recent entrant pushed <time>` otherwise, and `0 repos found` when there are none. The relative time SHALL be rounded down exactly as the CLI does it.

#### Scenario: More than 50 matches
- **WHEN** GitHub reports 244,832 matches and 50 are fetched, 10 of them active
- **THEN** the verdict begins `Showing the 50 best-matching of 244,832 repos, 10 active among them`

#### Scenario: Relative time rounded down
- **WHEN** the most recently pushed repository was pushed 16 days ago
- **THEN** the verdict ends `pushed 2 weeks ago`

### Requirement: Heartbeat strip
The page SHALL draw one dot per fetched repository on a horizontal axis of time since last push, divided into three zones of readable width, stale (left), slowing (middle) and active (right). Within each zone the position SHALL be proportional to days since last push over that zone's range (active 0-90 days, slowing 90-365 days, stale 365 days to 5 years); repositories pushed more than 5 years ago SHALL be placed at the left edge, which is labelled as 5+ years. Dot area SHALL grow with stars on a square-root (or capped) scale, dot shade SHALL show the bucket, and overlapping dots SHALL be separated vertically. Each dot SHALL show the repository name, stars and last push date on hover or tap. The page SHALL state in one line that "last push" is GitHub's `pushed_at`, not a verified last commit. If the chart libraries are not available or the chart fails to draw, the page SHALL still show the verdict and table, with a plain note that the chart is unavailable.

#### Scenario: Active repositories have room
- **WHEN** a search returns repositories pushed across ten years, some within the last 90 days
- **THEN** the active zone takes up a readable share of the strip's width (not a sliver), and the recent repositories appear in it

#### Scenario: Chart library missing
- **WHEN** the chart library fails to load
- **THEN** the verdict and table are still shown, with a note that the chart is unavailable, and no blank page

### Requirement: Results table and CSV download
The page SHALL show a table of the fetched repositories with the CLI's columns (`#`, `Repository`, `Stars`, `Last Push`, `Language`, `Bucket`), with `Last Push` as the UTC date of `pushed_at` (as the CLI does, regardless of the browser's time zone). It SHALL offer a download of the same rows as a CSV with the CLI's CSV columns (the table columns plus `URL`), an empty `Language` when GitHub reports none, and a filename following the CLI's rule (`<slug>-report.csv`, with filename-unsafe characters replaced and `search-report.csv` as the fallback).

#### Scenario: Download CSV
- **WHEN** the user searches for `c++/qt` and clicks Download CSV
- **THEN** the browser saves `c++-qt-report.csv` containing the header row and one row per fetched repository, in table order

### Requirement: Search states
The page SHALL show a plain-language message for each of these states, never a blank page or an error visible only in the browser console:
- loading while the request is in progress;
- empty input: an empty or whitespace-only keyword SHALL NOT be sent;
- zero results: `0 repos found`;
- incomplete results: when GitHub's response has `incomplete_results: true`, a warning that the results may be incomplete, shown together with the results;
- rate-limited: detected only on a non-OK response, with exactly the CLI's rule: any HTTP 429, or HTTP 403 with `X-RateLimit-Remaining: 0` or a `Retry-After` header (any other status, e.g. 422, is never a rate limit). The page SHALL show a static message with the clock time after which searching works again, computed from `Retry-After` when it is a whole number of seconds, otherwise from `X-RateLimit-Reset`; when neither is present it SHALL say GitHub gave no reset time and SHALL NOT invent one. There is no live countdown and no automatic retry; the search button stays usable;
- offline or unreachable: a message that GitHub could not be reached;
- any other error response (for example HTTP 422): a message naming the HTTP status;
- unexpected response: a successful response whose body is not valid JSON, or lacks `total_count`, `items` or `incomplete_results`, or contains an item missing `full_name`, `html_url`, `stargazers_count`, `pushed_at` or the `language` key, or whose `pushed_at` is not a valid timestamp, SHALL show a message that GitHub sent a response RepoScout doesn't understand (as the CLI does), instead of staying on the loading state.
A successful response SHALL always be shown as results, whatever its rate-limit headers say. The page SHALL always show the outcome of the most recently submitted search: a response to an earlier search that arrives later SHALL be ignored (a new search replaces one still in progress).

#### Scenario: Secondary rate limit
- **WHEN** GitHub answers HTTP 403 with `Retry-After: 42` and `X-RateLimit-Remaining: 7`
- **THEN** the page shows a rate-limit message saying to try again after the clock time 42 seconds from now

#### Scenario: Last allowed search
- **WHEN** GitHub answers HTTP 200 with results and `X-RateLimit-Remaining: 0`
- **THEN** the page shows the results normally

#### Scenario: Older answer arrives last
- **WHEN** the user searches `react` and then `vue` before the first answer arrives, and GitHub answers `vue` first and `react` second
- **THEN** the page keeps showing the `vue` results and ignores the late `react` answer

#### Scenario: Garbage success response
- **WHEN** a network login page answers HTTP 200 with an HTML page instead of GitHub's JSON
- **THEN** the page shows that GitHub sent a response RepoScout doesn't understand, and does not stay on "loading"

#### Scenario: No reset time given
- **WHEN** GitHub answers HTTP 429 with no `Retry-After` and no `X-RateLimit-Reset`
- **THEN** the page says it is rate-limited and that GitHub gave no reset time, without inventing a time

### Requirement: Browser cache
The page SHALL cache each search's fetched data in browser storage for 24 hours, keyed by the keyword normalized like the CLI's cache key (trimmed, internal whitespace collapsed, case-folded), and SHALL serve a repeat search within 24 hours from the cache without calling GitHub. The cached entry SHALL record whether the results were incomplete, so a cache hit shows the same warning; an entry without that record SHALL be treated as a miss. If browser storage is unavailable, the page SHALL still work, without caching.

#### Scenario: Repeat search
- **WHEN** the user searches `Expense   Tracker` within 24 hours of searching `expense tracker`
- **THEN** the results are shown from the cache, with no request to GitHub

#### Scenario: Storage blocked
- **WHEN** the browser refuses access to local storage
- **THEN** searches still work, each one calling GitHub

### Requirement: Rules parity with the CLI
The bucketing, verdict wording, relative-time rounding, keyword normalization, CSV filename and CSV row rules SHALL be checked against one shared test fixture by both the Python test suite and a JavaScript test run, so that a rule changed in only one language makes a test fail. The fixture SHALL include at least: bucket boundary cases (89, 90, 364, 365 days), verdict cases for both wordings, for zero results and for an incomplete result (30 fetched of 60 reported), relative-time cases across every unit, a non-ASCII keyword, a keyword with filename-unsafe characters, a repository with no language, a `pushed_at` at 23:30 UTC, and rate-limit cases (a 429 with no headers is limited; a 422 with `X-RateLimit-Remaining: 0` is not; a non-numeric `Retry-After` falls back to `X-RateLimit-Reset`). Parity SHALL be checked with recorded inputs and a fixed "now", not by comparing two live searches. The fixture SHALL be fixed reference data, edited by hand on purpose, not regenerated from either implementation. Keyword normalization parity is claimed for the fixture's cases (ASCII, Hungarian, `ß`); rarer Unicode case-folding or whitespace characters may differ from Python.

#### Scenario: A rule drifts
- **WHEN** the active threshold is changed in the JavaScript rules but not in the Python package (or the reverse)
- **THEN** the fixture test for that language fails

### Requirement: Usable at phone width
The page SHALL be usable on a phone-sized screen (360 px wide): the sections stack vertically, nothing requires horizontal page scrolling except the table itself, the table either scrolls sideways within its own area or hides its less important columns (`Language`, `Last Push`), and the strip is tall enough for its dots to remain distinguishable.

#### Scenario: Phone viewport
- **WHEN** the page is shown at 360 px width after a search
- **THEN** the search box, verdict, strip and table are all reachable by vertical scrolling, and the page itself does not scroll sideways
