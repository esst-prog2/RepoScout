# SPEC: "From 14,067 repos to one sentence"

GOAL:    a viewer who has never seen RepoScout understands, without sound, how one search becomes one
         sentence (50 best matches → placed by last push → grouped → counted), and wants to try it.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps, silent (it plays muted on the promo page).
TIME:    30 s x 30 fps = 900 frames. No music, so no beat grid.

LOOK:    RepoScout's own ECG printout world (DESIGN.md), nothing new.
         Ground: paper #fdfafa for the mechanism; oxblood band #3a0d17 for the opening question and the end line
         (the page's own header band). Ink #24161a, soft ink #6a5357, cream #fbeef0 / #e3bfc5 on oxblood.
         One accent, trace red #b3122e: only on "active" and on the 50 chosen marks.
         Bucket inks as in the app: stale #9a9ea5 / #4f5359, slowing #d48a14 / #8a5000, active #c8193a / #a3102a.
         Type: Archivo (the app's vendored woff2). Display 800 weight at font-stretch 75%, tracking -1%;
         body 500 at 100%. Sizes: hero number 260 px, scene lines 56 px, small lines 30-36 px (floor 28 px).
         Chart paper: 5 px minor grid #f1cdd2, 25 px major #e09aa6, both scaled with the sheet (x1.5).
         No shadows, no grain, no vignette: it is printed paper.
OBJECTS: GitHub's own search page for the topic (screenshot of github.com, 17 Nov 2026, sorted by Best match;
         account names and avatars blurred), with rank badges #1-#7 and the sort control circled;
         the ECG sheet from the app, with its four axis labels (5+ years, 1 year, 90 days, now),
         its two zone rules and its trace; the real result and table screens from 26 October 2026
         (table crop with account names blurred, as on the page).
DATA:    one module, assets/data.js. Counts from the 26 Oct screenshot 3: 14,067 matches, 50 shown,
         36 stale / 4 slowing / 10 active, verdict sentence verbatim. Dot positions and sizes read from that
         screenshot's strip (Pillow colour detection): 10 active and 4 slowing found exactly, 29 stale found;
         the other 7 stale dots overlap in the "5+ years" pile and are placed in that pile.
MOTION:  arrivals expo.out 0.5-0.7 s; recolour power2.inOut 0.4 s; marks drop power3.out 0.35 s,
         stagger by x order 22 ms; trace draws linearly left to right in 1.2 s (constant speed is the point);
         exits are blur 6 px + fade in 0.18 s. Landed text holds dead still.

SHOTS:
  s1  0.0-3.5   oxblood. "14,067" counts up 0 → 14,067 in 1.2 s (tabular figures). 0.5: "repos on GitHub match
                “project management software”". 1.7: "Which 50 matter?" (3 words: the short opening question).
  s2  3.5-8.6   paper. Left: "GitHub's own search". Right: the real results page (assets/github-search.png).
                0.6: "It ranks them by how well they match". 1.0: "Sort by: Best match" circled and labelled.
                1.4: badges #1-#7 down the results. 2.9: "RepoScout reads the top 50". Caption: "github.com,
                17 November 2026 · account names and avatars blurred". (Earlier versions: a field of 14,067 marks,
                a hand-drawn list, a two-bar chart; the user chose a real GitHub screen instead.)
  s3  8.6-15.5  paper. The ECG sheet prints left to right. 0.3: "Each repo is placed by its last push".
                The 50 dots drop onto their real positions in ink. 2.2: zone rules draw, dots take their bucket
                colours, zone counts print (36 stale · 4 slowing · 10 active). 3.6: "Size is stars. The trace
                spikes at every push." 3.8: the trace draws.
  s4  15.5-21.6 paper. The verdict sentence prints word by word from light grey to ink (80 ms apart):
                "Showing the 50 best-matching of 14,067 repos, 10 active among them", "10 active" in trace red;
                1.6: "— most recent entrant pushed 1 minute ago".
  s5  21.6-26.2 paper. The real screens, one at a time: result + strip (2.1 s), then the ranked table with
                Download CSV (2.2 s). Caption: "The real screens, 26 October 2026" / "Ranked by stars · Download CSV".
  s6  26.2-30.0 oxblood. "14,067 repos in." / "One sentence out." then "Try it: esst-prog2.github.io/RepoScout".

BANNED:  dark navy void; glow, particles, gradients, glass; everything centred (text is left-aligned on the
         192 px title-safe edge); everything fading and sliding up; text moving while read; corner labels and
         HUD decoration; three cards in a row; the logo in a corner; a title over a dimmed screenshot;
         invented numbers; any account name readable.
QA:      t=0.2 (first frame not empty), 2.8, 6.5, 12.8, 14.8, 18.5, 23.0, 25.5, 29.0, plus the phone sheet.
