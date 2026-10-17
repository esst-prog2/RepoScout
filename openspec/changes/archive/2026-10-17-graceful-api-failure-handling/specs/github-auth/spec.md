# Spec Delta

## MODIFIED Requirements

### Requirement: Graceful rate-limit-exceeded handling
The system SHALL catch any GitHub rate-limit-exceeded response (authenticated or not) and report a clear message that includes when the limit resets, instead of surfacing a raw error or crashing mid-run. The process SHALL exit with code `2` in this case, distinct from the exit code used for other errors.

#### Scenario: Authenticated rate limit is exceeded
- **WHEN** a request fails because the authenticated rate limit has been exhausted
- **THEN** the system reports a clear message stating the limit was hit and when it resets, without a raw stack trace or crash, and the process exits with code `2`

#### Scenario: Unauthenticated rate limit is exceeded
- **WHEN** a request fails because the unauthenticated rate limit has been exhausted
- **THEN** the system reports a clear message, without a raw stack trace or crash, and the process exits with code `2`

## ADDED Requirements

### Requirement: Graceful network-failure handling
The system SHALL catch a network failure (connection error or timeout) while contacting GitHub's API and report a clear message that GitHub could not be reached, instead of surfacing a raw error or crashing mid-run. The process SHALL exit with code `3`, distinct from both the rate-limit exit code and the exit code used for other errors.

#### Scenario: GitHub is unreachable
- **WHEN** a request to GitHub's API fails due to a connection error (e.g. no network, DNS failure)
- **THEN** the system reports a clear message that GitHub could not be reached, without a raw stack trace or crash, and the process exits with code `3`

#### Scenario: Request to GitHub times out
- **WHEN** a request to GitHub's API fails due to a timeout
- **THEN** the system reports a clear message that GitHub could not be reached, without a raw stack trace or crash, and the process exits with code `3`
