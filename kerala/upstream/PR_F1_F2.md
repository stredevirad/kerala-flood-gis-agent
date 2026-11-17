# Fix `count_in_polygon` empty-polygon count and reject terrain ops on geographic DEMs

Two small correctness fixes in `src/agent/geo_ops.py`, found while building a flood-mapping benchmark on GISclaw. Each comes with a regression test. Patches: `F1.patch`, `F2.patch` (source only; the tests live in our fork's `tests/test_kerala_fixes.py` and are reproduced below in outline).

## F1 — `count_in_polygon` reports 1 for polygons that contain no points

**Cause.** `_b_count_in_polygon` does `sjoin(polygons, points, how="left")` and then `groupby(index).size()`. A left join keeps one row with a null right index for every polygon without a match, and `.size()` counts that row, so an empty polygon gets a count of 1.

**Fix.** Count non-null right-index values instead: find the `index_right*` column by its prefix and use `groupby(level=0)[col].count()`.

| Case (2 polygons A, B; 2 points, both inside A) | A | B |
|---|---:|---:|
| Before | 2 | **1** |
| After | 2 | **0** |

Test: `test_count_in_polygon_does_not_count_empty_left_join_rows`.

## F2 — slope/aspect/hillshade on a geographic-CRS DEM return nonsense

**Cause.** `_terrain` takes the pixel size from the affine transform. On a geographic DEM that size is in degrees, while elevations are in metres, so gradients are inflated by roughly 10⁵: a gentle 0.57° slope comes out as about 89.95°.

**Fix.** The generated code checks `_meta['crs']`; if it is geographic it prints a single `❌` line telling the agent to reproject the DEM to a projected CRS, and computes nothing (so no silently wrong raster is produced). Projected DEMs are unchanged.

| Case | Before | After |
|---|---:|---:|
| 1 % ramp on a projected (metre) grid | ≈ 0.57° | ≈ 0.57° (unchanged) |
| Same ramp on a geographic (degree) grid | ≈ 89.95° | `❌` "The DEM must be reprojected to a projected CRS…", no output |

Tests: `test_slope_of_projected_one_percent_ramp_is_about_057_degrees` and `test_terrain_skips_geographic_crs` (parametrised over slope, aspect, hillshade).

## Notes
- No behaviour change for valid inputs; both fixes are local to the generated code templates.
- Licence: AGPL-3.0-or-later, same as GISclaw.
- Other issues we documented but did not change: `ErrorMemory.record` is effectively dead code (its condition is checked after `last_action_failed` is overwritten); `_raster_tail` writes multi-band output with `count=1`; `load_raster` reads whole rasters as float64; there are no `area` or `nearest` ops; and `app.runner.DATA_BLOCK` describes files under `data/` while the agent sees them under `dataset/` (our F6).
