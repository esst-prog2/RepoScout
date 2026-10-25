# Spec Delta

## MODIFIED Requirements

### Requirement: Cache hit avoids GitHub API calls
The system SHALL serve a search from the local cache, making zero GitHub API calls, when a valid (unexpired, uncorrupted) cache entry exists for the normalized keyword and less than 24 hours have passed since it was fetched. A cache entry that does not record that its repositories were selected by GitHub's relevance ranking (i.e. one written before that selection rule) SHALL NOT be served; it SHALL be treated as a cache miss, refetched, and overwritten.

#### Scenario: Repeat search within the cache window
- **WHEN** a user runs the same search twice within 24 hours, without passing `--refresh`
- **THEN** the second run serves results from the cache and makes zero GitHub API calls, verifiable via a logged API call count

#### Scenario: Repeat search after the cache window expires
- **WHEN** a user runs the same search again after 24 hours have passed since it was last fetched
- **THEN** the system re-fetches from GitHub and overwrites the cache entry

#### Scenario: Entry fetched under the old star-based selection
- **WHEN** an unexpired cache entry exists for the keyword but was written before results were selected by relevance
- **THEN** the system does not serve it, fetches fresh results from GitHub, and overwrites the entry
