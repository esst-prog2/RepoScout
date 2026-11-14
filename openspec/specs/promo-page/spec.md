# promo-page Specification

## Purpose
A public promo page for RepoScout that tells a visitor what the program is for, who it is for and how to try it, using only evidence from RepoScout's own recorded searches, and links straight into the live app and the code.

## Requirements

### Requirement: The three answers on one page
The promo page SHALL answer, each in its own visible section, what RepoScout is for, who it is for, and how to try it. Trying it SHALL be offered two ways: in the browser (the live app, no account and no token) and on the command line (the Python tool, with the clone-and-install commands and Python 3.10 or newer). Every text SHALL be in English.

#### Scenario: A visitor reads the page top to bottom
- **WHEN** a visitor opens the promo page
- **THEN** they find a hero stating what RepoScout does, a section for people about to build, a section explaining how to read a result, a "Try it" section with a browser path and a command-line block, and an "Honest limits" section

#### Scenario: Command-line block is copyable
- **WHEN** a visitor selects the command-line block
- **THEN** there is one block for Windows (PowerShell) and one for macOS and Linux, and each copies as plain text containing the commands to clone the repository, create a virtual environment, install with `pip install .` and run `reposcout search "project management software"`; the Windows block works without running an activation script, which PowerShell blocks by default

### Requirement: Links into the app, the code and the manual
The promo page SHALL show an "Open RepoScout" action that opens the live app, and a "View the code on GitHub" action that opens `https://github.com/esst-prog2/RepoScout`, both in the hero and again in "Try it". It SHALL link to the user manual on GitHub. "Open RepoScout" SHALL be the page's single primary action.

#### Scenario: Open the app from the hero
- **WHEN** a visitor activates "Open RepoScout" on the published promo page
- **THEN** the RepoScout search page opens at the site's `app/` address and can run a search

#### Scenario: Keyboard only
- **WHEN** a visitor moves through the page with the Tab key
- **THEN** every link and button receives a visible focus indicator, in reading order

### Requirement: Evidence only, from the 26 October searches
The promo page SHALL make no claim that RepoScout's own recorded output does not show: no testimonials, user counts, star-count badges, logos, superlatives or exclamation marks. Every number on the page SHALL come from the 26 October 2026 screenshots in `docs/screenshots/` (and match README §1 where it quotes the same figure) or from the HW4 spike (5 of 50 repositories change activity group). The page SHALL say that its example searches are from 26 October 2026. Verdict sentences SHALL be quoted exactly as RepoScout printed them. The original screenshots SHALL NOT be retaken or edited; the page may use cropped copies of them.

#### Scenario: Alive vs. graveyard hero
- **WHEN** a visitor views the hero
- **THEN** they see the `mcp server` result (37 of the 50 best-matching of 177,486 repositories active) above the `angularjs directive` result (0 of the 50 best-matching of 3,137 active), each with its verdict as text and its heartbeat strip, labelled as two real searches from 26 October 2026

#### Scenario: Numbers stay consistent
- **WHEN** the page's figures are compared with the 26 October screenshots and README §1
- **THEN** every figure matches (14,067 repos and 10 active for `project management software`; 37 of 50 and 0 of 50 for the two hero searches)

### Requirement: Honest limits stated
The promo page SHALL state that RepoScout reads the 50 best-matching repositories rather than every match, that "active" means pushed in the last 3 months and that GitHub's push time is not always the latest commit, that keyword search matches words rather than meaning, and that its numbers are a snapshot.

#### Scenario: Limits section present
- **WHEN** a visitor reaches "Honest limits"
- **THEN** all four limits are listed in plain words

### Requirement: Readable without the images and at phone width
Every image on the promo page SHALL have alternative text that states what it shows, including the verdict it illustrates. The page SHALL be usable at 360 px wide with no sideways page scrolling; a command line longer than the screen SHALL scroll inside its own block. Any entrance motion SHALL leave content visible by default and SHALL NOT run when the visitor's system asks for reduced motion.

#### Scenario: Images fail to load
- **WHEN** the images do not load
- **THEN** the verdict text and alt texts still convey that one topic is alive and the other is not

#### Scenario: Phone width
- **WHEN** the page is viewed 360 px wide
- **THEN** content is a single column, nothing overflows the page sideways, and both actions remain reachable

#### Scenario: Reduced motion
- **WHEN** the visitor's system requests reduced motion
- **THEN** the page shows its final state with no reveal animation

### Requirement: Nothing personal published
The promo page SHALL NOT contain personal data: no real names, photos of faces, e-mail addresses, local file paths or private context, in its text or in its images. GitHub account names that can be people's names (the `owner/` part of a repository name) SHALL NOT be readable in any image on the page; where a screenshot shows them, the promo page SHALL use a copy with that part blurred, leaving the original screenshot untouched. The footer SHALL name the course (Advanced Programming at ELTE, 2026) and link the public repository.

#### Scenario: Personal-data check
- **WHEN** the published promo page's text and source are searched for e-mail addresses and local paths (`C:\`, `/home/`, `/Users/`)
- **THEN** nothing is found

#### Scenario: Table image without account names
- **WHEN** a visitor looks at the ranked-table image in "One search, four answers"
- **THEN** the repository names, stars, dates, languages, buckets and the Download CSV button are readable, and the account part before each `/` is blurred beyond reading
