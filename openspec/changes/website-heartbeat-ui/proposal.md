# Proposal

## Why

Session 7 (halftime) asks finished projects to "make it bigger", and the slides name a real interface as one of the options. RepoScout's CLI is complete and tested, but its output is a terminal table. The final demo (1 or 8 December) is a five-minute presentation with screenshots, so the result has to read instantly on a slide. A web page can show a whole topic's health in one picture, the "heartbeat strip", which no terminal table can. The design was explored with `/opsx:explore` and gstack `/office-hours`, passed an independent spec review, and was approved by the user: `docs/designs/reposcout-website.md`.

## What Changes

- **New: a static web page in `site/`** (HTML + CSS + JavaScript, no build step, no server code), run locally with `python -m http.server` from `site/`. The browser calls GitHub's search API directly, **without a token**. The CLI and its token handling are unchanged.
- The page follows the CLI's rules: GitHub's relevance picks the 50 repos, the display is ranked by stars, the active/slowing/stale thresholds are the same, and the verdict wording and round-down relative time are the same.
- **The heartbeat strip (hero):** one dot per repo on a piecewise "days since last push" axis (stale | slowing | active zones of readable width), dot size by stars, shade by bucket, tooltips. Uses Observable Plot and d3, **vendored** at pinned versions into `site/vendor/` (no CDN, works offline). If the chart library is missing, the verdict and table still render.
- A results table (same columns as the CLI) and a **Download CSV** button that builds the file in the browser, with the CLI's columns and filename rule.
- Plain-language states: loading, empty input, zero results, incomplete results, rate-limited (countdown when GitHub gives a time, honest "unknown" otherwise), offline, other errors.
- A 24-hour browser cache (`localStorage`) keyed like the CLI's cache, storing the incomplete flag.
- **Two implementations, one shared test fixture:** the rules exist in Python (`reposcout/`) and in JavaScript (`site/rules.js`). A shared fixture (`tests/fixtures/rules.json`) is checked by both pytest and `node --test`, so a rule changed in one language but not the other fails a test.
- **Usable at phone width** (user decision, "should" priority): the layout stacks, the table scrolls or hides less important columns, the strip gets more height.
- **README §1 "The demo" is rewritten** for the website (this is HW8), and `docs/USER_MANUAL.md` gets a "Website" section.

**Not in scope:** publishing on GitHub Pages (later; Pages' settings switch serves only the repo root or `/docs`, so it needs a move to `docs/` or a Pages workflow, see design.md), topic-vs-topic comparison (a "could"), any token on the web page, any change to the CLI's behaviour.

## Capabilities

### New Capabilities

- `web-ui`: the static, tokenless search page: what it fetches, how it shows the verdict, heartbeat strip, table and CSV, its states, its browser cache, its parity with the CLI's rules, and its phone-width layout.

### Modified Capabilities

_None._ The CLI's `repo-search`, `search-cache` and `github-auth` behaviour is unchanged. The new fixture tests check the existing Python rules without changing them.

## Impact

- **New files:** `site/index.html`, `site/style.css`, `site/app.js`, `site/rules.js`, `site/vendor/` (d3 + Observable Plot, pinned, with their licence files), `tests/fixtures/rules.json`, `tests/test_rules_fixture.py`, `tests/js/rules.test.mjs`.
- **Changed docs:** `README.md` §1, `docs/USER_MANUAL.md` (new Website section, including the test command `pytest && node --test tests/js/`).
- **Unchanged:** all of `reposcout/`, `pyproject.toml` (no new Python dependencies). JavaScript tests use Node's built-in test runner (Node 24 is installed), with no npm packages.
- **Demo:** screenshots for the 28 Nov slides come from this page.
