// RepoScout's rules for the web page: pure functions, no DOM, no network.
// They copy the Python CLI (reposcout/bucketing.py, output.py, cache.py,
// github.py). Two implementations, one shared test fixture: both test runs
// (pytest and node --test) check tests/fixtures/rules.json, so a rule changed
// in only one language fails a test. "now" is always passed in, in ms.

export const ACTIVE_THRESHOLD_DAYS = 90;
export const STALE_THRESHOLD_DAYS = 365;

export const ACTIVE = "active";
export const SLOWING = "slowing";
export const STALE = "stale";

export const TABLE_HEADERS = ["#", "Repository", "Stars", "Last Push", "Language", "Bucket"];
export const CSV_HEADERS = [...TABLE_HEADERS, "URL"];

const DAY_MS = 86400 * 1000;
const PUSHED_AT_FORMAT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;

// --- bucketing.py ---------------------------------------------------------

export function bucketFor(pushedAtMs, nowMs) {
  const ageDays = (nowMs - pushedAtMs) / DAY_MS;
  if (ageDays < ACTIVE_THRESHOLD_DAYS) return ACTIVE;
  if (ageDays < STALE_THRESHOLD_DAYS) return SLOWING;
  return STALE;
}

export function activeWindowText() {
  const months = Math.round(ACTIVE_THRESHOLD_DAYS / 30);
  return months * 30 === ACTIVE_THRESHOLD_DAYS ? `${months} months` : `${ACTIVE_THRESHOLD_DAYS} days`;
}

export function rankByStars(repos) {
  return [...repos].sort((a, b) => b.stars - a.stars);
}

// --- output.py ------------------------------------------------------------

function count(n, unit) {
  return n === 1 ? `${n} ${unit}` : `${n} ${unit}s`;
}

// Always rounded down, so the shown time is never later than the truth.
export function timeAgo(deltaMs) {
  const seconds = Math.max(Math.trunc(deltaMs / 1000), 0); // clock skew -> "just now"
  const days = Math.floor(seconds / 86400);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${count(Math.floor(seconds / 60), "minute")} ago`;
  if (days < 1) return `${count(Math.floor(seconds / 3600), "hour")} ago`;
  if (days < 14) return `${count(days, "day")} ago`;
  if (days < 90) return `${count(Math.floor(days / 7), "week")} ago`;
  if (days < 365) return `${count(Math.floor(days / 30), "month")} ago`;
  const years = Math.floor(days / 365);
  const months = Math.min(Math.floor((days % 365) / 30), 11);
  if (months === 0) return `${count(years, "year")} ago`;
  return `${count(years, "year")}, ${count(months, "month")} ago`;
}

// repos: [{pushedAt: ISO string, bucket}]; counts only ever describe the fetched repos.
// A comma every three digits ("244,832"), the same in every browser language,
// as Python's "{:,}" does it (toLocaleString would follow the browser's locale).
export function groupThousands(n) {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

export function formatVerdict(totalCount, repos, nowMs) {
  if (repos.length === 0) return "0 repos found";
  const activeCount = groupThousands(repos.filter((r) => r.bucket === ACTIVE).length);
  const mostRecentMs = Math.max(...repos.map((r) => Date.parse(r.pushedAt)));
  const pushedAgo = timeAgo(nowMs - mostRecentMs);
  if (totalCount <= repos.length) {
    return `${groupThousands(totalCount)} repos found, ${activeCount} active in the last ${activeWindowText()} — most recent entrant pushed ${pushedAgo}`;
  }
  return `Showing the ${groupThousands(repos.length)} best-matching of ${groupThousands(totalCount)} repos, ${activeCount} active among them — most recent entrant pushed ${pushedAgo}`;
}

// Filename-unsafe characters on Windows (only "/" on macOS/Linux), control
// characters and whitespace: each run becomes one hyphen (output.py).
const UNSAFE_FILENAME_RUN = /[<>:"/\\|?*\x00-\x1f\x7f\s]+/g;

export function slugifyKeyword(keyword) {
  const slug = normalizeQuery(keyword)
    .replace(UNSAFE_FILENAME_RUN, "-")
    .replace(/-{2,}/g, "-")
    .replace(/^[-.]+|[-.]+$/g, "");
  return slug || "search";
}

export function csvFilename(keyword) {
  return `${slugifyKeyword(keyword)}-report.csv`;
}

// The UTC date of pushed_at, as Python's pushed_at.date() - never local time.
export function lastPushDate(pushedAt) {
  return pushedAt.slice(0, 10);
}

// One table/CSV row in TABLE_HEADERS order (output.py _row).
export function row(rank, repo, missingLanguage) {
  return [rank, repo.name, repo.stars, lastPushDate(repo.pushedAt), repo.language || missingLanguage, repo.bucket];
}

// Python's csv module: quote only fields with a comma, quote, CR or LF; CRLF line ends.
function csvField(value) {
  const text = String(value);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function csvText(rankedRepos) {
  const lines = [CSV_HEADERS, ...rankedRepos.map((r, i) => [...row(i + 1, r, ""), r.url])];
  return lines.map((fields) => fields.map(csvField).join(",") + "\r\n").join("");
}

// --- cache.py -------------------------------------------------------------

// Trim, collapse whitespace, case-fold. JS has no exact casefold(): toLowerCase
// plus "ß" -> "ss" matches Python for the fixture's cases (ASCII, Hungarian, ß).
export function normalizeQuery(keyword) {
  return keyword.trim().replace(/\s+/g, " ").toLowerCase().replace(/ß/g, "ss");
}

// --- github.py ------------------------------------------------------------

function header(headers, name) {
  if (headers && typeof headers.get === "function") return headers.get(name);
  const key = Object.keys(headers || {}).find((k) => k.toLowerCase() === name.toLowerCase());
  return key === undefined ? null : headers[key];
}

// _is_rate_limited: any 429; a 403 only with Remaining 0 or a Retry-After header.
export function isRateLimited(status, headers) {
  if (status === 429) return true;
  if (status === 403) {
    return header(headers, "X-RateLimit-Remaining") === "0" || header(headers, "Retry-After") !== null;
  }
  return false;
}

// _parse_reset_time: numeric Retry-After first, then X-RateLimit-Reset; null if
// GitHub gave no reset time (never invent one). Returns epoch milliseconds.
export function resetAt(headers, nowMs) {
  const retryAfter = header(headers, "Retry-After");
  if (retryAfter !== null && /^\d+$/.test(retryAfter)) return nowMs + Number(retryAfter) * 1000;
  const reset = header(headers, "X-RateLimit-Reset");
  if (reset !== null) return Number(reset) * 1000;
  return null;
}

export class UnexpectedResponse extends Error {}

// search_repositories' parsing: missing or wrongly shaped fields mean this is
// not a search response we understand (never "0 repos found").
export function parseSearchPayload(payload) {
  const ok = payload !== null && typeof payload === "object" && !Array.isArray(payload);
  if (!ok || !("total_count" in payload) || !("incomplete_results" in payload) || !Array.isArray(payload.items)) {
    throw new UnexpectedResponse("missing total_count, items or incomplete_results");
  }
  const repos = payload.items.map((item) => {
    for (const key of ["full_name", "html_url", "stargazers_count", "pushed_at", "language"]) {
      if (item === null || typeof item !== "object" || !(key in item)) {
        throw new UnexpectedResponse(`item missing ${key}`);
      }
    }
    if (typeof item.pushed_at !== "string" || !PUSHED_AT_FORMAT.test(item.pushed_at) || Number.isNaN(Date.parse(item.pushed_at))) {
      throw new UnexpectedResponse("item has an unreadable pushed_at");
    }
    return {
      name: item.full_name,
      url: item.html_url,
      stars: item.stargazers_count,
      pushedAt: item.pushed_at,
      language: item.language,
    };
  });
  return { totalCount: payload.total_count, incomplete: Boolean(payload.incomplete_results), repos };
}

// --- heartbeat strip axis --------------------------------------------------

// Days since last push -> 0..3 on equal-width zones: stale 365d..5y -> 0..1
// (older pinned at 0), slowing 90..365d -> 1..2, active 0..90d -> 2..3.
export function xPosition(days) {
  const d = Math.max(days, 0);
  if (d <= ACTIVE_THRESHOLD_DAYS) return 3 - d / ACTIVE_THRESHOLD_DAYS;
  if (d <= STALE_THRESHOLD_DAYS) return 2 - (d - ACTIVE_THRESHOLD_DAYS) / (STALE_THRESHOLD_DAYS - ACTIVE_THRESHOLD_DAYS);
  const fiveYears = 5 * 365;
  if (d >= fiveYears) return 0;
  return 1 - (d - STALE_THRESHOLD_DAYS) / (fiveYears - STALE_THRESHOLD_DAYS);
}
