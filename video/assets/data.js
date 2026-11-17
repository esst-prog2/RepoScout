// The one data module for the film. Every number and position comes from the
// 26 October 2026 search for "project management software" (docs/screenshots/3-...png).
// Dot positions are in that screenshot's pixels (the strip spans x 224-1217, y 527-790);
// r is the dot radius in the same pixels. See SPEC.md "DATA".
window.RS = {
  total: 14067,
  shown: 50,
  counts: { stale: 36, slowing: 4, active: 10 },
  verdict: "Showing the 50 best-matching of 14,067 repos, 10 active among them",
  tail: "— most recent entrant pushed 1 minute ago",
  sheet: { x0: 224, y0: 527, w: 993, h: 263, baseline: 765,
           axis: [[255, "5+ years"], [567, "1 year"], [879, "90 days"], [1191, "now"]],
           rules: [567, 879] },
  dots: [
    // stale: found in the screenshot
    ["stale",255,561,3],["stale",255,578,3],["stale",255,584,3],["stale",255,595,2.5],["stale",255,600,2.5],
    ["stale",255,608,3],["stale",255,629,3],["stale",255,635,3],["stale",255,647,3],["stale",255,657,3.5],
    ["stale",255,662,3.5],["stale",255,675,3],["stale",255,686,2.5],["stale",255,693,3.5],["stale",255,717,3.5],
    ["stale",266,591,3],["stale",279,661,5.5],["stale",289,574,3],["stale",328,608,3.5],["stale",337,603,2.5],
    ["stale",348,609,3.5],["stale",353,697,2.5],["stale",438,610,3],["stale",461,688,3],["stale",472,703,2.5],
    ["stale",476,712,2.5],["stale",492,652,3],["stale",504,702,3],["stale",555,594,4],
    // stale: hidden in the overlapping "5+ years" pile, placed in that pile
    ["stale",255,570,2.5],["stale",255,615,2.5],["stale",255,622,2.5],["stale",255,641,2.5],
    ["stale",255,668,2.5],["stale",255,680,2.5],["stale",255,705,2.5],
    // slowing
    ["slowing",654,674,3.5],["slowing",761,605,5],["slowing",791,658,3],["slowing",858,696,4],
    // active
    ["active",1038,594,5.5],["active",1044,570,4.5],["active",1120,555,3],["active",1177,571,3],
    ["active",1177,638,3],["active",1182,671,12.5],["active",1188,698,7.5],["active",1191,578,3],
    ["active",1191,595,3.5],["active",1196,681,14.5]
  ]
};
