# REVIEW: "From 14,067 repos to one sentence"

Delivered: `promo/video/reposcout-explainer.mp4` (30.0 s, 1920×1080, 30 fps, H.264, no audio track, 1.23 MB after
re-encoding the 3.3 MB HyperFrames render at CRF 24 with faststart) and `promo/video/poster.jpg` (the frame at 2.8 s).
Re-render: `cd video`, `npx hyperframes render -o renders/reposcout-explainer.mp4`, then the ffmpeg line in
`promo/img/README.md`'s spirit: `ffmpeg -i video/renders/reposcout-explainer.mp4 -c:v libx264 -crf 24 -preset slow
-pix_fmt yuv420p -movflags +faststart -an promo/video/reposcout-explainer.mp4`.

## Creative calls

- Idea 2 of three proposed (the others: "how a heartbeat strip is built", "can you trust the date?").
- Style: explainer, one idea a layer at a time: a 3-word opening question ("Which 50 matter?"), then the mechanism
  (14,067 marks → the 50 best → placed by last push → grouped → the sentence), then the line to remember
  ("14,067 repos in. One sentence out."). The idea is on screen by the second scene.
- Silent on purpose: the request says it must work without sound and the page plays it muted. HyperFrames' check
  warns `film_silent`; kept.
- Look: RepoScout's own ECG world (oxblood bookends, paper, Archivo from `site/vendor/fonts`), nothing new.

## Data, and what is drawn rather than captured

- All numbers are the 26 October 2026 search (screenshot 3) and match the promo page: 14,067, 50, 36/4/10, the verdict.
- The 50 dots are placed where they are in that screenshot's strip (Pillow colour detection). 10 active and 4 slowing
  were found exactly; 29 stale dots were found and the other 7 overlap in the "5+ years" pile, so they are drawn in
  that pile (`assets/data.js`). The trace is redrawn from those dots, so it is close to, not identical with, the app's.
- The selection is shown on GitHub's own search page: a 1920×1080 screenshot of
  github.com/search?q=project+management+software&type=repositories (logged out, 17 Nov 2026, "Sort by: Best
  match"), cropped to the results (1160×1000 at x 320, y 80). Every owner name (the part before "/") and every
  avatar was pixelated with Pillow using boxes measured from the page's DOM, and checked at 3× zoom. The page
  showed 14.4k results that day (14,067 on 26 Oct); the caption dates the screenshot instead of hiding the count.
- Real screens: the result + strip crop and the table crop already on the promo page (account names blurred).
- Nothing in the film shows a feature RepoScout does not have.

## Checked

- `npx hyperframes check`: 0 errors. Warnings kept: `film_silent` (above), `timeline_track_too_dense` (4-6 timed
  elements per scene file; readable as is). Fixed: a 4 s dead stretch on the verdict (added the line "The command
  line prints the same sentence."), a caption shown 2.13 s for 8 words (shortened and held 2.6 s), "them" alone on
  a third line (narrower type).
- Looked at: 11 frames at the SPEC's QA times, the review sheets (cuts, phone width at 360 px), and 7 frames pulled
  from the final MP4. On the promo page (headless Chromium): the video loads (readyState 4, 1920×1080), plays muted,
  no sideways scroll at 1440 or 360 px.
- Not checked: real phones and Safari; how it looks on a projector.

## Weakest shot, and next

- Fixed after publishing (17 Nov): the first version showed 14,067 tiny marks as a field, which read as a glitch;
  a hand-drawn list and then a two-bar chart (registry `chart-story`) followed; the user chose a real GitHub screen.
- Weakest now: the cut between the list and the sheet. With more time: carry the 50 red rows into the next
  scene as its 50 dots, so the same objects travel through the whole film.
- At phone width the small lines (axis labels, zone counts) are too small to read; the scene lines are readable.
