# Spec Delta

## Purpose

A static, tokenless web page that searches GitHub by keyword with the same rules as the RepoScout CLI and shows a topic's health at a glance as a heartbeat strip, plus the verdict, a ranked table and a CSV download.

## ADDED Requirements

### Requirement: Static, tokenless page
The web interface SHALL consist only of static files (HTML, CSS, JavaScript and vendored libraries) that work when served by any static file server, with no build step and no server-side code. The page SHALL call GitHub's repository search API directly from the browser and SHALL NOT use, ask for, or contain a GitHub token. Third-party libraries SHALL be loaded from files inside the project at pinned versions, not from a CDN.

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
The page SHALL show a one-line verdict with the same wording rules as the CLI: `<N> repos found, <A> active in the last <window> — most recent entrant pushed <time>` when GitHub reports 50 or fewer matches, and `Showing the <n> best-matching of <N> repos, <A> active among them — most recent entrant pushed <time>` otherwise, and `0 repos found` when there are none. The relative time SHALL be rounded down exactly as the CLI does it.

#### Scenario: More than 50 matches
- **WHEN** GitHub reports 244,832 matches and 50 are fetched, 10 of them active
- **THEN** the verdict begins `Showing the 50 best-matching of 244832 repos, 10 active among them`

#### Scenario: Relative time rounded down
- **WHEN** the most recently pushed repository was pushed 16 days ago
- **THEN** the verdict ends `pushed 2 weeks ago`

### Requirement: Heartbeat strip
The page SHALL draw one dot per fetched repository on a horizontal axis of time since last push, divided into three zones of readable width, stale (left), slowing (middle) and active (right). Within each zone the position SHALL be proportional to days since last push over that zone's range (active 0-90 days, slowing 90-365 days, stale 365 days to 5 years); repositories pushed more than 5 years ago SHALL be placed at the left edge, which is labelled as 5+ years. Dot area SHALL grow with stars on a square-root (or capped) scale, dot shade SHALL show the bucket, and overlapping dots SHALL be separated vertically. Each dot SHALL show the repository name, stars and last push date on hover or tap. The page SHALL state in one line that "last push" is GitHub's `pushed_at`, not a verified last commit. If the chart library is not available, the page SHALL still show the verdict and table, with a plain note that the chart is unavailable.

#### Scenario: Active repositories have room
- **WHEN** a search returns repositories pushed across ten years, some within the last 90 days
- **THEN** the active zone takes up a readable share of the strip's width (not a sliver), and the recent repositories appear in it

#### Scenario: Chart library missing
- **WHEN** the chart library fails to load
- **THEN** the verdict and table are still shown, with a note that the chart is unavailable, and no blank page

### Requirement: Results table and CSV download
The page SHALL show a table of the fetched repositories with the CLI's columns (`#`, `Repository`, `Stars`, `Last Push`, `Language`, `Bucket`), with `Last Push` as a date. It SHALL offer a download of the same rows as a CSV with the CLI's CSV columns (the table columns plus `URL`), an empty `Language` when GitHub reports none, and a filename following the CLI's rule (`<slug>-report.csv`, with filename-unsafe characters replaced and `search-report.csv` as the fallback).

#### Scenario: Download CSV
- **WHEN** the user searches for `c++/qt` and clicks Download CSV
- **THEN** the browser saves `c++-qt-report.csv` containing the header row and one row per fetched repository, in table order

### Requirement: Search states
The page SHALL show a plain-language message for each of these states, never a blank page or an error visible only in the browser console:
- loading while the request is in progress;
- empty input: an empty or whitespace-only keyword SHALL NOT be sent;
- zero results: `0 repos found`;
- incomplete results: when GitHub's response has `incomplete_results: true`, a warning that the results may be incomplete, shown together with the results;
- rate-limited: detected only on a non-OK response, as either `X-RateLimit-Remaining: 0` or HTTP 403/429 with a `Retry-After` header. The page SHALL count down from `Retry-After` when present, otherwise from `X-RateLimit-Reset`; when neither is present it SHALL say GitHub gave no reset time and SHALL NOT invent one. When the countdown ends, the search button SHALL be usable again, without retrying automatically;
- offline or unreachable: a message that GitHub could not be reached;
- any other error response (for example HTTP 422): a message naming the HTTP status.
A successful response SHALL always be shown as results, whatever its rate-limit headers say.

#### Scenario: Secondary rate limit
- **WHEN** GitHub answers HTTP 403 with `Retry-After: 42` and `X-RateLimit-Remaining: 7`
- **THEN** the page shows a rate-limit message counting down from 42 seconds

#### Scenario: Last allowed search
- **WHEN** GitHub answers HTTP 200 with results and `X-RateLimit-Remaining: 0`
- **THEN** the page shows the results normally

#### Scenario: No reset time given
- **WHEN** GitHub answers HTTP 429 with no `Retry-After` and no `X-RateLimit-Reset`
- **THEN** the page says it is rate-limited and that GitHub gave no reset time, with no countdown

### Requirement: Browser cache
The page SHALL cache each search's fetched data in browser storage for 24 hours, keyed by the keyword normalized like the CLI's cache key (trimmed, internal whitespace collapsed, case-folded), and SHALL serve a repeat search within 24 hours from the cache without calling GitHub. The cached entry SHALL record whether the results were incomplete, so a cache hit shows the same warning; an entry without that record SHALL be treated as a miss. If browser storage is unavailable, the page SHALL still work, without caching.

#### Scenario: Repeat search
- **WHEN** the user searches `Expense   Tracker` within 24 hours of searching `expense tracker`
- **THEN** the results are shown from the cache, with no request to GitHub

#### Scenario: Storage blocked
- **WHEN** the browser refuses access to local storage
- **THEN** searches still work, each one calling GitHub

### Requirement: Rules parity with the CLI
The bucketing, verdict wording, relative-time rounding, keyword normalization, CSV filename and CSV row rules SHALL be checked against one shared test fixture by both the Python test suite and a JavaScript test run, so that a rule changed in only one language makes a test fail. The fixture SHALL include at least: bucket boundary cases (89, 90, 364, 365 days), verdict cases for both wordings and for zero results, relative-time cases across every unit, a non-ASCII keyword, a keyword with filename-unsafe characters, and a repository with no language. Parity SHALL be checked with recorded inputs and a fixed "now", not by comparing two live searches.

#### Scenario: A rule drifts
- **WHEN** the active threshold is changed in the JavaScript rules but not in the Python package (or the reverse)
- **THEN** the fixture test for that language fails

### Requirement: Usable at phone width
The page SHALL be usable on a phone-sized screen (360 px wide): the sections stack vertically, nothing requires horizontal page scrolling except the table itself, the table either scrolls sideways within its own area or hides its less important columns (`Language`, `Last Push`), and the strip is tall enough for its dots to remain distinguishable.

#### Scenario: Phone viewport
- **WHEN** the page is shown at 360 px width after a search
- **THEN** the search box, verdict, strip and table are all reachable by vertical scrolling, and the page itself does not scroll sideways
