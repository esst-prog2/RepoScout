# Promo page images

How each image here was made. This file is not published (`scripts/build_pages.py` leaves it out).

All three images are cut from the 26 October 2026 screenshots in `docs/screenshots/`. Nothing was retaken, and the originals are untouched, so every number matches README §1 and the screenshots. The tool is `ffmpeg`, and every source image is 1440 × 900.

## Hero leads: `lead-mcp-server.png`, `lead-angularjs-directive.png`

Both use the same crop box: 1036 × 330 at x 200, y 495. It runs from the zone labels down to the axis labels, so the two time axes line up exactly.

```
ffmpeg -i docs/screenshots/1-alive-mcp-server.png -vf "crop=1036:330:200:495" promo/img/lead-mcp-server.png
ffmpeg -i docs/screenshots/2-graveyard-angularjs-directive.png -vf "crop=1036:330:200:495" promo/img/lead-angularjs-directive.png
```

The verdict sentences above the leads are HTML text in `promo/index.html`, copied from the same screenshots.

## Ranked table: `table-csv.png`

This is screenshot 4 (`4-table-csv-project-management-software.png`) with the account part of every repository name blurred. Account names such as `brettkromkamp/` can be people's names, and the instructor's rule for the published site is no real names. Repository names, numbers, buckets and the Download CSV button stay sharp. The original screenshot 4 is never published.

**Finding the boxes.** For each row, the end of the `owner/` part was found by measuring the row's name with the vendored Archivo font (Pillow `ImageFont.getlength`). The measurement was scaled to the name's width in the screenshot, and the box stops 4 px before the slash so the slash stays visible.

**Blurring.** Each box was shrunk to (width ÷ 9) × 3 pixels, scaled back up with bilinear filtering, then laid over the original:

```
[0:v]crop=W:H:X:Y,scale=max(2,W/9):3,scale=W:H:flags=bilinear[bN];[prev][bN]overlay=X:Y[oN]   (one pair per row)
```

The result was checked by eye at 100 % and at 3× zoom: no account name can be read.

| Row | Blurred box (x, y, width, height) |
|---:|---|
| 1 | 264, 120, 24, 21 |
| 2 | 264, 155, 65, 19 |
| 3 | 264, 190, 81, 21 |
| 4 | 264, 226, 46, 21 |
| 5 | 264, 261, 105, 21 |
| 6 | 264, 296, 71, 21 |
| 7 | 264, 331, 28, 20 |
| 8 | 264, 367, 46, 20 |
| 9 | 264, 402, 72, 21 |
| 10 | 264, 437, 61, 20 |
| 11 | 264, 473, 150, 21 |
| 12 | 264, 508, 87, 21 |
| 13 | 264, 543, 83, 21 |
| 14 | 264, 579, 94, 21 |
| 15 | 264, 614, 75, 21 |
| 16 | 264, 649, 78, 21 |
| 17 | 264, 685, 77, 21 |
| 18 | 264, 720, 73, 21 |
| 19 | 264, 755, 93, 21 |
| 20 | 264, 791, 41, 21 |
| 21 | 264, 826, 107, 21 |
| 22 | 264, 861, 98, 20 |
