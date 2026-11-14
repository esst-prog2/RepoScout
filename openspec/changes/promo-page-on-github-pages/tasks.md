## 1. Assembly script (tests first)

- [ ] 1.1 Write `tests/test_build_pages.py` covering:
  - the allowed layout and the forbidden files
  - every relative CSS/JS reference suffixed, the `./rules.js` import suffixed, fonts not suffixed
  - `site/` and `promo/` unchanged (hashes before and after)
  - the check failing on an unsuffixed fixture
  - refused output folders

  Run it and confirm it fails because the script doesn't exist yet.
- [ ] 1.2 Write `scripts/build_pages.py` (stdlib only), with `--out` (default `_site`), `--version` (default `dev`) and `--serve [port]`, following design Decisions 1–3. Add `_site/` to `.gitignore`.
- [ ] 1.3 Run the full pytest and node suites. All must pass, and the existing app tests stay unchanged.

## 2. Promo page (first version, from the brief)

- [ ] 2.1 Crop the two hero leads from `docs/screenshots/1-…` and `2-…` with `ffmpeg`, using the same box for both (zone labels down to the axis labels), into `promo/img/`. Record the exact commands in `promo/img/README.md`, and keep that file out of the assembled site. Check the crops by eye.
- [ ] 2.2 Write `promo/index.html` with all content from `docs/designs/promo-page.md`, word for word:
  - hero: headline, sub-line, the two actions, the two leads with verdict text and alt text, and the 26 October caption
  - "For people about to build"
  - "One search, four answers": screenshots 3 and 4 with numbered markers as HTML
  - "Try it": browser and command line (with the venv steps)
  - "Honest limits"
  - footer
- [ ] 2.3 Write `promo/style.css` in the app's ECG printout world:
  - tokens copied from DESIGN.md, and Archivo from `app/vendor/fonts/`
  - phone layout down to 360 px
  - the one-time left-to-right reveal of lead I, skipped under `prefers-reduced-motion`, with content visible by default
- [ ] 2.4 Add promo-text tests to `tests/test_build_pages.py`:
  - the exact verdict sentences and figures
  - the 26 October date
  - links to `app/`, the repo and the manual
  - no e-mail addresses, local paths or exclamation marks
- [ ] 2.5 Preview with `python scripts/build_pages.py --serve` and check in a real browser (gstack browse) at 1440 and 360 wide:
  - no sideways scroll
  - focus visible in reading order
  - images-off view still makes sense
  - reduced motion shows the final state
  - "Open RepoScout" opens the working app under `app/` and a search runs

## 3. Homework steps on the built page (Impeccable)

- [ ] 3.1 `/impeccable generate` on the hero: variants in the browser, and the user picks one. Bake it in, then re-run the tests.
- [ ] 3.2 `/impeccable critique` on the promo page (as a classmate, the teacher and a stranger). Fix its weakest part, then re-run the tests.

## 4. Deploy workflow

- [ ] 4.1 Look up the current exact release tags of `actions/checkout`, `actions/setup-python`, `actions/setup-node`, `actions/configure-pages`, `actions/upload-pages-artifact` and `actions/deploy-pages` (GitHub API via PowerShell).
- [ ] 4.2 Write `.github/workflows/pages.yml` per design Decision 6: triggers, minimal permissions, concurrency, the tests before the build, `--version ${GITHUB_SHA::7}`, upload, deploy.

## 5. Docs and release

- [ ] 5.1 `docs/USER_MANUAL.md`: add the live addresses (promo and app) and the preview command. Update `PRODUCT.md`'s Operating Context line about GitHub Pages.
- [ ] 5.2 Commit with a `PROCESS.md` row after each homework step. Push `promo-page` and open the PR. After the user merges, watch the workflow run and check the live promo page and app on a laptop and a phone.
