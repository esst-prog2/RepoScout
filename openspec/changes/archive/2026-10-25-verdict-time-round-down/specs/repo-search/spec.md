# Spec Delta

## MODIFIED Requirements

### Requirement: One-line verdict summary
The system SHALL print a one-line verdict after the table, stating how many repositories were found, how many fall in the `active` bucket, and the most recently pushed repository among the fetched results, phrased as a relative time (e.g. "2 weeks ago"). Bucket counts in the verdict SHALL only ever reflect the repositories actually fetched, never an estimate of the full match population. The relative time SHALL always be rounded down, never up, to whole units of the largest fitting size: "just now" under a minute, minutes under an hour, hours under a day, days under 14 days, weeks under 90 days, months (of 30 days) under 365 days, and years plus any remaining whole months (at most 11) from 365 days on. A count of 1 SHALL use the singular unit (e.g. "1 day ago"), and a push time slightly in the future (clock skew) SHALL be shown as "just now".

#### Scenario: Total matches within the fetched limit
- **WHEN** GitHub reports 50 or fewer total matching repositories for the keyword
- **THEN** the verdict states the exact total count of repositories found (e.g. "42 repos found, 6 active in the last 3 months — most recent entrant pushed 2 weeks ago")

#### Scenario: Total matches exceed the fetched limit
- **WHEN** GitHub reports more than 50 total matching repositories for the keyword
- **THEN** the verdict makes explicit that only the top 50 (by stars) were fetched and evaluated, rather than implying the 50 shown is the full result set

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
