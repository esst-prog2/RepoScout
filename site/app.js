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
  thead: document.querySelector("#table thead tr"),
  tbody: document.querySelector("#table tbody"),
};

let latestSearch = 0;
let shown = null; // {keyword, ranked} currently on screen, for the CSV button

// --- messages ---------------------------------------------------------------

function setStatus(text, isError = false) {
  els.status.textContent = text;
  els.status.classList.toggle("error", isError);
}

function showOnlyStatus(text, isError = true) {
  els.results.hidden = true;
  shown = null;
  setStatus(text, isError);
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
    return { totalCount: entry.totalCount, incomplete: entry.incomplete, repos: entry.repos };
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
    els.thead.append(th);
  }
}

function renderTable(ranked) {
  els.tbody.replaceChildren();
  ranked.forEach((repo, i) => {
    const tr = document.createElement("tr");
    row(i + 1, repo, "-").forEach((value, col) => {
      const td = document.createElement("td");
      const name = TABLE_HEADERS[col];
      if (name === "Bucket") {
        const pill = document.createElement("span");
        pill.className = `bucket ${value}`;
        pill.textContent = value;
        td.append(pill);
      } else {
        td.textContent = String(value); // GitHub text always goes in as plain text
      }
      if (name === "#" || name === "Stars") td.classList.add("num");
      if (OPTIONAL_COLUMNS.has(name)) td.classList.add("optional");
      tr.append(td);
    });
    els.tbody.append(tr);
  });
}

function renderChart(ranked, nowMs) {
  els.chart.replaceChildren();
  els.chartNote.hidden = true;
  if (typeof window.d3 === "undefined" || typeof window.Plot === "undefined") {
    els.chartNote.hidden = false;
    return;
  }
  try {
    const Plot = window.Plot;
    const narrow = els.chart.clientWidth < 520;
    // Short labels on narrow screens, or the three overlap at phone width.
    const zones = [
      { x1: 0, x2: 1, label: narrow ? "stale" : "stale (1 year+)", fill: "#f0f0ee" },
      { x1: 1, x2: 2, label: narrow ? "slowing" : "slowing (3–12 months)", fill: "#faf3e3" },
      { x1: 2, x2: 3, label: narrow ? "active" : "active (last 3 months)", fill: "#e6f2e8" },
    ];
    const points = ranked.map((r) => ({
      ...r,
      x: xPosition((nowMs - Date.parse(r.pushedAt)) / DAY_MS),
      lastPush: lastPushDate(r.pushedAt),
    }));
    const svg = Plot.plot({
      width: els.chart.clientWidth || 900,
      height: narrow ? 300 : 230,
      marginTop: 28,
      marginBottom: 32,
      x: {
        domain: [0, 3],
        ticks: [0, 1, 2, 3],
        tickFormat: (t) => ["5+ years", "1 year", "90 days", "now"][t],
        label: null,
      },
      y: { axis: null },
      r: { range: [2, narrow ? 12 : 16] },
      color: { domain: [STALE, SLOWING, ACTIVE], range: ["#a5a8ad", "#e8a317", "#2b8a3e"] },
      marks: [
        Plot.rect(zones, { x1: "x1", x2: "x2", fill: "fill" }),
        Plot.text(zones, { x: (d) => (d.x1 + d.x2) / 2, text: "label", frameAnchor: "top", dy: -16, fill: "#5f6368", fontSize: 11 }),
        Plot.dot(points, Plot.dodgeY({
          anchor: "middle",
          x: "x",
          r: "stars",
          fill: "bucket",
          stroke: "white",
          strokeWidth: 0.6,
          padding: 1,
          channels: { Repository: "name", Stars: "stars", "Last push": "lastPush" },
          tip: { format: { x: false, y: false, r: false, fill: false } },
        })),
      ],
    });
    els.chart.append(svg);
    els.chart.setAttribute("aria-label", `Heartbeat chart of ${ranked.length} repositories by time since last push`);
  } catch (err) {
    console.error("RepoScout: chart failed to draw", err);
    els.chart.replaceChildren();
    els.chartNote.hidden = false;
  }
}

function render(keyword, data) {
  const nowMs = Date.now();
  const ranked = rankByStars(data.repos).map((r) => ({ ...r, bucket: bucketFor(Date.parse(r.pushedAt), nowMs) }));
  shown = { keyword, ranked };
  setStatus("");
  els.results.hidden = false;
  els.verdict.textContent = formatVerdict(data.totalCount, ranked, nowMs);
  els.incomplete.hidden = !data.incomplete;
  // Verdict and table first: whatever happens to the chart, they are on screen.
  renderTable(ranked);
  els.csv.hidden = ranked.length === 0;
  renderChart(ranked, nowMs);
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

  const cached = readCache(key, Date.now());
  if (cached) {
    render(keyword, cached);
    return;
  }

  setStatus("Scouting GitHub…");
  const url = `${SEARCH_URL}?q=${encodeURIComponent(keyword)}&per_page=50`;
  let response;
  try {
    response = await fetch(url, { headers: { Accept: "application/vnd.github+json" } });
  } catch (err) {
    if (!isLatest()) return;
    console.error("RepoScout: request failed", url, err);
    showOnlyStatus("Could not reach GitHub. Check your internet connection and try again.");
    return;
  }
  if (!isLatest()) return;

  if (!response.ok) {
    if (isRateLimited(response.status, response.headers)) {
      const at = resetAt(response.headers, Date.now());
      showOnlyStatus(at === null
        ? "GitHub allows 10 searches a minute without signing in, and that limit is reached. GitHub gave no reset time; try again in a minute or two."
        : `GitHub allows 10 searches a minute without signing in, and that limit is reached. Try again after ${clockTime(at)}.`);
      return;
    }
    const detail = await errorDetail(response);
    if (!isLatest()) return;
    console.error("RepoScout: GitHub error", url, response.status, detail);
    showOnlyStatus(`GitHub returned an error (HTTP ${response.status})${detail ? `: ${detail}` : "."}`);
    return;
  }

  let data;
  try {
    data = parseSearchPayload(JSON.parse(await response.text()));
  } catch (err) {
    if (!isLatest()) return;
    if (!(err instanceof SyntaxError) && !(err instanceof UnexpectedResponse)) throw err;
    console.error("RepoScout: unexpected response", url, err);
    showOnlyStatus("GitHub sent a response RepoScout doesn't understand. If you're on a Wi-Fi with a login page, sign in there and try again.");
    return;
  }
  if (!isLatest()) return;

  writeCache(key, data, Date.now());
  render(keyword, data);
}

els.form.addEventListener("submit", (event) => {
  event.preventDefault();
  const keyword = els.keyword.value;
  if (keyword.trim() === "") {
    setStatus("Type a topic to search, for example \"expense tracker\".", true);
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

renderTableHeader();
