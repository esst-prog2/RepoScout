# search-cache Specification

## Purpose
Cache GitHub search results per normalized keyword for 24 hours so repeat searches avoid redundant GitHub API calls, while keeping cache entries correctly scoped to distinct queries and resilient to interruption.

## Requirements

### Requirement: Cache key normalization
The system SHALL normalize a search keyword into a cache key by casefolding it, trimming leading/trailing whitespace, and collapsing runs of internal whitespace to a single space. Hyphens SHALL NOT be treated as equivalent to whitespace — a query containing a hyphen and a query containing a space in the same position SHALL be treated as distinct cache entries.

#### Scenario: Case and whitespace variants share a cache entry
- **WHEN** a user searches `"expense tracker"` and later searches `"Expense   Tracker"`
- **THEN** both searches resolve to the same cache entry

#### Scenario: Hyphenated and spaced variants stay distinct
- **WHEN** a user searches `"expense tracker"` and separately searches `"expense-tracker"`
- **THEN** the two searches are treated as distinct cache entries, each independently fetched and cached

### Requirement: Cache hit avoids GitHub API calls
The system SHALL serve a search from the local cache, making zero GitHub API calls, when a valid (unexpired, uncorrupted) cache entry exists for the normalized keyword and less than 24 hours have passed since it was fetched.

#### Scenario: Repeat search within the cache window
- **WHEN** a user runs the same search twice within 24 hours, without passing `--refresh`
- **THEN** the second run serves results from the cache and makes zero GitHub API calls, verifiable via a logged API call count

#### Scenario: Repeat search after the cache window expires
- **WHEN** a user runs the same search again after 24 hours have passed since it was last fetched
- **THEN** the system re-fetches from GitHub and overwrites the cache entry

### Requirement: Cache bypass on demand
The system SHALL support a `--refresh` flag on the search command that skips reading the cache, always fetches fresh results from GitHub, and overwrites the corresponding cache entry with the new results.

#### Scenario: Refresh flag forces a fresh fetch
- **WHEN** a user runs `reposcout search "<keyword>" --refresh`, even with an unexpired cache entry present
- **THEN** the system fetches fresh results from GitHub and overwrites the existing cache entry

### Requirement: Cache storage isolation per query
The system SHALL store each normalized query's cached results in its own file, located in the OS-appropriate user-level cache directory, independent of the directory the command is run from.

#### Scenario: Cache persists across working directories
- **WHEN** a user runs the same search from two different working directories
- **THEN** the second run finds and uses the same cache entry the first run created

### Requirement: Corrupted cache entry self-heals
The system SHALL treat a cache file that cannot be read or parsed as if no cache entry existed, fetching fresh results from GitHub and overwriting the file, rather than raising an error to the user.

#### Scenario: Cache file is unreadable or malformed
- **WHEN** a cache entry's file exists but is not valid, readable cached data
- **THEN** the system silently fetches fresh results from GitHub and overwrites the file, without surfacing an error to the user
