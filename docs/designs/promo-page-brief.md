# Design brief: RepoScout promo page

Made with Impeccable `shape`, 2026-11-14. No code yet. The content (every sentence and number) comes from [promo-page.md](promo-page.md) and is not changed here.

## 1. Job and audience

- **Mode: Persuade.** The visitor should understand what RepoScout is, believe it's worth one try, and click **Open RepoScout**.
- **Who arrives:** classmates and the instructor, from a link in the course or on the December slides, often on a phone. Also people about to build who land on the GitHub repo and click through to the page.
- **State of mind:** curious, short on time, allergic to sales talk.

## 2. Outcome and proof

- **Success:** within one screen the visitor can say "it shows whether a GitHub topic is alive, and I can try it right now, without signing in".
- **Proof is the product's own output, not claims:** the two 26 October searches (`mcp server` 37 of 50 active; `angularjs directive` 0 of 50 active), the `project management software` result (14,067 repos, 10 active) and the HW4 number (5 of 50 change group). Nothing else is claimed.

## 3. Selected direction

- **Visual world: the app's own ECG printout world**, inherited unchanged from [DESIGN.md](../../DESIGN.md): paper ground, oxblood band, trace red / amber / grey for meaning only, Archivo with its width axis, hairlines, no shadows, no cards. The promo page is louder through scale and layout, not through new colours or fonts. Pressing **Open RepoScout** should feel like stepping further into the same printout.
- **Hero: two ECG leads, stacked on one time axis.**
  - **Lead I:** `mcp server`, where the trace beats on the right.
  - **Lead II:** `angularjs directive`, where it flatlines across the active zone.
  - **Images:** both are cropped from the 26 October screenshots, strip only (zone labels, grid, dots, trace, axis). They are cut, not retaken, so every number stays as it was.
  - **Verdicts:** each lead's verdict is set as real text above its strip, quoting the screenshot exactly. It stays sharp at any size and readable on a phone.
  - **Reading:** the two "now" ends sit at the same x, so the eye compares the right edges.
- **Signature motion (once, on load):** each lead is revealed left to right, like paper feeding out of the recorder. It runs only for lead I in the first viewport and is skipped under reduced motion. The content is visible by default.
- **Sequence:** hero, then "For people about to build", then "One search, four answers" (screenshots 3 and 4 with numbered markers drawn as HTML over the image, so the labels stay text), then "Try it" (a browser block and a command-line block), then "Honest limits", then a footer band.
- **Open for `generate`:** the hero's exact arrangement, the next homework step (variants in the browser, you pick one). One option puts the headline and buttons above the leads. Another puts a narrow headline column beside them on desktop.

## 4. Scope and boundaries

- **Target:** a new page in `promo/` (`promo/index.html` plus its stylesheet), published at the site root. The app goes under `/app/`.
- **Untouched:** `site/` (the app), the CLI, `README.md`, and the four originals in `docs/screenshots/`. New files are only the promo page and the cropped copies.
- **Anti-goals (your choice: no salesy / hype):**
  - no superlatives ("blazing", "powerful", "the best")
  - no exclamation marks or urgency
  - no testimonials, logos or star-count badges
  - no invented users or numbers
  - no "trusted by" rows
  - no feature-icon grid
- **Nothing personal:** no name, email, local paths or thesis talk. The footer names the course and links the repo.

## 5. States and ranges

- **Images:** five crops or screenshots in total, each with alt text quoting its verdict. If an image fails, the alt text and the HTML verdict above it still carry the point.
- **Text:** fixed (no data loads on this page). The longest strings are the verdicts (about 90 characters) and the command block (the longest line is about 45 characters).
- **No interactive states** beyond links, buttons and focus. The command block can be selected and copied. A copy button is optional and not required.

## 6. Interaction and layout

- **Desktop (1280–1600 wide):** the headline, sub-line and both buttons sit in the first viewport together with lead I. Lead II starts just below, or beside the headline if `generate` picks the side layout.
- **Phone (360–390 wide):**
  - one column
  - the leads full width, verdict text above each strip
  - no sideways page scroll
  - buttons full width
  - the command block scrolls inside itself if a line is too long
- **Primary action:** **Open RepoScout** in trace red (the one action colour). **View the code on GitHub** is the quieter secondary button. The same pair repeats in "Try it".
- **Focus:** visible focus rings as in the app (2 px trace red).

## 7. Constraints and open decisions

- **Static, no build step.** It reuses the vendored Archivo font, with no CDN and no new dependency. GitHub Pages deploys it via our own Actions workflow, and cache-busting is done only in the workflow, as in the content doc.
- **Usable at 360 px**, with WCAG AA contrast (the app's tokens already meet it).
- **Open decision 1, for `/opsx:propose`:** how the promo page reaches the vendored font locally and when published (a relative path into `/app/vendor/fonts/` after assembly, or a copy), and how to preview the assembled site on localhost.
- **Open decision 2, for `generate`:** the hero arrangement, as described in section 3.
