# PROGRESS
## Status: Phase 2 acceptance passed; stopped before Phase 4
## Checklist
- [x] Phase 0
  - [x] 0.1 git init + .gitignore + upstream snapshot commit
  - [x] 0.2 save prompt verbatim and split Part B into phase files
  - [x] 0.3 write AGENTS.md
  - [x] 0.4 write PROGRESS.md phase checklist
  - [x] 0.5 create small Kerala files
  - [x] 0.6 build venv in background
  - [x] 0.7 run baseline tests
  - [x] 0.8 set up Ollama and confirm 16K context
  - [x] 0.9 measure default and CPU-only timing
- [x] Phase 1 — F1–F5 and regression tests
  - [x] F1 polygon count left-join regression
  - [x] F2 terrain operations reject geographic CRS
  - [x] F3 Windows UTF-8 file handling
  - [x] F4 conversation trim respects context budget
  - [x] F5 OpenAI retries, zero temperature and optional seed
  - [x] Run targeted fixes tests
  - [x] Run full baseline suite and compare with Phase 0
- [x] Phase 2 — data preparation
  - [x] Area of interest and district boundaries
  - [x] Taluk boundaries and verification
  - [x] Target grid
  - [x] Vector and raster layers
  - [x] Reference flood using approved T=-14.0 dB (T_valley rounded half-up)
  - [x] Manifest and cache outputs
  - [x] Optional NASA cross-check attempted; skipped after HTTP 404
  - [x] Lock layers and acceptance check
- [x] Phase 3 — pack, AnswerChecker, agent, prompt
  - [x] Pack schema and tool
  - [x] KeralaAgent and AnswerChecker
  - [x] Prompt construction and task composition
  - [x] Offline tests
- [ ] Phase 4 — questions, gold, review (STOP gate)
  - [ ] Questions and rubric
  - [ ] Independent gold and sensitivity results
  - [ ] GOLD_REVIEW.md
  - [ ] Gold acceptance and review STOP
  - [ ] Freeze only after "gold approved"
- [ ] Phase 5 — runner, scorer, demo, smoke tests (STOP gate)
  - [ ] run_one and run_bench
  - [ ] Scorer, tables, taxonomy, figures
  - [ ] Demo CLI
  - [ ] Offline harness tests
  - [ ] Approved smoke runs only
  - [ ] Smoke acceptance and matrix STOP
- [ ] Phase 6 — score, analyse, write
  - [ ] Score matrix and inspect at least 10 failed traces
  - [ ] Draft REPORT.md
  - [ ] Write README_KERALA.md
  - [ ] Write INTERVIEW_PREP.md
  - [ ] Optional upstream PR artifacts
  - [ ] Optional trace HTML viewer
  - [ ] Verify report numbers against summary/manifest
## Numbers so far

### Baseline
- Command: .\.venv\Scripts\python.exe -m pytest -q tests --ignore=tests\test_ui.py
- Result: 9 passed, 5 failed in 31.58 s.
- Failing tests: test_local_probe_add_test_run; test_run_to_completion; test_cancel_busy_and_rejoin; test_toolbox_is_recorded; test_settings_mask_keys.
- The failures were recorded as the unmodified repository baseline. No upstream product files were changed.

### Ollama
- Ollama version: 0.40.13; model: qwen2.5-coder:7b, Q4_K_M; derived model: gisclaw-qwen7b-16k.
- loaded_context returned 16384 after a model call; the runner log also showed n_ctx_seq=16384.
- Vulkan trial required OLLAMA_IGPU_ENABLE=1. The default Vulkan configuration alone dropped the Intel Arc iGPU and used CPU.
- Actual Vulkan backend: Vulkan0, Intel Arc Graphics. CPU trial: library=cpu.
- CPU-only warm sample left more RAM available than the Vulkan sample.

### Timing table
All runs used GISReActAgent on examples\urban-heat-madison, task "Compute the mean temperature per block and save a choropleth PNG", max_rounds=12. System RAM is laptop-wide physical use; process RAM is the Python agent working set.

| Mode | Calls | Mean seconds/call | Run minutes | Prompt / completion tokens | Max prompt tokens | Peak process RAM | Peak system RAM | Outcome |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Vulkan0 / warm | 12 | 18.34 | 3.67 | 41,201 / 861 | 8,306 | 175.4 MB | 15.06 GB | 12-round limit; emergency output save; task not completed |
| CPU / cold | 9 | 49.35 | 7.40 | 22,808 / 733 | 6,748 | 174.9 MB | 14.61 GB | code dedup force-termination; task not completed |
| CPU / warm repeat | 9 | 25.67 | 3.85 | 22,808 / 733 | 3,484 | 172.3 MB | 12.45 GB | code dedup force-termination; task not completed |

- Representative logs are logs\phase0_timing\cpu_calls\calls.jsonl (9 rows for 9 calls) and logs\phase0_timing\vulkan_final\calls.jsonl (12 rows for 12 calls). Each row records prompt tokens, completion tokens and wall time. The earlier cold CPU log groups a retry into one step event.
- Backend recommendation: CPU for the benchmark. Warm runtime was about 5% slower than Vulkan, while peak system RAM use was 2.61 GB lower. The Vulkan run peaked at 15.06 GB of 15.6 GiB detected by Ollama.
- Projected local matrix at warm timing: 52 × 3.85 minutes = 3.34 hours on CPU; 52 × 3.67 minutes = 3.18 hours on Vulkan. Cold CPU extrapolation would be about 6.41 hours. All are below the 20-hour cut threshold.
- Timed runs over 25 minutes: 0 of 2 backend modes; naive observed share 0%. This is a two-run timing sample, and both runs ended through agent logic before any wall-clock timeout.
- Cloud runtime was not measured in Phase 0. The 25-minute per-run ceiling implies at most 21.67 compute hours for 52 serial runs, plus rate-limit backoff; the prompt schedules cloud work across about two days.
- Historical pre-rebuild Phase 2 Otsu check returned T_raw=-11.6113 dB and T=-11.6 dB. The later Otsu/KI analysis and Kirito's approved valley choice supersede that initial stop; final Phase 2 acceptance is recorded below.

## Decisions made (with reason)
- Git was already installed (2.51.0.windows.1); no winget installation was needed.
- uv and Ollama were already installed. The venv used Python 3.11.16 and the exact desktop, dev and Kerala requirement files.
- The model pull and Ollama access needed elevation for the user model directory. The agent timing run needed elevation for Windows junction creation.
- Python timing output used PYTHONIOENCODING=utf-8 after GISclaw progress output failed under cp1252.
- Whole-system RAM was sampled because the Ollama model runner shares the Intel Arc system memory; Python-process memory alone is not representative.
- Earlier, Kirito approved rebuilding only the Sentinel-1 VV mosaic and selecting KI if its range/agreement gate passed; the subsequent decision below supersedes KI as the selected method. Otsu and KI remain diagnostics.
- Kirito superseded the KI-gated threshold selection after reviewing the histogram: choose T=-14.0 dB from T_valley=-13.95 dB using conventional half-up rounding. T_ki=-12.55 dB missed the prior range by 0.45 dB; the water/land trough is selected because the seasonality 1–9 flooded-vegetation tail biases Otsu and breaks KI's Gaussian-class assumption. Keep the [-22,-13] plausible range and all rubric ranges unchanged. Pack provenance is updated as instructed. This is a post-hoc threshold choice to describe in REPORT.md during Phase 6.
- No Phase 0 acceptance item was skipped.

## Needs Kirito
- Kirito explicitly resumed the work by directing Phase 1 after the Phase 0 STOP gate. The smoke task failures remain documented: Vulkan reached the 12-round limit; CPU stopped on repeated-code detection. The projected local matrix is below 20 hours, so no cut is required by the prompt.
- The initial pre-rebuild Otsu stop and later KI-gate STOP are superseded by Kirito's post-hoc valley decision recorded under Decisions made. No plausible range or rubric range changed.
- Pre-rebuild Phase 2 threshold diagnosis (historical; superseded by the approved rerun below):
  - District polygon areas in EPSG:32643: Ernakulam 2,919.995 km2 versus official land area about 3,068 km2 (-4.8%); Alappuzha 1,417.757 km2 versus about 1,415 km2 (+0.2%). Combined OSM area is 4,337.752 km2 versus 4,483 km2. The AOI mask is the union of these district polygons; it has zero in-AOI pixels outside their union. These areas give no evidence of substantial open sea in the polygons; minor coastal/backwater water may remain. Therefore a sea-removed Otsu result is not applicable. The requested plot is `data/kerala/meta/cache/vv_histogram.png`; the empty sea/outside-land candidate is labeled as such, and JRC curves use in-range VV pixels: seasonality >=10 n=272,981; 1-9 n=343,566; 0 n=4,189,467.
  - 500 m-radius spot medians (coordinates are lon,lat; only finite VV in [-30,5] dB): Vembanad Lake centre (76.390, 9.600), n=869, -19.50 dB; central Kochi/MG Road (76.285, 9.970), n=835, -3.53 dB; Kuttanad paddy near Nedumudi (76.370, 9.430), n=871, -18.72 dB. Lake median is within the expected -18 to -25 dB range.
  - Otsu uses the existing 256 bins over [-30,5] dB: current AOI n=4,806,014, T_raw=-11.6113 dB, rounded T=-11.6 dB; excluding JRC seasonality >=10 n=4,533,033, T_raw=-11.3379 dB, rounded -11.3 dB; Ernakulam alone n=3,234,661, T_raw=-11.2012 dB, rounded -11.2 dB; Alappuzha alone n=1,571,353, T_raw=-12.0215 dB, rounded -12.0 dB. All remain outside [-22,-13].
  - This was the pre-rebuild diagnosis: its 256-bin Otsu values and unmasked-zero audit are historical and are superseded by the approved rerun below.
- Threshold re-check after Kirito's approved VV-only rebuild (2026-11-14): the two signed Sentinel-1 COGs were streamed by windows. The rebuilt mosaic reader excludes source -32768, 0, non-finite values, source masks and declared nodata before reprojection and averaging; averages in linear gamma0, then converts the average with 10*log10. RTC sample percentiles remain 0.0288/0.2867/0.8537. The rebuilt one-band raster is EPSG:32643, 30 m; the AOI histogram has 4,806,014 finite pixels in 350 0.1 dB bins over [-30,5].
  - Approved threshold results: T_otsu=-11.65 dB (diagnostic only), T_ki=-12.55 dB, T_valley=-13.95 dB. The KI/valley distance is 1.40 dB and passes the <=1.5 dB test, but T_ki fails the allowed [-22,-13] dB range (it is 0.45 dB above -13); therefore T is unset and the rule requires STOP. Otsu water fraction at T_otsu is 15.2571% (733,259 pixels); no water fraction at T is reported because T is unset. The updated three-threshold plot is `data/kerala/meta/cache/vv_histogram_thresholds.png` and the rebuilt JRC-class histogram is `data/kerala/meta/cache/vv_histogram.png`.
  - Recomputed Otsu alternatives on the same 0.1 dB AOI histogram: current AOI -11.65 dB (4,806,014 pixels); excluding JRC seasonality >=10, -11.35 dB (4,533,033); Ernakulam, -11.15 dB (3,234,661); Alappuzha, -11.95 dB (1,571,353). For context, JRC >=10 is -14.95 dB (272,981 pixels), JRC 1-9 is -14.15 dB (343,566), and JRC 0 is -9.55 dB (4,189,467).
  - The OSM district polygons measure Ernakulam 2,919.995 km2 versus official land area about 3,068 km2 (-4.8%), and Alappuzha 1,417.757 km2 versus about 1,415 km2 (+0.2%). Their combined area is 4,337.752 km2 versus 4,483 km2 official combined land area. The AOI is the exact union of those polygons and has no in-AOI pixels outside that union; no substantial open sea is included, so a sea-removed Otsu sample is not applicable. The histogram's sea/outside-land candidate is empty (0 pixels); minor coastal/backwater water may remain.
  - Recomputed 500 m-radius spot medians: Vembanad Lake centre (76.390, 9.600), 869 pixels, -19.50 dB; central Kochi/MG Road (76.285, 9.970), 835 pixels, -3.53 dB; Kuttanad paddy near Nedumudi (76.370, 9.430), 871 pixels, -18.72 dB.
  - At the time this diagnosis was recorded, the gate failure required STOP. Kirito later selected T=-14.0 dB from the histogram valley; see Decisions made.

## Phase 2 execution
- Area of interest cached from `osmnx.geocode_to_gdf` for Ernakulam and Alappuzha on 2026-11-14. OSMnx's HTTP cache is under the ignored `data/kerala/meta/cache/` directory.
- The resumable script was added in commit `1e01f80`; `python -m kerala.prepare_data --stage aoi` completed with `AOI cached` and `Area of interest ready`.
- Taluk verification passed: Ernakulam (7): Kothamangalam, Muvattupuzha, Kunnathunad, Aluva, Paravur, Kanayannur, Kochi; Alappuzha (6): Kuttanad, Chengannur, Mavelikkara, Karthikappally, Ambalappuzha, Cherthala. All `name` values are ASCII; Kuttanad is present. The OSM result is stored as `data/kerala/layers/taluks.gpkg`.
- Target grid cached as EPSG:32643 at 30 m: 2,765 × 4,400 = 12,166,000 pixels (<25 million); exterior AOI pixels will be nodata in each agent-visible raster.
- Raster outputs built from the two instructed descending Sentinel-1 slices, JRC seasonality, and Copernicus DEM. RTC sample percentiles were 0.0288/0.2867/0.8537, confirming linear gamma0; each raster has one band, EPSG:32643, 12,166,000 pixels and 4,819,784 valid inside-AOI pixels. Districts and hospitals (860 features) are also built. OSMnx uses a project-specific User-Agent, a 600-second request timeout and exponential backoff; the exact AOI/district geometries filter bbox results.
- Threshold diagnostics after the post-hoc choice: T_otsu=-11.65 dB, T_ki=-12.55 dB, T_valley=-13.95 dB, chosen T=-14.0 dB; Otsu water fraction=15.2571% and water fraction at T=13.5636%. The KI range screen remains recorded as failed; the selected T comes from conventional half-up rounding of the valley. Flood area sensitivity at T±1 dB is recorded with flood stats and the manifest.
- Hospital GeoJSON diagnosis before rebuild: the 860-row file's saved `geom_kind` values (captured from the source geometries before serialization) were 510 Point and 350 Polygon; OSM cache IDs classify these as 510 nodes and 350 ways, with 0 relations. After reading the file, 440 geometries were Points and 420 were null; the nulls break down to 230 node/Point and 190 way/Polygon rows, and 160 way/Polygon rows instead had Point geometry. Fetch/clip retained the source rows and hospitals do not pass through `to_crs`; the loss/misalignment occurs while constructing a new GeoDataFrame: property lists use a fresh RangeIndex while `geometry=raw.geometry` retained the sparse post-filter index. Resetting indices before assembly fixed the misalignment. The same audit found 6 `geom_kind` mismatches in schools and 90 null road rows in the initial outputs.
- The corrected OSM rebuild passed read-after-write checks: hospitals.geojson has 860 features (510 Points, 350 Polygons), schools.geojson has 2,295 features (426 Points, 1,869 Polygons), and roads_major.gpkg has 6,075 LineStrings. All three have 0 null and 0 empty geometries; both facility files have 0 `geom_kind` mismatches. No fetched features required dropping for missing geometry. The source-element/geometry breakdown before saving, retrieval timestamp, and endpoint are recorded in `data/kerala/meta/cache/osm_retrieval.json`; the manifest writer includes geometry counts and retrieval metadata.
- Historical initial Otsu and KI-gate runs stopped before polygonization; the approved post-hoc valley choice and corrected OSM layers subsequently allowed flood outputs and the manifest to be completed.
- Final flood: Ernakulam 57.662 km2, Alappuzha 279.019 km2, total 336.681 km2. Kuttanad flooded area is 171.847 km2, or 56.238% of its 339,526 in-AOI pixel centres.
- Sensitivity: at T=-15 dB, water fraction 12.8966%, flood Ernakulam 51.252 km2 / Alappuzha 265.949 km2, Kuttanad 54.133%; at T=-14 dB, 13.5636%, 57.662 km2 / 279.019 km2, Kuttanad 56.238%; at T=-13 dB, 14.2289%, 64.388 km2 / 291.431 km2, Kuttanad 58.086%.
- Quicklook is `data/kerala/meta/cache/quicklook.png`; flood mask is `data/kerala/meta/cache/flood_mask_20180821.tif`. The optional NASA export returned HTTP 404, so `nasa_compare.png` was not created; the attempt and skipped status are recorded in `data/kerala/meta/cache/nasa_crosscheck.json` and the manifest.
- Final vector geometry counts: districts.gpkg 2 Polygon; taluks.gpkg 13 Polygon; hospitals.geojson 510 Point + 350 Polygon; schools.geojson 426 Point + 1,869 Polygon; roads_major.gpkg 6,075 LineString; flood_extent_20180821.gpkg 1 MultiPolygon. The VV, JRC and DEM rasters each contain 12,166,000 grid pixels in one band. All nine layer files are read-only, and the manifest records geometry counts and matching SHA-256 hashes.

## Phase 3 execution
- Kirito directed continuation to Phase 3 while the Phase 2 threshold review remains pending. The Phase 3 pack keeps `water_threshold_vv_db` unresolved in YAML and resolves it only from an accepted manifest at load time; it rejects values outside the prescribed range. No threshold value was invented or substituted.
- Schema-v1 pack YAML and `kerala.pack.pack` now provide schema checking, manifest binding, value-free parameter indexing, and per-run `domain_param` call logging.
- `AnswerChecker` and `KeralaAgent` now enforce answer shape/unit/range rules, preserve numbered answer attempts, call GISclaw's built-in output guard, and append checker records without accessing pack values.
- Prompt and task builders now reuse GISclaw's `SYSTEM_PROMPT`, skill and data blocks, add the value-free pack index only in the pack arm, keep parameter task sections arm-specific, and profile the dataset through the existing junction helper.
- Phase 3 acceptance passed: 26 offline tests. Tests use a temporary manifest value inside the declared range; with Phase 2 accepted, the production pack resolves T=-14.0 dB from the manifest.

## Historical Phase 2 stop output (before the post-hoc valley choice)
Command:
`.\.venv\Scripts\python.exe -m kerala.prepare_data --stage flood`

Output:
`FLOOD_EXIT=1`
`Target grid EPSG:32643 2765 x 4400 = 12,166,000 pixels`
`Otsu T_raw=-11.6113 dB; rounded T=-11.6 dB`
`NEEDS KIRITO: rounded Otsu T=-11.6 dB is outside [-22, -13]`

## Phase 2 acceptance
Command:
`.\.venv\Scripts\python.exe -m kerala.prepare_data --check`

Last 15 output lines:
```text
Alappuzha: flood=279.019 km2; pixels=310,021
Taluks: Kothamangalam, Muvattupuzha, Kunnathunad, Aluva, Paravur, Kanayannur, Kochi, Kuttanad, Chengannur, Mavelikkara, Karthikappally, Ambalappuzha, Cherthala
Kuttanad flooded=56.238% (171.847 km2)
districts.gpkg: 2 features; geometry types={'Polygon': 2}
taluks.gpkg: 13 features; geometry types={'Polygon': 13}
hospitals.geojson: 860 features; geometry types={'Point': 510, 'Polygon': 350}
schools.geojson: 2,295 features; geometry types={'Polygon': 1869, 'Point': 426}
roads_major.gpkg: 6,075 features; geometry types={'LineString': 6075}
s1_vv_20180821_db.tif: 12,166,000 pixels; bands=1
jrc_seasonality.tif: 12,166,000 pixels; bands=1
dem_cop30.tif: 12,166,000 pixels; bands=1
flood_extent_20180821.gpkg: 1 features; geometry types={'MultiPolygon': 1}
Quicklook: D:\GISclaw\GISclaw-main\data\kerala\meta\cache\quicklook.png
NASA cross-check: skipped; HTTPError: HTTP Error 404: Not Found
Checked 9 layers and matching SHA-256 hashes
```

## Phase 0 acceptance outputs (preserved)

Baseline command:
.\.venv\Scripts\python.exe -m pytest -q tests --ignore=tests\test_ui.py
Last 15 output lines:
        - 0o600
E         + 0o666

tests\test_smoke.py:142: AssertionError
---------------------------- Captured stderr call -----------------------------
2026-11-14 12:11:11,041 [INFO] stored API key for openai (sk-ab�1234)
------------------------------ Captured log call ------------------------------
INFO     gisclaw:server.py:176 stored API key for openai (sk-ab�1234)
=========================== short test summary info ===========================
FAILED tests/test_local.py::test_local_probe_add_test_run - assert (False is ...
FAILED tests/test_smoke.py::test_run_to_completion - AssertionError: assert (...
FAILED tests/test_smoke.py::test_cancel_busy_and_rejoin - assert (None)
FAILED tests/test_smoke.py::test_toolbox_is_recorded - assert (False)
FAILED tests/test_smoke.py::test_settings_mask_keys - AssertionError: assert ...
5 failed, 9 passed in 31.58s

Context confirmation command:
.\.venv\Scripts\python.exe -c "from app.local_models import loaded_context; print(loaded_context('http://localhost:11434/v1','gisclaw-qwen7b-16k:latest'))"
Output: 16384

Vulkan timing command:
.\.venv\Scripts\python.exe -m kerala.tools.smoke_run --label vulkan_final --out logs/phase0_timing
Summary:
{
  "label": "vulkan_final",
  "backend": "1",
  "success": true,
  "rounds": 12,
  "wall_seconds": 220.05,
  "minutes_per_run": 3.67,
  "calls": 12,
  "mean_seconds_per_call": 18.34,
  "prompt_tokens": 41201,
  "completion_tokens": 861,
  "peak_working_set_mb": 175.4,
  "peak_system_ram_used_gb": 15.06,
  "call_log": "logs\\phase0_timing\\vulkan_final\\calls.jsonl"
}
CPU timing command:
.\.venv\Scripts\python.exe -m kerala.tools.smoke_run --label cpu_calls --out logs/phase0_timing
Summary:
{
  "label": "cpu_calls",
  "backend": "0",
  "success": true,
  "rounds": 9,
  "wall_seconds": 231.06,
  "minutes_per_run": 3.85,
  "calls": 9,
  "mean_seconds_per_call": 25.67,
  "prompt_tokens": 22808,
  "completion_tokens": 733,
  "peak_working_set_mb": 172.3,
  "peak_system_ram_used_gb": 12.45,
  "call_log": "logs\\phase0_timing\\cpu_calls\\calls.jsonl"
}
## Last acceptance output

Targeted Phase 1 command:
.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_fixes.py
Last output:
..........                                                               [100%]
10 passed in 2.53s

Full Phase 1 comparison command:
.\.venv\Scripts\python.exe -m pytest -q tests --ignore=tests\test_ui.py
Last 15 output lines:
        - 0o600
E         + 0o666

tests\test_smoke.py:142: AssertionError
---------------------------- Captured stderr call -----------------------------
2026-11-14 13:32:51,344 [INFO] stored API key for openai (sk-ab…1234)
------------------------------ Captured log call -----------------------------
INFO     gisclaw:server.py:176 stored API key for openai (sk-ab…1234)
=========================== short test summary info ===========================
FAILED tests/test_local.py::test_local_probe_add_test_run - assert (False is ...
FAILED tests/test_smoke.py::test_run_to_completion - AssertionError: assert (...
FAILED tests/test_smoke.py::test_cancel_busy_and_rejoin - assert (None)
FAILED tests/test_smoke.py::test_toolbox_is_recorded - assert (False)
FAILED tests/test_smoke.py::test_settings_mask_keys - AssertionError: assert ...
5 failed, 19 passed in 20.72s

The five failing baseline tests are identical to the Phase 0 failures; no regressions. The 10 new Kerala fix tests passed.

Phase 3 acceptance command:
.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_pack.py tests\test_kerala_checker.py tests\test_kerala_leak.py
Last output:
..........................                                               [100%]
26 passed in 1.63s
