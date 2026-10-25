# Spec Delta

## MODIFIED Requirements

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
