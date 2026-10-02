# Spec Delta

## Purpose

Given a keyword, search GitHub for matching repositories, rank and classify them by recent activity, and present the results as a terminal summary and a CSV export.

## ADDED Requirements

### Requirement: Keyword search against GitHub
The system SHALL search GitHub's repository Search API for a given keyword and retrieve the top 50 matching repositories ordered by star count, using data already present in the search response (no separate per-repository follow-up call for stars, last-push time, or primary language).

#### Scenario: Search returns matches
- **WHEN** a user runs `reposcout search "<keyword>"` for a keyword with matching repositories
- **THEN** the system fetches up to 50 repositories from GitHub's Search API, ordered by stars descending, using only the search response's own fields (stars, `pushed_at`, language)

#### Scenario: Search returns zero matches
- **WHEN** a user runs `reposcout search "<keyword>"` for a keyword with no matching repositories
- **THEN** the system reports "0 repos found" in the terminal and writes a CSV file containing only the header row, with no error raised

### Requirement: Activity bucketing
The system SHALL classify each fetched repository into exactly one activity bucket based on the recency of its last push: `active` (pushed within the last 3 months), `slowing` (pushed 3-12 months ago), or `stale` (pushed 12 or more months ago).

#### Scenario: Repository with a recent push
- **WHEN** a repository's last push was less than 3 months ago
- **THEN** the system labels it `active`

#### Scenario: Repository with no recent commits
- **WHEN** a repository's last push was 12 or more months ago
- **THEN** the system labels it `stale`, not `active`

### Requirement: Terminal results table
The system SHALL print a terminal table of the fetched, ranked repositories with columns for rank, repository name, stars, last commit date, primary language, and activity bucket, sorted by stars descending. The repository URL SHALL NOT appear in the terminal table.

#### Scenario: Table reflects fetched results
- **WHEN** a search completes with at least one matching repository
- **THEN** the terminal table lists each fetched repository with its rank, name, stars, last commit date, language, and activity bucket, ordered by stars descending

### Requirement: One-line verdict summary
The system SHALL print a one-line verdict after the table, stating how many repositories were found, how many fall in the `active` bucket, and the most recently pushed repository among the fetched results, phrased as a relative time (e.g. "2 weeks ago"). Bucket counts in the verdict SHALL only ever reflect the repositories actually fetched, never an estimate of the full match population.

#### Scenario: Total matches within the fetched limit
- **WHEN** GitHub reports 50 or fewer total matching repositories for the keyword
- **THEN** the verdict states the exact total count of repositories found (e.g. "42 repos found, 6 active in the last 3 months — most recent entrant pushed 2 weeks ago")

#### Scenario: Total matches exceed the fetched limit
- **WHEN** GitHub reports more than 50 total matching repositories for the keyword
- **THEN** the verdict makes explicit that only the top 50 (by stars) were fetched and evaluated, rather than implying the 50 shown is the full result set

### Requirement: CSV export
The system SHALL export the full ranked, bucketed result set to a CSV file in the current working directory, with the same columns as the terminal table plus the repository URL. The filename SHALL be derived from the normalized search keyword (lowercased, whitespace collapsed to single hyphens) with a `-report.csv` suffix.

#### Scenario: Export on a successful search
- **WHEN** a search for `"expense tracker"` completes
- **THEN** the system writes `expense-tracker-report.csv` in the current working directory containing every fetched repository, in the same rank order as the terminal table, plus a URL column

#### Scenario: Export on a zero-match search
- **WHEN** a search returns zero matching repositories
- **THEN** the system still writes a CSV file containing only the header row

#### Scenario: Filename collision between distinct keywords
- **WHEN** two distinct searches (e.g. `"expense tracker"` and `"expense-tracker"`) normalize to the same CSV filename
- **THEN** the later export silently overwrites the earlier file, without prompting or erroring
