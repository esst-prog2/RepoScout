# Spec Delta

## MODIFIED Requirements

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
