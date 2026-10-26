---
version: 1
slug: "site-index-html"
primary_target: "site/index.html"
related_targets: []
---

# Surface brief: RepoScout search page (site/index.html)

Scope: the single search page (start screen, results, states). Mode: Operate.
Audience/job: demo audience seeing still screenshots; author and friend searching a topic and exporting a CSV. Constraints: static/no build, vendored assets only, CLI-identical rules and verdict wording, usable at 360 px, all web-ui spec scenarios stay true.
Example topics (buttons): data visualization, project management software, expense tracker, monitoring.

## Direction contract

THESIS: A topic's activity read like an ECG printout: the strip is chart paper and a trace runs under the dots, spiking where repos were pushed and flatlining where nothing moved. Refuses the grey-card dashboard with a blue button.
OWN-WORLD: Near-white paper ground with a pink millimetre grid inside the strip; oxblood ink header band holding title and search; trace red (#b3122e family) = active, amber = slowing, flat grey = stale; Archivo variable (condensed widths for headline and numbers, normal for body); hairline pink-grey rules; tabular numerals.
STORY: The visitor types a topic, reads one headline verdict with the active count in trace red, sees whether the trace beats or flatlines, scans a dense ranked table (hover a row and its dot lifts), downloads the CSV.
FIRST VIEWPORT: Oxblood band: RepoScout title, one-line promise, search field + red Scout button, example topic buttons. Below on paper: verdict headline (condensed, ~2.25rem) with tail line, then the strip (≈340 px) with zone counts, grid, dots and trace lane at the bottom. Table starts below the fold.
FORM: Candidate 3 of 7 (ECG chart paper). Signature move: the trace lane, a flatline where nothing pushed. Raises: hover row lifts its dot and dims the rest (streaming wall); hairline dense table (Japanese high-density); fixed label sizes (rail map); state restyles a row without breaking the grid (split-flap). seed:57447f7b3f68e516
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
