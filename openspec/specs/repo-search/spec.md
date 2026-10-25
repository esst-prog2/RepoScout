# repo-search Specification

## Purpose
Given a keyword, search GitHub for matching repositories, rank and classify them by recent activity, and present the results as a terminal summary and a CSV export.

## Requirements

### Requirement: Keyword search against GitHub
The system SHALL search GitHub's repository Search API for a given keyword and retrieve the 50 best-matching repositories according to GitHub's own relevance ranking ("best match"), not the 50 most-starred, using data already present in the search response (no separate per-repository follow-up call for stars, last-push time, or primary language). The keyword SHALL be passed to GitHub unchanged, so GitHub's own search syntax (a quoted exact phrase, qualifiers such as `language:python`) works as GitHub defines it. The fetched repositories are then displayed ranked by stars (see "Terminal results table").

#### Scenario: Search returns matches
- **WHEN** a user runs `reposcout search "<keyword>"` for a keyword with matching repositories
- **THEN** the system fetches up to 50 repositories from GitHub's Search API, selected by GitHub's relevance ranking rather than by stars, using only the search response's own fields (stars, `pushed_at`, language)

#### Scenario: Search returns zero matches
- **WHEN** a user runs `reposcout search "<keyword>"` for a keyword with no matching repositories
- **THEN** the system reports "0 repos found" in the terminal and writes a CSV file containing only the header row, with no error raised

#### Scenario: Popular but off-topic matches are not preferred
- **WHEN** a search has more than 50 matches, and some matching repositories contain the keyword's words only scattered through a long description
- **THEN** the system does not ask GitHub to rank by stars, so those repositories are not selected merely for being popular

### Requirement: Activity bucketing
The system SHALL classify each fetched repository into exactly one activity bucket based on the recency of its last push: `active` (pushed within the last 3 months), `slowing` (pushed 3-12 months ago), or `stale` (pushed 12 or more months ago).

#### Scenario: Repository with a recent push
- **WHEN** a repository's last push was less than 3 months ago
- **THEN** the system labels it `active`

#### Scenario: Repository with no recent commits
- **WHEN** a repository's last push was 12 or more months ago
- **THEN** the system labels it `stale`, not `active`

### Requirement: Terminal results table
The system SHALL print a terminal table of the fetched, ranked repositories with columns for rank, repository name, stars, last push date (labeled "Last Push" — this is `pushed_at`, not a verified last-commit date), primary language, and activity bucket, sorted by stars descending. The repository URL SHALL NOT appear in the terminal table.

#### Scenario: Table reflects fetched results
- **WHEN** a search completes with at least one matching repository
- **THEN** the terminal table lists each fetched repository with its rank, name, stars, last push date, language, and activity bucket, ordered by stars descending

### Requirement: One-line verdict summary
The system SHALL print a one-line verdict after the table, stating how many repositories were found, how many fall in the `active` bucket, and the most recently pushed repository among the fetched results, phrased as a relative time (e.g. "2 weeks ago"). Bucket counts in the verdict SHALL only ever reflect the repositories actually fetched, never an estimate of the full match population. The relative time SHALL always be rounded down, never up, to whole units of the largest fitting size: "just now" under a minute, minutes under an hour, hours under a day, days under 14 days, weeks under 90 days, months (of 30 days) under 365 days, and years plus any remaining whole months (at most 11) from 365 days on. A count of 1 SHALL use the singular unit (e.g. "1 day ago"), and a push time slightly in the future (clock skew) SHALL be shown as "just now".

#### Scenario: Total matches within the fetched limit
- **WHEN** GitHub reports 50 or fewer total matching repositories for the keyword
- **THEN** the verdict states the exact total count of repositories found (e.g. "42 repos found, 6 active in the last 3 months — most recent entrant pushed 2 weeks ago")

#### Scenario: Total matches exceed the fetched limit
- **WHEN** GitHub reports more than 50 total matching repositories for the keyword
- **THEN** the verdict makes explicit that only the 50 best-matching repositories were fetched and evaluated (e.g. "Showing the 50 best-matching of 3241 repos, 12 active among them — …"), rather than implying the 50 shown is the full result set or the 50 most popular

#### Scenario: Relative time is rounded down, not to the nearest unit
- **WHEN** the most recently pushed repository was pushed 16 days ago
- **THEN** the verdict says it was pushed "2 weeks ago", not "a month ago"

#### Scenario: An active repository is never described as 3 months old
- **WHEN** the most recently pushed repository was pushed 89 days ago (inside the 90-day active window)
- **THEN** the verdict says "12 weeks ago", and a repository pushed 100 days ago is described as "3 months ago"

#### Scenario: Over a year
- **WHEN** the most recently pushed repository was pushed 400 days ago
- **THEN** the verdict says "1 year, 1 month ago"

#### Scenario: Leftover months never reach 12
- **WHEN** the most recently pushed repository was pushed 729 days ago
- **THEN** the verdict says "1 year, 11 months ago", not "1 year, 12 months ago"

### Requirement: CSV export
The system SHALL export the full ranked, bucketed result set to a CSV file in the current working directory, with the same columns as the terminal table plus the repository URL. The filename SHALL be derived from the normalized search keyword (lowercased, whitespace collapsed to single hyphens) with a `-report.csv` suffix. Characters that are invalid in filenames on common operating systems (`<`, `>`, `:`, `"`, `/`, `\`, `|`, `?`, `*`, and control characters) SHALL NOT appear in the filename: each run of such characters and/or whitespace SHALL become a single hyphen, repeated hyphens SHALL collapse to one, and leading or trailing hyphens and dots SHALL be removed. Other characters, including non-ASCII letters, SHALL be kept. If nothing remains, the filename SHALL be `search-report.csv`. The file SHALL always be written directly in the current working directory, never in a subdirectory.

#### Scenario: Export on a successful search
- **WHEN** a search for `"expense tracker"` completes
- **THEN** the system writes `expense-tracker-report.csv` in the current working directory containing every fetched repository, in the same rank order as the terminal table, plus a URL column

#### Scenario: Export on a zero-match search
- **WHEN** a search returns zero matching repositories
- **THEN** the system still writes a CSV file containing only the header row

#### Scenario: Filename collision between distinct keywords
- **WHEN** two distinct searches (e.g. `"expense tracker"` and `"expense-tracker"`) normalize to the same CSV filename
- **THEN** the later export silently overwrites the earlier file, without prompting or erroring

#### Scenario: Keyword containing filename-unsafe characters
- **WHEN** a search for `"c++/qt"` completes
- **THEN** the system writes `c++-qt-report.csv` in the current working directory, without crashing and without creating a subdirectory

#### Scenario: Keyword containing a colon
- **WHEN** a search for `"c#: tools"` completes
- **THEN** the system writes a visible file named `c#-tools-report.csv` in the current working directory

#### Scenario: Keyword with no usable filename characters
- **WHEN** a search for `"???"` completes
- **THEN** the system writes `search-report.csv` in the current working directory

### Requirement: Incomplete search results are flagged
When GitHub's search response reports `incomplete_results: true` (its search timed out before finishing), the system SHALL print a warning after the verdict that the results may be incomplete. The flag SHALL be stored with the cache entry so the warning also appears when the same results are later served from the cache.

#### Scenario: GitHub reports incomplete results
- **WHEN** a search response has `incomplete_results: true`
- **THEN** the system prints the table and verdict as usual, followed by a warning that the results may be incomplete

#### Scenario: Incomplete results served from cache
- **WHEN** a search whose fetched results were flagged incomplete is repeated within the cache window
- **THEN** the cached results are shown with the same incomplete-results warning
