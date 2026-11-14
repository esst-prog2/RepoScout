# Proposal

## Why

The course homework asks for a promo page on GitHub Pages: what RepoScout is for, who it is for, how to try it, with a link to the program when it runs online. Today the app (`site/`) runs only on localhost, so nobody can try it from a link. The instructor confirmed that we publish from the course repo itself (Pages source "GitHub Actions", already set by the user), not from a fork.

## What Changes

- New promo page in `promo/`, built from the approved content (`docs/designs/promo-page.md`) and design brief (`docs/designs/promo-page-brief.md`):
  - **Hero:** the question headline, **Open RepoScout** and **View the code on GitHub**, and two stacked "ECG leads" cut from the 26 October screenshots (`mcp server` beating, `angularjs directive` flatlining), with their verdicts as real text.
  - **Sections:** "For people about to build", "One search, four answers" (screenshots 3 and 4 with numbered markers), "Try it" (browser and command line) and "Honest limits", then a footer.
  - **Look:** the app's existing ECG printout look and vendored Archivo font. No new dependency.
- New cropped images of screenshots 1 and 2 (strip only) in `promo/img/`. They are cut from the 26 October originals, not retaken; the originals in `docs/screenshots/` stay untouched.
- New assembly script `scripts/build_pages.py`. It copies the promo page to the site root, the app to `app/` and the screenshots the promo page needs into one output folder (`_site/`, gitignored), and adds cache-busting `?v=<version>` suffixes to the copies only.
  - The same script powers a local preview, so localhost shows exactly what GitHub Pages will show.
  - Sources stay plain: the app still runs with `cd site` and `python -m http.server`.
- New GitHub Actions workflow `.github/workflows/pages.yml`. On every push to `main`, and on manual start, it runs the tests, assembles `_site/` with the script and deploys only that folder to GitHub Pages. The whole repository is never published.
- Docs:
  - `docs/USER_MANUAL.md` gets the live address and the preview command.
  - `PRODUCT.md`'s "GitHub Pages is a possible later step" line is updated.
- Out of scope: any change to the app's behaviour or look, the CLI, README §1, slides, `?q=` deep links from the promo page into the app.

## Capabilities

### New Capabilities
- `promo-page`: the promo page's required content (what for, who for, how to try), its links into the app and repo, evidence-only claims taken from the 26 October screenshots, phone width and reduced motion.
- `pages-publishing`: what gets published and where (promo at the root, app under `/app/`, nothing else from the repo), the assembly script and local preview, cache-busting of the published copies, and the deploy workflow.

### Modified Capabilities
<!-- none: the app's (web-ui) requirements already cover "works when served by any static file server"; publishing it under /app/ changes no app behaviour -->

## Impact

- **New files:**
  - `promo/index.html`, `promo/style.css`, `promo/img/*.png`
  - `scripts/build_pages.py`
  - `.github/workflows/pages.yml`
  - tests for the assembly script (`tests/test_build_pages.py`)
- **Changed files:** `.gitignore` (`_site/`), `docs/USER_MANUAL.md`, `PRODUCT.md`.
- **Unchanged:** `site/`, `reposcout/`, `README.md`, `docs/screenshots/`, all existing tests.
- **External:**
  - GitHub Pages for `esst-prog2/RepoScout` (public). The live address will be https://esst-prog2.github.io/RepoScout/ (promo) and https://esst-prog2.github.io/RepoScout/app/ (app).
  - The workflow uses GitHub's official Pages actions, pinned to exact versions.
  - Visitors of the live app share GitHub's unauthenticated search limit per network (10 a minute), which the app already handles.
