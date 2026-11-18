# Number-traceability check

This file lists every number written in `REPORT.md`, `README_KERALA.md` and `INTERVIEW_PREP.md`, together with the file it comes from. Paths are relative to the repo root. `S` means `results/summary/matrix_gptoss_v1/`.

**Completeness check:** `.\.venv\Scripts\python.exe -m kerala.tools.number_check`. It extracts every number from the three documents and fails if a number is missing from the first column below. It skips inline code, link targets, question/arm/fix ids (P01, A2, F8), list and heading numerals, and model names (gpt-oss:20b, Qwen 3.5 9B …). Result on 2026-11-18: see the end of this file.

The task rule is that every number must trace to `results/` or to a gold/frozen file. Most numbers do. A few trace to other repo files, and they are marked in the "Kind" column:
- **config**: `kerala/models.yaml`, `kerala/pack/kerala_pack.yaml` (frozen);
- **data meta**: `data/kerala/meta/…`;
- **log**: `logs/laptop/…`, `PROGRESS.md`;
- **external**: citations, versions, dates.

None of them is invented.

## Repeat 1 results (`matrix_gptoss_v1`)

| Number(s) | Meaning | Source | Kind |
|---|---|---|---|
| 52, 36, 16 | runs in the matrix (36 parameter + 16 control) | `S/per_run.csv` (52 rows); `S/failure_report.md` | results |
| 12, 40 | correct / incorrect runs | `S/failure_report.md` ("Total"), `S/per_run.csv` | results |
| 5, 20, 0.250 | noparam correct / runs / accuracy | `S/failure_report.md` per-arm table; `S/cost.csv` | results |
| 1, 12, 0.083 | inline correct / runs / accuracy | same | results |
| 6, 20, 0.300 | pack correct / runs / accuracy | same | results |
| 2 | noparam correct_given_own_params (P08, P10) | `S/per_run.csv`, `S/failure_report.md` | results |
| 0 | inline/pack correct_given_own_params; error/timeout exits; quota errors; PARAM_IGNORED/PARAM_CHOICE counts | `S/failure_report.md`, `S/analysis.md` | results |
| 2/12, 1/12, 3/8, 4/8 | parameter-question and control correct by arm | `S/failure_report.md` ("Parameter questions", "Controls") | results |
| 13.94, 45.07, 11.29 | minutes per correct (noparam, inline, pack) | `S/cost.csv` | results |
| 69.72, 67.73 | minutes per arm | `S/cost.csv` | results |
| 309,301, 1,024,083, 237,676 | tokens per correct | `S/cost.csv` | results |
| 40, 12 (exits) | finished / max_rounds | `S/failure_report.md` "Run statistics" | results |
| 3.04, 3.51 | total wall hours / mean minutes per run | `S/failure_report.md` "Run statistics" (sum of `wall_seconds` in meta.json) | results |
| 10,388 | largest per-call prompt (tokens) | `S/failure_report.md` "Run statistics" | results |
| 321, 42 | F8 native tool calls rendered / raw-code calls recovered | `S/failure_report.md` "Run statistics" | results |
| 23.62, 7,237 | peak system RAM (GB) / peak VRAM (MiB) | `S/failure_report.md` "Run statistics" | results |
| 0, 2, 1, 9, 1.00 | A3 vs A2 paired: both right / only A3 / only A2 / both wrong / p | `S/paired_tables.csv` | results |
| 0, 1, 2, 9, 1.00 | A2 vs A1 paired | `S/paired_tables.csv` | results |
| 3, 1, 0, 4, 1.00 | A3 vs A1 controls paired | `S/paired_tables.csv` | results |
| 1.0 | sign-test p (rounded) | `S/paired_tables.csv` | results |
| 3, 3, 0 | correct on first attempt (noparam, pack, inline) | `S/results_tables.md` "First attempt vs final" | results |
| 26, 11, 2, 1 | FORMAT, TOOL_BUG, LOGIC, UNANSWERABLE_ANSWERED | `S/taxonomy_auto.csv`, `S/failure_report.md` | results |
| 5 | C07/pack answered value 5 | `S/failure_runs.csv` (value column) | results |
| 39, 36, 40 | incorrect runs with a tool-protocol error (all / without NameError) out of 40 | `S/failure_report.md` | results |
| 26, 25 | incorrect runs without answer.json / of them with a protocol error | `S/failure_report.md` | results |
| 84, 28 | unknown-op events / runs | `S/failure_report.md` | results |
| 25, 13 | unexpected-argument events / runs | `S/failure_report.md` | results |
| 14, 8 | unknown-tool events / runs | `S/failure_report.md` | results |
| 54, 31 | NameError events / runs | `S/failure_report.md` | results |
| 39, 28, 8, 7 | `load_vector`, `list_files`, `inspect`, `load_raster` as geoprocess op | `S/failure_report.md` "Most frequent offending names" | results |
| 10, 4 | `commentary` / `container` calls | `S/failure_report.md` | results |
| 28 | runs whose first protocol error is a NameError | `S/failure_report.md` "Kind of the first tool-protocol error" | results |
| 12 of 12, 1–4, 8 | pack parameter questions calling domain_param; calls each; zero-call controls | `S/failure_report.md` "domain_param calls" | results |
| 82, 2, 174 | gpt-oss P01 answers (noparam, inline, pack) | `S/analysis.md`, `S/p01_method.csv` | results |
| 0/3 | P06 in repeat 1 | `S/accuracy.csv` | results |
| 278.806, 278.8056 | P08/pack answer vs gold | `S/traces/P08_pack.html` / `kerala/bench/gold.json` | results / gold |
| 16 (rounds) | round limit hit by max_rounds runs | `kerala/models.yaml` (`max_rounds: 16`) | config |
| 35 | repeat 2 meta.json count at the stop | count of `results/runs/matrix_gptoss_v1_r2/**/meta.json` (PROGRESS.md "Step 1 record") | results |
| 13 of 13 | raw-reply check, quoted as recorded | `PROGRESS.md` "Session 2 → Repeat 2" (early runs of the stopped repeat 2; not a result) | log |

## P01 grid and gold

| Number(s) | Meaning | Source | Kind |
|---|---|---|---|
| 93 | P01 gold | `kerala/bench/gold.json` | gold |
| 96, 161, 43, 82, 201, 34, 35, 158, 189, 2, 5, 9, 66, 67, 375, 383 | P01 under other rules/buffers/district filters | `S/p01_alt_grid.md` (from the gold helpers) | results |
| 0, 100, 250, 500 | buffers in the grid (m) | `S/p01_alt_grid.md` | results |
| 96, 96, 96, 161, 2, 0 | floor-check P01 answers of Gemini/Qwen 3.5 | `results/summary/floor_diagnostics.md` | results |
| 57.6, 56.236341, 1,417.757234, 1,417.76 | P06, P07, C01 gold | `kerala/bench/gold.json` | gold |
| 23, 12, 8, 3 | questions: total, parameter, control, dev | `kerala/bench/gold.json` (23 answers), `kerala/bench/questions.yaml` | frozen |
| 250 | facility flood buffer (m) | `kerala/bench/gold.json` parameters; `kerala/pack/kerala_pack.yaml` | gold |
| 10, 5 | permanent water (JRC months), max slope (°) | `kerala/bench/gold.json` parameters | gold |
| 3, 1, 0.5 | tolerances: ±3 % km²/km, ±1 point percent, ±0.5 m | `kerala/bench/rubric.yaml` | frozen |
| −22, −13 | plausible threshold range (dB) | `kerala/bench/rubric.yaml` (defensible_ranges) | frozen |
| 1,417.76 | Alappuzha OSM area used as a sanity statement | `kerala/bench/gold.json` (C01) | gold |

## Floor check

| Number(s) | Meaning | Source | Kind |
|---|---|---|---|
| 0/6, 0, 1, 2 | qwen2.5-coder:7b correct / format_ok | `results/summary/per_run.csv` (batch `phase5_f6_floor`) | results |
| 0/6 | qwen3.5:9b | `results/summary/model_selection/pc-qwen35-9b/per_run.csv` | results |
| 0/6 | gpt-oss before F8 | `results/summary/model_selection/pc-gptoss20b/per_run.csv` | results |
| 2/6, 2, 6 | gpt-oss after F8 (P06/inline, P06/pack) | `results/summary/model_selection/pc-gptoss20b-f8/per_run.csv` | results |
| 1/6 | gemini-3.5-flash-lite (P06/inline) | `results/summary/model_selection/cloud-flashlite/per_run.csv` | results |
| 57.254, 57.221, 57.25 | floor P06 answers | `results/summary/floor_diagnostics.md` | results |
| three / 3 | P06/inline outcomes over three attempts (error, max_rounds, finished) | `results/runs/_archive_floor_gptoss_f8_errors/…/P06/inline/meta.json`, `results/runs/diag_gptoss_500/…/P06/inline/meta.json`, `results/runs/floor_gptoss_f8/…/P06/inline/meta.json` | results |
| 500 | HTTP 500 from Ollama (F8) | `results/runs/_archive_floor_gptoss_f8_errors/**/meta.json` (`last_api_error`) | results |

## Data, threshold and sensitivity

| Number(s) | Meaning | Source | Kind |
|---|---|---|---|
| 30, 32643 | 30 m grid, EPSG:32643 | `data/kerala/meta/data_manifest.json` | data meta |
| 2,765, 4,400, 12,166,000 | grid size | `data/kerala/meta/data_manifest.json`; `kerala.prepare_data --check` output | data meta |
| 860, 2,295, 6,075, 2, 13 | hospitals, schools, roads, districts, taluks | `data/kerala/meta/data_manifest.json` (geometry counts) | data meta |
| 21, 2018 | Sentinel-1 date (21 Aug 2018), two S1A slices | `data/kerala/meta/data_manifest.json` (item ids `…20180821T00…`) | data meta |
| 4,806,014, 0.1 | valid histogram pixels, bin width (dB) | `data/kerala/meta/cache/threshold_diagnostics.json` | data meta |
| −18.85, −5.15, −19, −5 | water / land modes (dB; rounded in INTERVIEW_PREP) | `data/kerala/meta/cache/threshold_diagnostics.json` | data meta |
| −11.65, −12.55, −13.95, −14.0, −14, 0.45 | Otsu, KI, valley, T; KI miss of the range | `data/kerala/meta/cache/threshold_diagnostics.json`, `flood_stats.json` | data meta |
| 15, 15.26 | Otsu water fraction (%) | `threshold_diagnostics.json` (`otsu_water_pixel_fraction` 0.15257) | data meta |
| 1 | ±1 dB sensitivity; 1 dB smoothing | `threshold_diagnostics.json` (`sensitivity_db`) | data meta |
| −15, −13, 12.90, 13.56, 14.23 | T alternatives and water fractions (%) | `data/kerala/meta/cache/flood_stats.json` (`sensitivity_at_plus_minus_1_db`) | data meta |
| 51.25, 57.66, 64.39, 265.95, 279.02, 291.43 | flood km² by district at −15/−14/−13 dB | `flood_stats.json` | data meta |
| 51.2181, 64.2897, 51.22, 64.29 | P06 gold at −15/−13 dB | `kerala/bench/gold_sensitivity.json` | gold |
| 404 | NASA cross-check HTTP status | `data/kerala/meta/cache/nasa_crosscheck.json` | data meta |

## System, configuration and fixes

| Number(s) | Meaning | Source | Kind |
|---|---|---|---|
| 28 | GISclaw geoprocessing ops | `src/agent/geo_ops.py` (28 registry entries) | code |
| 0, 1, 16, 300, 25, 16,384, 16384, 8192 | temperature, seed, rounds, sandbox s, wall-clock min (1500 s), context, max_tokens | `kerala/models.yaml` (`pc-gptoss20b`) | config |
| 0.57, 89.95, 1 | F2 test ramp (1 %) slope before/after | `kerala/upstream/PR_F1_F2.md`; `tests/test_kerala_fixes.py` | code |
| 1, 0 | F1 empty-polygon count before/after | `kerala/upstream/PR_F1_F2.md` | code |
| 0.1 | F5: temperature 0 became 0.1 | `src/agent/llm_engine.py` at upstream snapshot `f2042be` (`temperature or self.temperature`, default 0.1) | code |
| 429 | HTTP status code in F7 | `src/agent/llm_engine.py` (`describe_api_error`) | code |
| 1 | AnswerChecker: areas below 1 km² flagged as degrees | `kerala/agent.py` (km2 check, `value < 1`) | code |
| 1252 | Windows code page cp1252 (F3) | code page name | name |
| 2603.26845 | GISclaw arXiv id | `README_GISCLAW.md` (upstream README) | external |
| 2016, 540, 418, 422 | Pekel et al. citation | literature reference | external |
| 2010, 2014, 2018 | Copernicus DEM licence years; 2018 floods | data provider attribution; event year | external |
| 3.11, 3.11.16, 1.2.0, 1.4.4, 3.10.3, 5.1, 0.13.8 | Python / geopandas / rasterio / GDAL / PowerShell / uv versions on the laptop | `logs/laptop/setup_venv.log`; `PROGRESS.md` "Step 1 record" | log |
| 75, 76, 1 | Kerala tests passed (before/after the new test); frozen test | `logs/laptop/step1_tests.log`; `PROGRESS.md` | log |
| 1.5 | download cap (GB) | `AGENTS.md` | config |
| 16 | laptop RAM (GB) | `LAPTOP_TASK.md` (machine description) | external |
| 2026-11-18 | date of this session | session date | external |
| 3, 5 | "3–5 repeats" in future work | proposal, not a measurement | — |
| 256 | SHA-256 (hash algorithm name) | — | name |
| 3.0 | AGPL-3.0 (licence version) | `LICENSE` | name |
| 68 | files a non-autocrlf git showed as modified (line endings only) | `git status` under WSL, 2026-11-18; `PROGRESS.md` "Step 1 record" | log |

## Completeness check result

Command: `.\.venv\Scripts\python.exe -m kerala.tools.number_check` (2026-11-18), exit code 0:

```
REPORT.md: 114 distinct numbers, 114 listed
README_KERALA.md: 41 distinct numbers, 41 listed
INTERVIEW_PREP.md: 47 distinct numbers, 47 listed
```

The script checks that nothing is missing from the table. Whether each number matches its source was checked by hand while writing.
- These numbers were re-derived from their files this session: every repeat 1 number, the P01 grid, the floor-check counts, the threshold and sensitivity values, the gold values and the config values.
- Numbers that were fixed: the earlier draft of INTERVIEW_PREP said gpt-oss ran "on an 8 GB laptop GPU". It ran on the GPU PC, and "8 GB" is not in any results file, so the sentence now cites the measured peak VRAM (7,237 MiB). REPORT.md no longer states the PC's total RAM, which is not in any results file.
