// Shared rules fixture, JavaScript side: the same tests/fixtures/rules.json that
// tests/test_rules_fixture.py checks against the Python CLI, run through the web
// page's site/rules.js. Run with: node --test "tests/js/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import {
  bucketFor,
  csvFilename,
  csvText,
  formatVerdict,
  isRateLimited,
  normalizeQuery,
  parseSearchPayload,
  rankByStars,
  resetAt,
  timeAgo,
  UnexpectedResponse,
  xPosition,
} from "../../site/rules.js";

const FIXTURE = JSON.parse(readFileSync(new URL("../fixtures/rules.json", import.meta.url), "utf-8"));
const NOW = Date.parse(FIXTURE.now);

const withBucket = (r) => ({ ...r, pushedAt: r.pushed_at, bucket: bucketFor(Date.parse(r.pushed_at), NOW) });

for (const c of FIXTURE.bucket) {
  test(`bucket ${c.pushed_at}`, () => assert.equal(bucketFor(Date.parse(c.pushed_at), NOW), c.expected));
}

for (const c of FIXTURE.time_ago) {
  test(`timeAgo ${c.seconds}s`, () => assert.equal(timeAgo(c.seconds * 1000), c.expected));
}

for (const c of FIXTURE.verdict) {
  test(`verdict ${c.name}`, () => assert.equal(formatVerdict(c.total_count, c.repos.map(withBucket), NOW), c.expected));
}

for (const c of FIXTURE.normalize) {
  test(`normalize ${JSON.stringify(c.input)}`, () => assert.equal(normalizeQuery(c.input), c.expected));
}

for (const c of FIXTURE.filename) {
  test(`filename ${JSON.stringify(c.input)}`, () => assert.equal(csvFilename(c.input), c.expected));
}

test("csv text matches Python's csv module", () => {
  assert.equal(csvText(FIXTURE.csv.repos.map(withBucket)), FIXTURE.csv.expected);
});

for (const c of FIXTURE.rate_limit) {
  // Like the CLI, only a non-OK response can be a rate limit.
  test(`rate limit ${c.name}`, () => {
    const ok = c.status >= 200 && c.status < 300;
    assert.equal(!ok && isRateLimited(c.status, c.headers), c.limited);
  });
}

for (const c of FIXTURE.reset) {
  test(`reset ${c.name}`, () => {
    const expected = c.expected === null ? null
      : "epoch" in c.expected ? c.expected.epoch * 1000
      : NOW + c.expected.retry_after_seconds * 1000;
    assert.equal(resetAt(c.headers, NOW), expected);
  });
}

for (const c of FIXTURE.payload) {
  test(`payload ${c.name}`, () => {
    if (c.valid) assert.equal(parseSearchPayload(c.body).repos.length, c.body.items.length);
    else assert.throws(() => parseSearchPayload(c.body), UnexpectedResponse);
  });
}

for (const c of FIXTURE.x_position) {
  test(`xPosition ${c.days} days`, () => assert.ok(Math.abs(xPosition(c.days) - c.expected) < 1e-9));
}

test("display order is by stars, whatever order GitHub returns", () => {
  const ranked = rankByStars([{ stars: 5 }, { stars: 300 }, { stars: 40 }]);
  assert.deepEqual(ranked.map((r) => r.stars), [300, 40, 5]);
});
