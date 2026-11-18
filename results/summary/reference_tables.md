# Reference tables (floor check and gold)

These tables are kept here, outside `matrix_gptoss_v1/results_tables.md`, so re-running `kerala.bench.score` (which rewrites `results_tables.md`) cannot overwrite them.
- The floor-check table was computed from the five floor `per_run.csv` files under `results/summary/` and `results/summary/model_selection/`.
- The gold table comes from the frozen `kerala/bench/gold.json` and `kerala/bench/rubric.yaml`.

## Floor check (model selection; P01 + P06 × 3 arms; pass rule ≥ 2/6 correct)

Pre-committed rule: at least 2 of 6 runs correct (`correct_final` or `correct_given_own_params`). The question choice (P01, P06) was fixed in advance and not changed after the fact (HANDOFF §2).

| Model (config id) | Batch | Runs | correct_final | correct_given_own_params | format_ok | Correct cells | Verdict | Source |
|---|---|---:|---:|---:|---:|---|---|---|
| qwen2.5-coder:7b (`local-qwen7b`, laptop) | `phase5_f6_floor` | 6 | 0/6 | 0/6 | 1/6 | — | below floor | `results/summary/per_run.csv` |
| qwen3.5:9b (`pc-qwen35-9b`) | `selection_pc_qwen35_9b` | 6 | 0/6 | 0/6 | 3/6 | — | below floor | `results/summary/model_selection/pc-qwen35-9b/per_run.csv` |
| gpt-oss:20b before F8 (`pc-gptoss20b`) | `selection_pc_gptoss20b` | 6 | 0/6 | 0/6 | 0/6 | — | not a valid measurement (integration bug, fixed as F8) | `results/summary/model_selection/pc-gptoss20b/per_run.csv` |
| gpt-oss:20b after F8 (`pc-gptoss20b`) | `floor_gptoss_f8` | 6 | 2/6 | 0/6 | 4/6 | P06/inline, P06/pack | **passes (borderline)** | `results/summary/model_selection/pc-gptoss20b-f8/per_run.csv` |
| gemini-3.5-flash-lite (`cloud-flashlite`) | `floor_cloud` | 6 | 1/6 | 0/6 | 5/6 | P06/inline | below floor | `results/summary/model_selection/cloud-flashlite/per_run.csv` |

Per-run values against gold and the first error in each run are in `results/summary/floor_diagnostics.md` (Qwen 3.5, gpt-oss and Gemini). The qwen2.5-coder run folders stayed on the old laptop; its six rows are in `results/summary/per_run.csv`.

## Gold reference (frozen)

Source: `kerala/bench/gold.json` (frozen; SHA-256 in `kerala/bench/frozen.json`). Tolerances: `kerala/bench/rubric.yaml`. D01–D03 are development questions and are not in the matrix.

| QID | Status | Gold value | Unit | Tolerance | Tied |
|---|---|---|---|---|---|
| C01 | ok | 1417.757234 | km2 | ±3 % (relative) | — |
| C02 | ok | 2058.921864 | km | ±3 % (relative) | — |
| C03 | ok | Kuttanad | name | normalized exact | Kuttanad |
| C04 | ok | 543 | count | exact | — |
| C05 | ok | 1.546613 | m | ±0.5 m | — |
| C06 | ok | 57.604372 | km2 | ±3 % (relative) | — |
| C07 | cannot_answer | — | — | status must be cannot_answer | — |
| C08 | cannot_answer | — | — | status must be cannot_answer | — |
| D01 | ok | 860 | count | exact | — |
| D02 | ok | 2919.9947 | km2 | ±3 % (relative) | — |
| D03 | ok | 278.86123 | km2 | ±3 % (relative) | — |
| P01 | ok | 93 | count | exact | — |
| P02 | ok | 226 | count | exact | — |
| P03 | ok | 8 | count | exact | — |
| P04 | ok | Kothamangalam | name | normalized exact | Kothamangalam |
| P05 | ok | 402.5898 | km2 | ±3 % (relative) | — |
| P06 | ok | 57.6 | km2 | ±3 % (relative) | — |
| P07 | ok | 56.236341 | percent | ±1.0 point | — |
| P08 | ok | 278.8056 | km2 | ±3 % (relative) | — |
| P09 | ok | 407 | count | exact | — |
| P10 | ok | Kuttanad | name | normalized exact | Kuttanad |
| P11 | ok | 68 | count | exact | — |
| P12 | ok | 215 | count | exact | — |

Gold parameters (the values the A2 and A3 arms receive):

| Parameter | Value |
|---|---|
| `facility_flood_buffer_m` | 250.0 |
| `facility_point_rule` | representative_point |
| `flood_date` | 2018-08-21 |
| `low_lying_max_elevation_m` | 10.0 |
| `max_flood_slope_deg` | 5.0 |
| `permanent_water_rule` | 10 |
| `project_crs` | EPSG:32643 |
| `raster_area_rule` | pixel_count * 900 m2, pixel centre inside zone |
| `relief_camp_hospital_access_m` | 3000.0 |
| `water_threshold_vv_db` | -14.0 |
