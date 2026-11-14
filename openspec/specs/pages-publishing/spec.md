# pages-publishing Specification

## Purpose
Publishes RepoScout's promo page and its web app together on GitHub Pages from the course repository, so that only the intended files go online, a visitor never runs mismatched cached files, and the local preview matches what is published.

## Requirements

### Requirement: Published layout
The published site SHALL serve the promo page at its root address and the RepoScout web app under `app/`, together with the images the promo page uses. It SHALL contain nothing else from the repository: no CLI source, tests, planning files, design notes, `.impeccable/` files, logs or configuration. The app's own files SHALL be published unchanged apart from cache-busting suffixes.

#### Scenario: Root and app addresses
- **WHEN** the site is published
- **THEN** `https://esst-prog2.github.io/RepoScout/` shows the promo page and `https://esst-prog2.github.io/RepoScout/app/` shows the working search page

#### Scenario: Only intended files
- **WHEN** the assembled folder is listed
- **THEN** it contains only the promo page and its assets, the `app/` folder (the contents of `site/`) and the promo images, and no file such as `AGENTS.md`, `PRODUCT.md`, `pyproject.toml` or anything from `tests/`, `openspec/`, `reposcout/` or `.impeccable/`

#### Scenario: No personal data in any published text file
- **WHEN** every text file in the assembled folder (HTML, CSS, JavaScript, licence files) is searched for e-mail addresses and local paths (`C:\`, `/home/`, `/Users/`)
- **THEN** nothing is found

### Requirement: One assembly for preview and publishing
Assembling the published folder SHALL be done by one script in the repository that runs with Python's standard library only. Running it locally SHALL produce the same folder the deploy uses, and it SHALL offer serving that folder for a local preview. The app's source in `site/` SHALL keep working unchanged when served on its own (`python -m http.server` in `site/`).

#### Scenario: Local preview matches the published site
- **WHEN** the user assembles and previews the site locally
- **THEN** the promo page opens at the preview's root and its "Open RepoScout" action opens the app under `app/`, as on GitHub Pages

#### Scenario: Sources untouched
- **WHEN** the assembly runs
- **THEN** no file under `site/` or `promo/` is modified

### Requirement: Cache-busting of published files
In the published copies only, every link from an HTML page to a stylesheet or script, and the app's module import of its rules file, SHALL carry a `?v=<version>` suffix that changes with every deployed commit, so a browser cannot combine an older cached file with a newer one. Font files SHALL NOT be suffixed. The assembly SHALL fail if any such link or the rules import is left without the suffix.

#### Scenario: New deploy, returning visitor
- **WHEN** a visitor who loaded the app before a deploy loads it again after the deploy
- **THEN** the browser requests the new `app.js` and the new `rules.js` (their URLs changed), never an old `rules.js` with a new `app.js`

#### Scenario: Missed link fails the build
- **WHEN** a stylesheet or script link, or the rules import, would be published without the suffix
- **THEN** the assembly stops with an error and nothing is deployed

### Requirement: Automatic deploy from main
The site SHALL be deployed to GitHub Pages by a GitHub Actions workflow in the repository on every push to `main` and on manual start. The workflow SHALL run the Python and JavaScript test suites first and SHALL NOT deploy if any test fails. It SHALL use GitHub's official Pages actions pinned to exact versions and only the permissions Pages deployment needs.

#### Scenario: Merge to main
- **WHEN** a pull request is merged into `main` and the tests pass
- **THEN** the workflow publishes the newly assembled site and the live address shows it

#### Scenario: Failing test
- **WHEN** a test fails in the workflow
- **THEN** nothing is deployed and the previously published site stays online
