# Spec Delta

## MODIFIED Requirements

### Requirement: Invalid or expired saved token recovery
When a saved token is rejected by GitHub as invalid or expired, the system SHALL inform the user and offer to accept a new token immediately, overwriting the invalid one in local config, rather than requiring manual edits to the config file. When the rejected token came from the `GITHUB_TOKEN` environment variable instead, the system SHALL NOT prompt for a replacement and SHALL NOT write to local config (a saved replacement would be overridden by the environment variable on the next run); it SHALL report that the token in the `GITHUB_TOKEN` environment variable is invalid or expired, tell the user to update or unset that variable, and exit with code `1`.

#### Scenario: Saved token is rejected by GitHub
- **WHEN** a search is attempted using a saved token and GitHub responds that the token is invalid or expired
- **THEN** the system tells the user the saved token is invalid and prompts them to enter a replacement, saving it over the old one if provided

#### Scenario: Environment-variable token is rejected by GitHub
- **WHEN** a search is attempted using a token from the `GITHUB_TOKEN` environment variable and GitHub responds that the token is invalid or expired
- **THEN** the system reports that the token in `GITHUB_TOKEN` is invalid or expired and tells the user to update or unset that variable, without prompting for a replacement, without writing to local config, without a raw stack trace, and the process exits with code `1`
