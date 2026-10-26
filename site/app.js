// RepoScout web page: wires the search form to GitHub's search API (no token)
// and renders the verdict, heartbeat strip, table and CSV. All rules live in
// rules.js; this file only handles the DOM, fetch, cache and chart.
//
//   submit -> validate -> cache? --hit--> render
//                           |miss
//                           v
//                         fetch --> parse/validate --> render (+ cache write)
//                           |            |
//                       offline /    unexpected
//                       limited /    response
//                       HTTP error
//
// Every await is followed by a "still the latest search?" check, so a slow,
// older answer can never overwrite a newer search's results.
import {
  ACTIVE,
  SLOWING,
  STALE,
  TABLE_HEADERS,
  bucketFor,
  csvFilename,
  csvText,
  formatVerdict,
  groupThousands,
  isRateLimited,
  lastPushDate,
  normalizeQuery,
  parseSearchPayload,
  rankByStars,
  resetAt,
  row,
  UnexpectedResponse,
  xPosition,
} from "./rules.js";

const SEARCH_URL = "https://api.github.com/search/repositories";
const CACHE_PREFIX = "reposcout:";
const CACHE_TTL_MS = 24 * 60 * 60 * 1000;
const DAY_MS = 86400 * 1000;
const FETCH_TIMEOUT_MS = 20 * 1000;
const OPTIONAL_COLUMNS = new Set(["Last Push", "Language"]); // hidden at phone width

const $ = (id) => document.getElementById(id);
const els = {
  form: $("search"),
  keyword: $("keyword"),
  status: $("status"),
  results: $("results"),
  verdict: $("verdict"),
  incomplete: $("incomplete"),
  chart: $("chart"),
  chartNote: $("chart-note"),
  csv: $("csv"),
  idle: $("idle"),
  printout: $("printout"),
  announce: $("announce"),
  empty: $("empty"),
  emptyKeyword: $("empty-keyword"),
  heartbeat: document.querySelector(".heartbeat"),
  tableHead: document.querySelector(".table-head"),
  tableWrap: document.querySelector(".table-wrap"),
  thead: document.querySelector("#table thead tr"),
  tbody: document.querySelector("#table tbody"),
};

let latestSearch = 0;
let shown = null; // {keyword, ranked, nowMs} currently on screen, for the CSV button and chart redraws

// --- messages ---------------------------------------------------------------

// A status line, optionally with a "Try again" button that repeats a search
// (for failures that a second attempt can fix: network, GitHub's own errors).
function setStatus(text, isError = false, retryKeyword = null) {
  els.status.replaceChildren(text);
  els.status.classList.toggle("error", isError);
  if (retryKeyword !== null) {
    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "retry";
    retry.textContent = "Try again";
    retry.addEventListener("click", () => search(retryKeyword));
    els.status.append(" ", retry);
  }
}

// While a search runs, earlier results stay visible but dimmed (aria-busy),
// so a half-finished search never looks like a finished one.
function startLoading() {
  els.idle.hidden = true;
  els.results.classList.add("loading");
  els.results.setAttribute("aria-busy", "true");
  els.status.classList.add("loading");
}

function endLoading() {
  els.results.classList.remove("loading");
  els.results.removeAttribute("aria-busy");
  els.status.classList.remove("loading");
}

function showOnlyStatus(text, retryKeyword = null) {
  endLoading();
  els.results.hidden = true;
  shown = null;
  setStatus(text, true, retryKeyword);
}

function clockTime(ms) {
  return new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

// --- cache (localStorage, 24h; storage may be unavailable) ------------------

function readCache(key, nowMs) {
  try {
    const raw = window.localStorage.getItem(CACHE_PREFIX + key);
    if (raw === null) return null;
    const entry = JSON.parse(raw);
    // An entry without the incomplete flag is an older format: refetch, don't guess.
    if (!entry || typeof entry.incomplete !== "boolean" || !Array.isArray(entry.repos)) return null;
    if (nowMs - entry.fetchedAt > CACHE_TTL_MS) return null;
    return { totalCount: entry.totalCount, incomplete: entry.incomplete, repos: entry.repos, fetchedAt: entry.fetchedAt };
  } catch {
    return null; // blocked storage or corrupt entry: behave as a cache miss
  }
}

function writeCache(key, data, nowMs) {
  try {
    const entry = { v: 1, fetchedAt: nowMs, totalCount: data.totalCount, incomplete: data.incomplete, repos: data.repos };
    window.localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(entry));
  } catch {
    // storage blocked or full: the page still works, just without caching
  }
}

// --- rendering ------------------------------------------------------------

function renderTableHeader() {
  for (const name of TABLE_HEADERS) {
    const th = document.createElement("th");
    th.textContent = name;
    if (OPTIONAL_COLUMNS.has(name)) th.className = "optional";
    if (name === "#" || name === "Stars") th.classList.add("num");
    els.thead.append(th);
  }
}

// Only https links to github.com become clickable; anything else (a
// javascript: URL, another host) stays plain text.
function isGitHubUrl(url) {
  try {
    const u = new URL(url);
    return u.protocol === "https:" && u.hostname === "github.com";
  } catch {
    return false;
  }
}

function renderTable(ranked) {
  els.tbody.replaceChildren();
  ranked.forEach((repo, i) => {
    const tr = document.createElement("tr");
    tr.dataset.rank = String(i);
    tr.className = `row-${repo.bucket}`;
    row(i + 1, repo, "-").forEach((value, col) => {
      const td = document.createElement("td");
      const name = TABLE_HEADERS[col];
      if (name === "Bucket") {
        const pill = document.createElement("span");
        pill.className = `bucket ${value}`;
        pill.textContent = value;
        td.append(pill);
      } else if (name === "Repository") {
        // owner/<wbr>name as text nodes: plain text, but a narrow column breaks
        // after the slash instead of in the middle of a word. It links to the
        // repo only when GitHub's URL really points at github.com.
        const text = String(value);
        const slash = text.indexOf("/");
        const parts = slash === -1 ? [text] : [text.slice(0, slash + 1), document.createElement("wbr"), text.slice(slash + 1)];
        if (isGitHubUrl(repo.url)) {
          const link = document.createElement("a");
          link.href = repo.url;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          link.append(...parts);
          td.append(link);
        } else {
          td.append(...parts);
        }
      } else {
        td.textContent = String(value); // GitHub text always goes in as plain text
      }
      if (name === "#" || name === "Stars") td.classList.add("num");
      if (name === "Last Push") td.classList.add("date");
      if (name === "Repository") td.classList.add("repo");
      if (OPTIONAL_COLUMNS.has(name)) td.classList.add("optional");
      tr.append(td);
    });
    els.tbody.append(tr);
  });
}

// A stable pseudo-random height in 0.26..0.94 from a repo name (FNV-1a hash).
// The band below 0.26 belongs to the trace.
function spread(name) {
  let h = 2166136261;
  for (let i = 0; i < name.length; i++) {
    h ^= name.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return 0.26 + ((h >>> 0) % 1000) / 1000 * 0.68;
}

// The signature move: an ECG-style trace along the bottom of the strip. It
// runs flat and spikes at every repo's last push (taller for more stars), so a
// topic nobody pushes to lately flatlines across the active zone.
const TRACE_BASE = 0.08;
// Spike shapes are sized in pixels (px = one screen pixel in x units), so a
// beat looks the same on a phone as on a projector.
function tracePoints(points, maxStars, px) {
  const spikes = [];
  for (const p of [...points].sort((a, b) => a.x - b.x)) {
    const h = 0.03 + 0.11 * Math.sqrt(p.stars / (maxStars || 1));
    const last = spikes[spikes.length - 1];
    if (last && p.x - last.x < 7 * px) last.h = Math.max(last.h, h); // merge piles into one beat
    else spikes.push({ x: p.x, h });
  }
  // A square calibration pulse in the margin before "5+ years", as at the start
  // of every ECG lead; its flat top can't be mistaken for a repo's spike.
  const x0 = -0.1 + px;
  const w = Math.min(10 * px, 0.06);
  const line = [
    { x: -0.1, y: TRACE_BASE },
    { x: x0, y: TRACE_BASE },
    { x: x0, y: TRACE_BASE + 0.1 },
    { x: x0 + w, y: TRACE_BASE + 0.1 },
    { x: x0 + w, y: TRACE_BASE },
  ];
  for (const { x, h } of spikes) {
    line.push(
      { x: x - 4 * px, y: TRACE_BASE },
      { x: x - 2 * px, y: TRACE_BASE - 0.025 },
      { x, y: TRACE_BASE + h },
      { x: x + 2 * px, y: TRACE_BASE - 0.035 },
      { x: x + 4 * px, y: TRACE_BASE },
    );
  }
  line.push({ x: 3.08, y: TRACE_BASE });
  return line;
}

// The chart uses the stylesheet's colour tokens, so page and chart share one palette.
function token(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// Grid paper for the strip: 5 px minor squares, 25 px major ones, as on an ECG.
function addGridPattern(svg) {
  const ns = "http://www.w3.org/2000/svg";
  const make = (tag, attrs) => {
    const el = document.createElementNS(ns, tag);
    for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
    return el;
  };
  const pattern = make("pattern", { id: "ecg-grid", width: 25, height: 25, patternUnits: "userSpaceOnUse" });
  pattern.append(make("rect", { width: 25, height: 25, fill: token("--sheet") }));
  for (let i = 5; i < 25; i += 5) {
    pattern.append(make("path", { d: `M${i} 0V25M0 ${i}H25`, stroke: token("--grid-minor"), "stroke-width": 1 }));
  }
  pattern.append(make("path", { d: "M0 0V25M0 0H25", stroke: token("--grid-major"), "stroke-width": 1 }));
  const defs = make("defs", {});
  defs.append(pattern);
  svg.prepend(defs);
}

let dots = []; // the chart's circles, in table (rank) order, for the linked highlight

function light(rank) {
  els.chart.classList.toggle("focusing", rank !== null && dots.length > 0);
  dots.forEach((c, i) => c.classList.toggle("lit", i === rank));
  for (const tr of els.tbody.rows) tr.classList.toggle("lit", Number(tr.dataset.rank) === rank);
}

function renderChart(ranked, nowMs) {
  els.chart.replaceChildren();
  els.chart.classList.remove("focusing");
  els.chartNote.hidden = true;
  dots = [];
  if (typeof window.d3 === "undefined" || typeof window.Plot === "undefined") {
    els.chartNote.hidden = false;
    return;
  }
  try {
    const Plot = window.Plot;
    const narrow = els.chart.clientWidth < 520;
    const count = (bucket) => ranked.filter((r) => r.bucket === bucket).length;
    // Each zone is labelled with its share of the repos, in its own (darkened)
    // bucket colour, so the strip reads as alive or graveyard from across a room.
    // Short labels on narrow screens, or the three overlap at phone width.
    const zones = [
      { x1: 0, x2: 1, name: narrow ? "stale" : "stale · 1 year+", n: count(STALE), ink: token("--stale-label") },
      { x1: 1, x2: 2, name: narrow ? "slowing" : "slowing · 3–12 months", n: count(SLOWING), ink: token("--slowing-label") },
      { x1: 2, x2: 3, name: narrow ? "active" : "active · last 3 months", n: count(ACTIVE), ink: token("--active-label") },
    ].map((z) => ({ ...z, label: `${z.n} ${z.name}` }));
    // Vertical spread instead of stacking: many repos can share one x (a "now"
    // or "5+ years" pile), and a stacked column would spill out of the chart.
    // Each dot gets a fixed height from its name, so redraws look the same.
    // Points stay in rank (stars) order: big dots are drawn first, small ones
    // on top, and circle i is table row i.
    const points = ranked.map((r) => ({
      ...r,
      x: xPosition((nowMs - Date.parse(r.pushedAt)) / DAY_MS),
      y: spread(r.name),
      lastPush: lastPushDate(r.pushedAt),
    }));
    const maxStars = Math.max(0, ...points.map((p) => p.stars));
    const width = els.chart.clientWidth || 900;
    const px = (3.08 - -0.1) / Math.max(1, width - 40); // x units per pixel (Plot's default side margins are 20 px)
    const svg = Plot.plot({
      width,
      height: narrow ? 360 : 340,
      marginTop: 40,
      marginBottom: 34,
      style: { fontSize: "13px", fontFamily: "Archivo, system-ui, sans-serif", color: token("--ink-soft"), background: "transparent" },
      x: {
        domain: [-0.1, 3.08], // room so the "5+ years" and "now" piles sit inside the frame
        ticks: [0, 1, 2, 3],
        tickFormat: (t) => ["5+ years", "1 year", "90 days", "now"][t],
        label: null,
      },
      y: { axis: null, domain: [0, 1], inset: 10 },
      r: { range: [3, narrow ? 11 : 16] },
      color: { domain: [STALE, SLOWING, ACTIVE], range: [token("--stale-dot"), token("--slowing-dot"), token("--active-dot")] },
      marks: [
        Plot.frame({ fill: "white", className: "ecg-paper" }),
        Plot.ruleX([1, 2], { stroke: token("--zone-rule") }),
        Plot.text(zones, { x: (d) => (d.x1 + d.x2) / 2, text: "label", frameAnchor: "top", dy: -22, fill: "ink", fontSize: narrow ? 13 : 15, fontWeight: 650 }),
        Plot.line(tracePoints(points, maxStars, px), { x: "x", y: "y", stroke: token("--band"), strokeWidth: 1.6, strokeLinejoin: "round" }),
        Plot.dot(points, {
          x: "x",
          y: "y",
          r: "stars",
          fill: "bucket",
          fillOpacity: 0.85,
          stroke: "white",
          strokeWidth: 0.8,
          className: "dots",
          channels: { Repository: "name", Stars: "stars", "Last push": "lastPush" },
          tip: { format: { x: false, y: false, r: false, fill: false } },
        }),
      ],
    });
    addGridPattern(svg);
    els.chart.append(svg);
    drawnWidth = Math.round(width);
    dots = [...svg.querySelectorAll(".dots circle")];
    els.chart.setAttribute(
      "aria-label",
      `Heartbeat chart of ${ranked.length} repositories by time since last push: ${zones[2].n} active, ${zones[1].n} slowing, ${zones[0].n} stale`,
    );
  } catch (err) {
    console.error("RepoScout: chart failed to draw", err);
    els.chart.replaceChildren();
    els.chartNote.hidden = false;
    dots = [];
  }
}

// The verdict as a headline: same words as the CLI (spec), but the "<A> active"
// count is picked out and the "— most recent entrant…" tail is set smaller.
// Built from text nodes, so the element's textContent is exactly the verdict.
// Plain text, except that "best-matching" never breaks at its hyphen.
function textWithNowrap(text) {
  const at = text.indexOf("best-matching");
  if (at === -1) return [text];
  const keep = document.createElement("span");
  keep.className = "nowrap";
  keep.textContent = "best-matching";
  return [text.slice(0, at), keep, text.slice(at + "best-matching".length)];
}

function renderVerdict(text, activeCount) {
  els.verdict.replaceChildren();
  const dash = text.indexOf(" — ");
  const head = dash === -1 ? text : text.slice(0, dash);
  const tail = dash === -1 ? "" : text.slice(dash);
  const match = /\b\d+ active\b/.exec(head);
  if (match) {
    const count = document.createElement("span");
    count.className = activeCount > 0 ? "count active" : "count none";
    count.textContent = match[0];
    els.verdict.append(...textWithNowrap(head.slice(0, match.index)), count, head.slice(match.index + match[0].length));
  } else {
    els.verdict.append(...textWithNowrap(head));
  }
  if (tail) {
    const rest = document.createElement("span");
    rest.className = "verdict-tail";
    rest.textContent = tail;
    els.verdict.append(rest);
  }
}

function render(keyword, data) {
  const nowMs = Date.now();
  const ranked = rankByStars(data.repos).map((r) => ({ ...r, bucket: bucketFor(Date.parse(r.pushedAt), nowMs) }));
  shown = { keyword, ranked, nowMs };
  endLoading();
  setStatus("");
  els.results.hidden = false;
  renderVerdict(formatVerdict(data.totalCount, ranked, nowMs), ranked.filter((r) => r.bucket === ACTIVE).length);
  els.incomplete.hidden = !data.incomplete;
  const none = ranked.length === 0;
  els.empty.hidden = !none;
  els.emptyKeyword.textContent = keyword.trim();
  for (const part of [els.heartbeat, els.tableHead, els.tableWrap]) part.hidden = none;
  // Verdict and table first: whatever happens to the chart, they are on screen.
  renderTable(ranked);
  els.csv.hidden = ranked.length === 0;
  renderChart(ranked, nowMs);
  els.printout.textContent = printoutLine(ranked.length, data.totalCount, data.fetchedAt, nowMs);
  // Screen readers heard "Scouting GitHub…"; now they hear the answer.
  els.announce.textContent = els.verdict.textContent + (data.incomplete ? ". " + els.incomplete.textContent : "");
}

// The line printed on the sheet's margin, like "25 mm/s · 10 mm/mV" on an ECG:
// where the data came from, how much of it, and when it was fetched (a cached
// result says so by its time).
function printoutLine(fetched, total, fetchedAt, nowMs) {
  const when = new Date(fetchedAt);
  const sameDay = new Date(nowMs).toDateString() === when.toDateString();
  const time = when.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const stamp = sameDay ? time : `${when.toLocaleDateString([], { day: "numeric", month: "short" })} ${time}`;
  return `GitHub search · ${fetched} of ${groupThousands(total)} repos · fetched ${stamp}`; // numbers as the verdict prints them
}

// --- search ---------------------------------------------------------------

async function errorDetail(response) {
  try {
    const body = await response.json();
    return body && typeof body === "object" && typeof body.message === "string" ? body.message : "";
  } catch {
    return "";
  }
}

async function search(keyword) {
  const id = ++latestSearch;
  const isLatest = () => id === latestSearch;
  const key = normalizeQuery(keyword);
  els.idle.hidden = true; // the blank start sheet goes once a search begins

  const cached = readCache(key, Date.now());
  if (cached) {
    render(keyword, cached);
    return;
  }

  startLoading();
  setStatus(`Scouting GitHub for “${keyword.trim()}”…`);
  const url = `${SEARCH_URL}?q=${encodeURIComponent(keyword)}&per_page=50`;
  let response;
  // A request that hangs (bad Wi-Fi) ends after 20 s instead of leaving the
  // page on "Scouting GitHub…" forever.
  const timeout = new AbortController();
  const timer = setTimeout(() => timeout.abort(), FETCH_TIMEOUT_MS);
  try {
    response = await fetch(url, { headers: { Accept: "application/vnd.github+json" }, signal: timeout.signal });
  } catch (err) {
    if (!isLatest()) return;
    console.error("RepoScout: request failed", url, err);
    showOnlyStatus(timeout.signal.aborted
      ? "Could not reach GitHub: there was no answer within 20 seconds. Check your connection, then try again."
      : "Could not reach GitHub. Check your internet connection, then try again.", keyword);
    return;
  } finally {
    clearTimeout(timer);
  }
  if (!isLatest()) return;

  if (!response.ok) {
    if (isRateLimited(response.status, response.headers)) {
      const at = resetAt(response.headers, Date.now());
      showOnlyStatus(at === null
        ? "Too many searches for now: GitHub allows 10 a minute without signing in. GitHub gave no reset time, so wait a minute and search again."
        : `Too many searches for now: GitHub allows 10 a minute without signing in. Search again after ${clockTime(at)}.`);
      return;
    }
    const detail = await errorDetail(response);
    if (!isLatest()) return;
    console.error("RepoScout: GitHub error", url, response.status, detail);
    const code = `HTTP ${response.status}${detail ? `: ${detail}` : ""}`;
    if (response.status >= 500) {
      showOnlyStatus(`GitHub had a problem on its side (${code}). Try again in a moment.`, keyword);
    } else {
      showOnlyStatus(`GitHub couldn't run this search (${code}). Try different words, without unusual symbols.`);
    }
    return;
  }

  let data;
  try {
    data = parseSearchPayload(JSON.parse(await response.text()));
  } catch (err) {
    if (!isLatest()) return;
    if (!(err instanceof SyntaxError) && !(err instanceof UnexpectedResponse)) throw err;
    console.error("RepoScout: unexpected response", url, err);
    showOnlyStatus("GitHub sent a response RepoScout doesn't understand. If this Wi-Fi has a login page, sign in there, then try again.", keyword);
    return;
  }
  if (!isLatest()) return;

  const fetchedAt = Date.now();
  writeCache(key, data, fetchedAt);
  render(keyword, { ...data, fetchedAt });
}

els.form.addEventListener("submit", (event) => {
  event.preventDefault();
  const keyword = els.keyword.value;
  if (keyword.trim() === "") {
    setStatus("Type a topic first, for example “expense tracker”.", true);
    return;
  }
  search(keyword);
});

els.csv.addEventListener("click", () => {
  if (!shown) return;
  try {
    const blob = new Blob([csvText(shown.ranked)], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = csvFilename(shown.keyword);
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);
  } catch (err) {
    console.error("RepoScout: CSV download failed", err);
    setStatus("This browser couldn't create the CSV download.", true);
  }
});

// Example topics in the header: fill the box and search.
for (const button of document.querySelectorAll(".topic")) {
  button.addEventListener("click", () => {
    els.keyword.value = button.textContent;
    els.form.requestSubmit();
  });
}

// Linked highlight: pointing at (or tabbing into) a table row lifts its dot.
const rankOf = (event) => {
  const tr = event.target.closest && event.target.closest("tr[data-rank]");
  return tr ? Number(tr.dataset.rank) : null;
};
els.tbody.addEventListener("mouseover", (e) => light(rankOf(e)));
els.tbody.addEventListener("focusin", (e) => light(rankOf(e)));
els.tbody.addEventListener("mouseleave", () => light(null));
els.tbody.addEventListener("focusout", () => light(null));

// The chart is drawn for the width it has. When that width changes (window
// resized, phone rotated), draw it again for the new width, with the same data
// and the same "now", once the resizing has settled.
let drawnWidth = 0;
let redrawTimer = 0;
if (typeof ResizeObserver !== "undefined") {
  new ResizeObserver((entries) => {
    const width = Math.round(entries[0].contentRect.width);
    if (!shown || shown.ranked.length === 0 || width === 0 || width === drawnWidth) return;
    clearTimeout(redrawTimer);
    redrawTimer = setTimeout(() => {
      drawnWidth = width;
      renderChart(shown.ranked, shown.nowMs);
    }, 150);
  }).observe(els.chart);
}

renderTableHeader();
