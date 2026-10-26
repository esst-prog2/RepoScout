---
name: RepoScout
description: A GitHub topic's activity read like an ECG printout, with a ranked table and a CSV.
colors:
  paper: "#fdfafa"
  sheet: "#ffffff"
  ink: "#24161a"
  ink-soft: "#6a5357"
  rule: "#ecdcdc"
  band: "#3a0d17"
  band-text: "#fbeef0"
  band-soft: "#e3bfc5"
  grid-minor: "#f1cdd2"
  grid-major: "#e09aa6"
  zone-rule: "#c98591"
  printout: "#9a5562"
  active: "#b3122e"
  active-hover: "#cf1a39"
  slowing: "#a35f00"
  stale: "#666b72"
  active-dot: "#c8193a"
  slowing-dot: "#d48a14"
  stale-dot: "#9a9ea5"
  active-label: "#a3102a"
  slowing-label: "#8a5000"
  stale-label: "#4f5359"
  tint: "#fdf1f3"
  head-bg: "#fbf4f4"
  warning-bg: "#fff3d9"
  warning-ink: "#5c3a00"
  error-ink: "#8f0f26"
  error-rule: "#e7b3bd"
typography:
  display:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "2.6rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.01em"
    fontVariation: "'wdth' 75"
  headline:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(1.7rem, 1.2rem + 1.8vw, 2.6rem)"
    fontWeight: 750
    lineHeight: 1.08
    letterSpacing: "-0.01em"
    fontVariation: "'wdth' 80"
  title:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1.3rem"
    fontWeight: 700
    fontVariation: "'wdth' 85"
  body-large:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 400
    lineHeight: 1.5
  body:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
    fontVariation: "'wdth' 100"
  label:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "0.85rem"
    fontWeight: 650
    fontVariation: "'wdth' 85"
  printout:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "0.82rem"
    fontWeight: 400
    letterSpacing: "0.01em"
    fontFeature: "'tnum'"
    fontVariation: "'wdth' 87"
  zone-label:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 650
rounded:
  mark: "1px"
  control: "6px"
  table: "8px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "24px"
  xl: "34px"
components:
  button-scout:
    backgroundColor: "{colors.active}"
    textColor: "{colors.sheet}"
    rounded: "{rounded.control}"
    padding: "13px 26px"
  button-scout-hover:
    backgroundColor: "{colors.active-hover}"
  input-search:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    typography: "{typography.body-large}"
    rounded: "{rounded.control}"
    padding: "13px 16px"
  chip-topic:
    textColor: "{colors.band-text}"
    rounded: "{rounded.control}"
    padding: "5px 12px"
  button-csv:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.active}"
    rounded: "{rounded.control}"
    padding: "9px 16px"
  button-csv-hover:
    backgroundColor: "{colors.tint}"
  table-head-cell:
    backgroundColor: "{colors.head-bg}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.label}"
    padding: "6px 12px"
  table-row-lit:
    backgroundColor: "{colors.tint}"
  status-error:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.error-ink}"
    rounded: "{rounded.control}"
    padding: "12px 16px"
  warning:
    backgroundColor: "{colors.warning-bg}"
    textColor: "{colors.warning-ink}"
    rounded: "{rounded.control}"
    padding: "12px 16px"
---

# Design System: RepoScout

## Overview

**Creative North Star: "The ECG Printout"**

A topic on GitHub is read the way a clinician reads a strip: near-white paper, a pink millimetre grid inside the chart, and one dark trace that runs flat and spikes where something moved. An oxblood ink band at the top holds the title and the search, like the printed header of a recording. Below it, everything is paper: the verdict set as a condensed headline, the strip itself, the line printed on the sheet's margin saying where the data came from, and a dense, hairline-ruled table.

The system is flat, dense and honest. Colour carries meaning only: trace red is active (and the one action), amber is slowing, flatline grey is stale. One vendored variable family (Archivo) does every job, and its width axis, not a second typeface, carries the hierarchy. The page answers first; the chart is supporting evidence, and the verdict and table survive without it.

It refuses the grey-card dashboard with a blue button: no cards around the chart, no shadows, no GitHub blue, no system fonts as display.

**Key Characteristics:**
- Paper ground, oxblood header band, pink grid only on the chart sheet.
- Three bucket inks (red, amber, grey) used for meaning, never for decoration.
- One family, Archivo, with condensed widths for headline, labels and numbers.
- Hairline rules and tonal tints instead of shadows or containers.
- Tabular numerals wherever numbers stack.
- A trace lane with a calibration pulse: the signature that turns a scatter into a heartbeat.

## Colors

A warm paper-and-ink palette tinted toward oxblood, with three instrument inks for the activity buckets.

### Primary
- **Trace Red** (`active`): the active bucket everywhere (the "N active" count in the verdict, bucket words, the square row mark), the Scout button, the CSV button's outline and text, the focus ring, the input caret. Its hover is **Pulse Red** (`active-hover`); its tint is **Blush** (`tint`).
- **Oxblood Ink** (`band`): the header band behind title and search, and the trace line in the strip and on the idle sheet. Also the `theme-color`.

### Secondary
- **Chart Amber** (`slowing`): slowing bucket words; dark enough to hold contrast on white.
- **Flatline Grey** (`stale`): stale bucket words and the "0 active" count when nothing is alive.
- **Dot inks** (`active-dot`, `slowing-dot`, `stale-dot`): lighter, more saturated versions of the bucket inks used only for chart dots (85% fill, white hairline stroke).
- **Zone inks** (`active-label`, `slowing-label`, `stale-label`): darkened bucket inks for the zone labels above the strip, so the labels read at presentation distance.

### Neutral
- **Paper** (`paper`): page ground below the band.
- **Sheet** (`sheet`): pure white for the input, the table box, the chart sheet and the error box.
- **Ink** (`ink`): body text, headline, `code`.
- **Soft Ink** (`ink-soft`): captions, notes, table header text, verdict tail, stale rows' rank and name, chart axis text.
- **Hairline** (`rule`): table borders and row dividers.
- **Band Text / Band Soft** (`band-text`, `band-soft`): title and promise on the band; topic chip borders are band text at 35% (60% on hover).
- **Grid Minor / Grid Major** (`grid-minor`, `grid-major`): the 5 px and 25 px squares of the chart paper. **Divider** (`zone-rule`): the two zone boundary rules inside the strip. **Printout Ink** (`printout`): the margin line under the strip.
- **Row Tint / Head Tint** (`tint`, `head-bg`): hovered or lit rows; the table header.
- **Warning** (`warning-bg`, `warning-ink`) and **Error** (`error-ink`, `error-rule`): the incomplete-results notice and the error status box.

### Named Rules
**The Instrument Ink Rule.** Red, amber and grey mean active, slowing and stale. Red additionally marks the one primary action and focus. No colour is applied for decoration.

**The Grid Belongs To The Sheet Rule.** The pink millimetre grid appears only on chart paper (the results strip and the blank start sheet). The page ground stays plain paper.

## Typography

**Display Font:** Archivo variable (wdth 62–125, wght 100–900), vendored woff2, with system-ui fallback
**Body Font:** Archivo at normal width
**Label/Mono Font:** Archivo condensed for labels; a system monospace stack only for the inline `pushed_at` code note

**Character:** A workmanlike grotesque that condenses into a tight, instrument-like headline and opens up for reading. Width is the hierarchy.

### Hierarchy
- **Display** (800, 2.6rem, 75% width, line-height 1): the RepoScout title on the band; 2.1rem at phone width.
- **Headline** (750, fluid 1.7–2.6rem, 80% width, line-height 1.08, balanced, max 32ch): the verdict. The "N active" phrase is coloured; the "— most recent entrant…" tail drops to a block line in body-large, 500, soft ink.
- **Title** (700, 1.3rem, 85% width): the table heading.
- **Body Large** (1.05rem): the promise, the search input, the Scout button, the idle caption, the verdict tail.
- **Body** (400, 16px/1.5): default text; table cells at 0.93rem.
- **Label** (650, 0.85rem, 85% width): table header cells. Bucket words are 700 at 0.88rem, 87% width (stale at 600).
- **Caption** (0.9rem / 0.85rem): the chart legend line and the notes.
- **Printout** (0.82rem, 87% width, tabular numerals): the margin line under the strip.
- **Zone label** (650, 15 px; 13 px on narrow charts) and axis ticks (13 px): fixed pixel sizes inside the chart.

### Named Rules
**The One Family Rule.** Archivo is the only typeface. New hierarchy comes from width (75 / 80 / 85–87 / 100%) and weight, not from a second family.

**The Tabular Numbers Rule.** Stars, ranks, dates and the printout use tabular numerals so columns align.

**The Fixed Label Rule.** Chart labels keep fixed pixel sizes (like a rail map), changing only at the narrow breakpoint; they never scale with the chart.

## Layout

A single centred column (max 1080 px, 24 px gutters; 16 px at phone width). The header band runs full-bleed. Order on the page: band (title, promise, search row, example topics) → status line → verdict → strip with legend, zone counts, printout line and notes → table heading with CSV button → table. On the start screen the results are replaced by a blank chart sheet (180 px; 140 px on phones) with a flat trace and the calibration pulse, captioned "No topic yet…".

Spacing is compact: 8–12 px inside groups, 16–26 px between blocks, 34 px under the strip. Table cells are dense (6 px × 12 px). The chart is 340 px tall (360 px when narrower than 520 px), with 40 px top margin for zone labels and 34 px bottom margin for the axis.

At ≤600 px: the search stacks (input above a full-width Scout button), example topics become one sideways-scrolling row with an edge fade, the table heading stacks above the CSV button, the Last Push and Language columns hide, cells tighten to 7 × 8 px, repo names break after the slash, and the page never scrolls sideways.

## Elevation & Depth

Flat. There are no shadows anywhere. Depth comes from two planes only: the oxblood band over the paper, and white sheets (input, table box, chart paper) on the paper ground, separated by hairlines and faint tints.

### Named Rules
**The Flat Printout Rule.** Nothing floats. State is shown with tint, ink and opacity (a lit row tints, a lit dot gets an ink ring, loading dims results to 45%), never with lift or shadow.

## Shapes

Gently rounded controls (6 px) and a slightly softer table box (8 px); the chart sheet and grid are square-cornered, like real chart paper. The only other shape is the 6 px square row mark with a 1 px radius. Dots are circles sized by the square root of stars (3–16 px radius, 3–11 px on narrow charts).

## Components

### Buttons
- **Scout (primary):** trace red fill, white 700 text at 87% width, 13 × 26 px padding, 6 px radius; hover to pulse red. Full width at phone size.
- **Download CSV (secondary):** white sheet, 1 px trace-red outline and text, 650 weight, 9 × 16 px; hover tints to blush. Hidden when there are zero results.
- **Focus:** a 2 px trace-red outline offset 2 px; on the band the outline switches to band text.

### Chips
- **Example topics:** transparent on the band, band-text label at 0.9rem, 1 px band-text border at 35%, 5 × 12 px, 6 px radius; hover adds a 12% band-text fill and a 60% border. Preceded by a plain "Try" label. Clicking fills the input and searches.

### Inputs / Fields
- **Search:** white, borderless (transparent 1 px border), 6 px radius, 13 × 16 px, body-large, ink text, trace-red caret, soft placeholder ("e.g. expense tracker"). Empty or spaces-only input shows the error status instead of searching.

### Status and notices
- **Status line:** soft-ink text in a reserved line above the results. Loading reads "Scouting GitHub…" in trace red at 1.15rem/600 while any previous results dim to 45%.
- **Error:** white box, 1 px error-rule border, error ink, 6 px radius; results are hidden.
- **Incomplete warning:** amber-cream fill with dark amber text, 6 px radius, under the verdict.

### Heartbeat strip (signature)
The strip is the sheet of chart paper itself, not a card holding a chart. A white sheet with a 5 px minor / 25 px major pink grid; two divider rules split it into three zones on a piecewise time axis (5+ years · 1 year · 90 days · now). Above each zone, a fixed-size label gives its count in its zone ink ("37 active · last 3 months"; short forms on narrow charts). Dots sit in the upper band at a stable height derived from the repo name (height only keeps dots apart); big dots draw first, small ones on top. Hovering a dot shows a tip with repository, stars and last push.

### Trace lane and calibration pulse
Along the bottom of the strip an oxblood 1.6 px trace runs flat and spikes at each repo's last push, taller for more stars, with neighbouring pushes within 7 px merged into one beat. Spike shapes are sized in screen pixels so a beat looks the same on a phone and a projector. A square calibration pulse sits in the margin before "5+ years", as at the start of every ECG lead; its flat top cannot be mistaken for a repo. A topic nobody pushes to flatlines across the active zone.

### Printout line
Under the strip, in printout type and printout ink: "GitHub search · 50 of N repos · fetched HH:MM" (date added when not today), like the speed/gain line on an ECG. A cached result tells on itself through its time. Followed by the note that "Last push" is GitHub's `pushed_at`.

### Results table
White box, 1 px hairline border, 8 px radius, scrolling sideways inside itself if ever needed. Header cells in label type on head tint. Columns: #, Repository, Stars, Last Push, Language, Bucket; # and Stars right-aligned in tabular numerals. Row states restyle inside the same grid (split-flap discipline): active rows carry a trace-red square mark left of the rank, the bucket word takes its bucket ink, stale rows fade rank and name to soft ink. Hover or keyboard focus tints the row and drives the linked highlight. Missing language shows "-".

### Linked highlight
Pointing at or tabbing into a table row dims every chart dot to 18% and lifts that row's dot to full opacity with a 2 px ink ring (120 ms ease-out; no transition under reduced motion).

## Do's and Don'ts

### Do:
- **Do** keep the verdict text exactly as the CLI words it (`formatVerdict` in `rules.js`, checked by the shared fixture). Styling may split it into spans, but the element's text content must equal the CLI sentence.
- **Do** insert every GitHub-supplied string (repo names, languages, error messages) and the keyword as plain text (`textContent` or text nodes), never as HTML.
- **Do** keep the page static: plain HTML/CSS/JS, vendored pinned assets (d3 7.9.0, Observable Plot 0.6.17, Archivo woff2), no CDN, no build step.
- **Do** render the verdict and table before the chart, and show the chart-unavailable note if the chart fails.
- **Do** use bucket inks only for bucket meaning, and use the darkened zone inks for labels on the grid.
- **Do** keep chart labels at fixed pixel sizes and spike shapes in screen pixels.
- **Do** keep the page usable at 360 px with no sideways page scroll.

### Don't:
- **Don't** wrap the strip in a card, add a shadow, or tint the zones; the sheet itself is the chart.
- **Don't** draw the pink grid outside chart paper.
- **Don't** introduce a second typeface or a system display face; use Archivo's width axis.
- **Don't** render buckets as filled pills; the bucket is a coloured word.
- **Don't** change a row's layout to show its state; change its ink.
- **Don't** reword "Last Push", "best-matching", or the bucket names "active / slowing / stale".
