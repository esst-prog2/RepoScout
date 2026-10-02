# Spec Delta

## Purpose

Acquire a GitHub personal access token from the environment, saved local config, or an interactive prompt as needed, and handle GitHub authentication and rate-limit failures with clear, actionable messages rather than crashes.

## ADDED Requirements

### Requirement: Token resolution order
The system SHALL resolve a GitHub token by checking, in order: the `GITHUB_TOKEN` environment variable, then a token previously saved to local config, then (if neither is present and the user has not previously chosen to skip) an interactive prompt.

#### Scenario: Environment variable takes precedence
- **WHEN** `GITHUB_TOKEN` is set in the environment
- **THEN** the system uses that token and does not read or write the saved config file

#### Scenario: Saved token is used when no environment variable is set
- **WHEN** `GITHUB_TOKEN` is not set but a token was saved from a prior run
- **THEN** the system uses the saved token without prompting

### Requirement: Interactive token prompt
When no token is available from the environment or saved config, and the user has not previously chosen to skip, the system SHALL prompt the user to enter a GitHub token with input masked (not echoed to the terminal or persisted to shell history). If the user enters a token, the system SHALL save it to a local config file for future runs. If the user submits an empty response, the system SHALL proceed without a token and SHALL remember this choice so it does not prompt again on subsequent runs.

#### Scenario: User provides a token at the prompt
- **WHEN** the interactive prompt appears and the user enters a token
- **THEN** the system uses that token for the current search and saves it to local config for future runs

#### Scenario: User skips the prompt
- **WHEN** the interactive prompt appears and the user submits an empty response
- **THEN** the system proceeds using GitHub's unauthenticated rate limits for this run, and does not show the prompt again on later runs

### Requirement: Unauthenticated rate-limit guidance
When a request fails because GitHub's unauthenticated rate limit has been exhausted, the system SHALL report a clear message instructing the user that providing a GitHub token will raise the limit, rather than a generic error or crash.

#### Scenario: Unauthenticated rate limit is exhausted
- **WHEN** a search is attempted without a token and GitHub's unauthenticated rate limit has been reached
- **THEN** the system reports a message telling the user to provide a token to raise the limit, instead of crashing

### Requirement: Invalid or expired saved token recovery
When a saved token is rejected by GitHub as invalid or expired, the system SHALL inform the user and offer to accept a new token immediately, overwriting the invalid one in local config, rather than requiring manual edits to the config file.

#### Scenario: Saved token is rejected by GitHub
- **WHEN** a search is attempted using a saved token and GitHub responds that the token is invalid or expired
- **THEN** the system tells the user the saved token is invalid and prompts them to enter a replacement, saving it over the old one if provided

### Requirement: Graceful rate-limit-exceeded handling
The system SHALL catch any GitHub rate-limit-exceeded response (authenticated or not) and report a clear message that includes when the limit resets, instead of surfacing a raw error or crashing mid-run.

#### Scenario: Authenticated rate limit is exceeded
- **WHEN** a request fails because the authenticated rate limit has been exhausted
- **THEN** the system reports a clear message stating the limit was hit and when it resets, without a raw stack trace or crash
