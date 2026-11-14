# Design

## Context

- **The app today:** `site/` is a static page run on localhost only (`cd site`, `python -m http.server`). It loads `style.css`, two vendored scripts and `app.js` from `index.html`, and `app.js` imports `./rules.js` as an ES module. On 26 October a browser kept an old cached `rules.js` while loading a new `app.js` and the page broke, so publishing needs cache-busting.
- **Already decided:**
  - The promo page's content: `docs/designs/promo-page.md` (approved in `/office-hours`).
  - Its design brief: `docs/designs/promo-page-brief.md` (`/impeccable shape`). It uses the app's ECG printout world and the vendored Archivo font, and its hero is two stacked "ECG leads" cut from screenshots 1 and 2.
  - The hero's exact arrangement is chosen afterwards with `/impeccable generate`.
- **Repo:** `esst-prog2/RepoScout` is public. The user has set its Pages source to "GitHub Actions". There is no `.github/` folder yet.
- **The course rule:** `main` never broken.

## Goals / Non-Goals

**Goals:**
- One public address shows the promo page, with the app one click away at `app/`.
- Only the promo page, the app and the promo images are published.
- A returning visitor never mixes old and new cached files.
- The local preview is byte-for-byte the folder that gets deployed.

**Non-Goals:**
- Any change to the app (`site/`), the CLI, README §1 or the original screenshots.
- `?q=` deep links from the promo page into the app.
- A custom domain, analytics or tracking of any kind.
- Retaking screenshots. The instructor asked us to keep the 26 October ones.

## Decisions

1. **Layout of the published site.** `_site/index.html` (promo) plus `_site/style.css` and `_site/img/`, and `_site/app/` holding the contents of `site/`.
   - Why: the promo page is what the course link should show, and the app stays reachable under a stable, readable address.
   - Rejected alternatives:
     - App at the root with the promo page elsewhere: the link would land on the tool rather than the page.
     - Moving files into `docs/` for "deploy from branch": it would publish all of `docs/`, including the design notes.

2. **One stdlib-only Python script, `scripts/build_pages.py`, for both preview and deploy.**
   - It empties and recreates the output folder (default `_site/`, gitignored), copies `promo/` to the root and `site/` to `app/`, then rewrites the copies for cache-busting.
   - `--version <text>` sets the suffix: the workflow passes the short commit SHA, and the local default is `dev`.
   - `--serve [port]` serves the folder after building (`http.server`, default 8000).
   - Why Python: the repo's language, testable with pytest, runs the same on Windows and in CI.
   - Rejected alternatives:
     - A shell `sed` step only in the workflow: it can't be previewed or unit-tested, and Windows has no `sed`.
     - A bundler: that would be a build tool, against the project's static, no-build rule.
   - Sources are never written. The script reads only `promo/` and `site/` and writes only into the output folder, and it refuses an output folder that resolves to the repo root, `site/` or `promo/`.

3. **Cache-busting rule, in the copies only.**
   - In every assembled `.html`, a `<link rel="stylesheet" href="X">` or `<script src="X">` whose `X` is a relative URL gets `X?v=<version>`.
   - In the assembled `app/app.js`, `from "./rules.js"` becomes `from "./rules.js?v=<version>"`.
   - Fonts (`<link rel="preload" … as="font">` and `@font-face` URLs) are left alone: they are vendored at a fixed version, and suffixing only the preload would make the browser download the font twice.
   - After rewriting, a check fails the run (non-zero exit, nothing to deploy) if any relative stylesheet or script URL lacks `?v=`, or if a plain `"./rules.js"` import remains.
   - Absolute and external URLs are not touched. The site has none, and a test keeps it that way.

4. **The promo page reuses the app's assets by relative path into `app/`.**
   - `promo/index.html` loads the vendored Archivo font from `app/vendor/fonts/…`, so there is no second copy in git. The licence file already sits in `app/vendor/fonts/`.
   - Consequence: the promo page renders correctly only in the assembled folder (preview or Pages), not by serving `promo/` alone. That's acceptable: the script's preview is the documented way to view it.
   - The promo stylesheet `promo/style.css` copies the few design tokens it needs from DESIGN.md (paper, ink, band, trace red, amber, grey, hairline) as CSS custom properties. It does not import the app's `style.css`, whose selectors belong to the app.

5. **Hero images are crops, not new screenshots.**
   - `promo/img/lead-mcp-server.png` and `promo/img/lead-angularjs-directive.png` are cut with `ffmpeg` (already on this machine) from `docs/screenshots/1-…` and `2-…`.
   - The crop runs from the zone labels to the axis labels: the strip only, with the same crop box for both so their time axes line up exactly.
   - The verdicts above them are HTML text, copied character for character from the screenshots.
   - Screenshots 3 and 4 are used whole, copied by the script from `docs/screenshots/` into `_site/img/`, so git keeps one copy.
   - The crop commands and the source file are recorded in `promo/img/README.md`. That file is not copied to the site.

6. **Deploy workflow, `.github/workflows/pages.yml`.**
   - **Triggers:** `push` to `main`, and `workflow_dispatch`.
   - **Permissions:** `contents: read`, `pages: write`, `id-token: write`.
   - **Concurrency:** group `pages`, `cancel-in-progress: false`.
   - **Job `build`:**
     1. Check out the repo.
     2. Set up Python 3.12, then `pip install ".[dev]"`, then run `pytest`.
     3. Set up Node 24 and run `node --test "tests/js/*.test.mjs"`.
     4. Run `python scripts/build_pages.py --version ${GITHUB_SHA::7}`.
     5. Upload `_site` with `actions/upload-pages-artifact`.
   - **Job `deploy`:** needs `build`, environment `github-pages`, uses `actions/deploy-pages`.
   - **Action versions:** every action is pinned to an exact release tag, looked up from GitHub when the workflow is written. No floating `@v4`-style major tags.
   - A failing test stops `build`, so `deploy` never runs and the previous site stays online.

7. **Tests (`tests/test_build_pages.py`, pytest).**
   - **Layout:** the script, built into a temporary folder, produces exactly the allowed paths and none of the forbidden ones.
   - **Cache-busting:** every relative CSS and JS reference is suffixed, the rules import is suffixed, and fonts are not.
   - **Sources untouched:** a hash of `site/` and `promo/` is the same before and after a build.
   - **Check fails** on a deliberately unsuffixed fixture.
   - **Refusals:** the script refuses dangerous output folders.
   - **Promo text:** the exact verdict sentences and figures, the 26 October date and the three links are present, and there are no e-mail addresses, local paths or exclamation marks.
   - Browser checks (360 px, reduced motion, alt texts, focus order) are done with gstack's browse tool, as for the app.

## Risks / Trade-offs

- **The course org may restrict Actions or Pages.** The user has already set the source to "GitHub Actions". If the first deploy is refused, the instructor asked to be told, and nothing in the repo needs to change.
- **Shared rate limit:** classmates on one Wi-Fi share 10 unauthenticated searches a minute. The app already shows when to retry, and the promo page says it up front.
- **The promo page can't be previewed by serving `promo/` alone** (Decision 4). The manual documents `python scripts/build_pages.py --serve`.
- **The cache-busting rewrite uses text patterns, not an HTML parser.** It is fine for our own small, fixed pages, and the post-rewrite check catches any link it misses.
- **Pages caches responses for about 10 minutes.** The `?v=` change still guarantees matching files, but a returning visitor may see the previous `index.html` for a few minutes after a deploy.

## Migration Plan

1. Build on the `promo-page` branch: script and tests first, then the promo page, then the workflow.
2. Merge to `main` by pull request ("Create a merge commit"). The first run on `main` deploys.
3. Open the live address on a laptop and a phone.
4. Rollback: revert the merge, and the next workflow run republishes the previous state. Disabling Pages in the settings takes the site down entirely.

## Open Questions

- None blocking. The hero arrangement is chosen with `/impeccable generate` after the first version exists.
