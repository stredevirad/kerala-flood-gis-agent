[Part A: Shared context](../MASTERPROMPT.md#part-a-shared-context-applies-to-every-session)

## Phase 4: Benchmark questions, gold, review (STOP gate; freeze only after approval)

### `kerala\bench\questions.yaml`

Each entry has these fields:
- `id`
- `split` (`test` or `dev`)
- `type`
- `needs_params`
- `expected_status` (`ok` or `cannot_answer`)
- `expected_unit` (null for `cannot_answer` questions)
- `text`

Use these questions exactly. Change wording only if a layer name differs from the one written here.

**Parameter questions** (run in A1, A2 and A3):

| id | text | needs_params | unit |
|---|---|---|---|
| P01 | How many mapped hospitals in Alappuzha district were inside the flood extent on 21 August 2018? | facility_point_rule | count |
| P02 | How many mapped schools in Ernakulam district were inside the flood extent on 21 August 2018? | facility_point_rule | count |
| P03 | How many mapped schools in Alappuzha district (candidate relief camps) had no hospital within the relief-camp hospital access distance? | relief_camp_hospital_access_m, facility_point_rule | count |
| P04 | Which taluk in Ernakulam or Alappuzha has the most mapped schools with no hospital within the relief-camp hospital access distance? | relief_camp_hospital_access_m, facility_point_rule | name |
| P05 | Using only the Sentinel-1 VV image of 21 August 2018, what area of Alappuzha district (km²) appears as open water? | water_threshold_vv_db, raster_area_rule | km2 |
| P06 | Using the Sentinel-1 VV image of 21 August 2018, excluding permanent water bodies and steep slopes, what area of Ernakulam district (km²) was flooded? | water_threshold_vv_db, permanent_water_rule, max_flood_slope_deg, raster_area_rule | km2 |
| P07 | Using the Sentinel-1 VV image of 21 August 2018, excluding permanent water bodies and steep slopes, what percentage of Kuttanad taluk was flooded? | water_threshold_vv_db, permanent_water_rule, max_flood_slope_deg, raster_area_rule | percent |
| P08 | How much low-lying land (km²) in Alappuzha district lay inside the flood extent on 21 August 2018? | low_lying_max_elevation_m, raster_area_rule | km2 |
| P09 | How many mapped hospitals in the two districts stand on low-lying land? | low_lying_max_elevation_m, facility_point_rule | count |
| P10 | Among taluks with at least 10 km² of low-lying land, which had the largest share of its low-lying land inside the flood extent on 21 August 2018? | low_lying_max_elevation_m, raster_area_rule | name |
| P11 | How many mapped hospitals in Ernakulam district were both inside the flood extent on 21 August 2018 and on low-lying land? | low_lying_max_elevation_m, facility_point_rule | count |
| P12 | How many mapped schools in Ernakulam district that were inside the flood extent on 21 August 2018 had a hospital within the relief-camp hospital access distance? | relief_camp_hospital_access_m, facility_point_rule | count |

**Control questions** (`needs_params` is empty; run in A1 and A3; every rule is stated in the text):

| id | text | unit |
|---|---|---|
| C01 | What is the total area of Alappuzha district in km², computed in EPSG:32643? | km2 |
| C02 | What is the total length in km of the parts of roads in `roads_major.gpkg` that lie inside Ernakulam district (clip the lines to the district)? | km |
| C03 | Using the polygons in `flood_extent_20180821.gpkg`, which taluk has the largest flooded area in km²? | name |
| C04 | How many features in `hospitals.geojson` have their representative point inside Ernakulam district? | count |
| C05 | What is the mean elevation (m) of Kuttanad taluk in `dem_cop30.tif`, counting a pixel when its centre lies inside the taluk? | m |
| C06 | Using the polygons in `flood_extent_20180821.gpkg`, what is the flooded area of Ernakulam district in km²? | km2 |
| C07 | How many hospitals in Alappuzha district were damaged by the flood? | `expected_status: cannot_answer` |
| C08 | How many people were evacuated to relief camps in Ernakulam district? | `expected_status: cannot_answer` |

**Dev questions** (never scored):
- D01: How many features are in `hospitals.geojson`?
- D02: What is the area of Ernakulam district in km²?
- D03: Using `flood_extent_20180821.gpkg`, what is the flooded area of Alappuzha district in km²?

### `kerala\bench\gold.py`

Define `gold_fn(qid, params) -> {value, unit, status, tied: [names]}`. The `params` argument may contain any defensible values, and `facility_point_rule` may be `representative_point`, `centroid` or `intersects`.

The frozen answers are `gold.json = gold_fn(qid, pack values)`.

**Definitions:**
- Facilities are reduced with the chosen rule; `intersects` means the polygon intersects the zone.
- Distances and areas are computed in EPSG:32643.
- "Inside the flood extent" means inside the `flood_extent_20180821.gpkg` polygons.
- Raster areas count pixels whose centre is inside the zone, times 900 m². Use `rasterio.features.geometry_mask` with `all_touched=False`.
- For P08 and P10: low-lying means DEM ≤ the threshold, counted only for pixels whose centre is inside both the flood polygons and the zone.
- For P05: water = `VV ≤ T`.
- For P06 and P07: flood = `VV ≤ T & seasonality < 10 & slope ≤ 5`.
- For P07: the denominator is the number of valid VV pixels whose centre is inside the taluk.
- For P10: share = flooded low-lying pixels ÷ low-lying pixels in that taluk.
- For name answers: if two candidates are within 1% of each other, return all of them in `tied`. Any one of the tied names counts as correct.

**Also write `gold_sensitivity.json`** (not used for scoring):
- P05 and P06 at T ± 1 dB;
- P03 at 1, 3 and 5 km;
- P09 at 5, 10 and 15 m.

### `kerala\bench\rubric.yaml`

**Tolerances:**
- counts: exact;
- km² and km: ±3% relative;
- percentages: ±1.0 point;
- metres: ±0.5;
- names: case-insensitive, after stripping "taluk", whitespace and punctuation.

**Defensible ranges for A1-chosen values:**

| Parameter | Defensible range |
|---|---|
| `water_threshold_vv_db` | −22 to −13 |
| `permanent_water_rule` | seasonality 6–12 |
| `max_flood_slope_deg` | 2–10 |
| `relief_camp_hospital_access_m` | 1,000–10,000 |
| `low_lying_max_elevation_m` | 3–20 |
| `facility_point_rule` | `representative_point`, `centroid` or `intersects` |

### Write `kerala\bench\GOLD_REVIEW.md`

For each question, include:
- the gold value;
- the steps in plain language;
- the exact `gold.py` lines that compute it;
- one sanity statement, such as "P01 ≤ the number of hospitals in Alappuzha (n)".

**Acceptance:** `.\.venv\Scripts\python.exe -m kerala.bench.gold --check` recomputes everything twice. Both runs must give identical results, and the sanity statements must hold.

**STOP.** I will:
1. read `GOLD_REVIEW.md`;
2. line-review `gold.py`;
3. hand-check P01, P07 and C01 in QGIS or a notebook.

Then I will reply "gold approved" or give corrections. **After approval only:**
1. write `kerala\bench\frozen.json`, holding the hashes and the `layers\` directory listing;
2. add `tests\test_kerala_frozen.py`;
3. commit `phase 4: frozen`.
