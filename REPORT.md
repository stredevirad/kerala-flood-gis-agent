# KeralaFloodBench: an LLM GIS agent for the 2018 Kerala floods, and what makes it fail

Final report, 2026-11-18. Model under test: **gpt-oss:20b** (local, Ollama). The results come from **repeat 1** of the matrix (`matrix_gptoss_v1`, 52 runs).

A second repeat was started but stopped at 35/52 runs when access to the GPU machine was lost; it is not used in any result.

Every number below can be traced to a file under `results/` or to a frozen/gold file. The list is in `results/summary/number_check.md`. The main analysis files are:
- `results/summary/matrix_gptoss_v1/findings_r1.md` (narrative);
- `failure_report.md`, `results_tables.md`, `p01_alt_grid.md` (same folder).

---

## 1. Problem and motivation

In August 2018, Kerala had severe monsoon floods. Ernakulam and Alappuzha districts, including the low-lying Kuttanad region, were among the hardest hit. Questions such as "how many hospitals in Alappuzha were flood-affected?" or "what share of Kuttanad was under water on 21 August?" are answered in practice by a GIS analyst. The analyst combines satellite radar, an elevation model and map data, and makes a number of expert choices along the way: the radar water threshold, what counts as "low-lying", how far from water a building counts as affected, and how to treat a polygon versus a point.

LLM agents that write and run GIS code promise to automate this work. When a small model fails, though, it is not clear why. It could lack the expert parameters, or it could be unable to execute the GIS. This project builds such an agent for the Kerala floods, and around it a small, frozen benchmark designed to tell those two failure sources apart.

## 2. System

- **Base agent: GISclaw** (open source, AGPL-3.0; arXiv 2603.26845). It provides:
  - a ReAct loop (`src/agent/react_agent.py`);
  - a persistent Python sandbox;
  - 28 deterministic geoprocessing ops behind one `geoprocess` tool (`src/agent/geo_ops.py`);
  - the tools `list_files`, `load_vector`, `load_raster`, `execute`, `inspect` and `finish`;
  - OpenAI-compatible LLM engines (`src/agent/llm_engine.py`).
- **Our layer (`kerala/`):**
  - `KeralaAgent` and the **AnswerChecker** (`kerala/agent.py`). The AnswerChecker rejects malformed or implausible `answer.json` files (wrong unit, an area that looks like it was computed in degrees, an area larger than the study region) and lets the agent retry. GISclaw's own `_validate_outputs`, which catches blank PNGs and empty CSVs, is called the **output guard** here.
  - The **domain pack** (`kerala/pack/kerala_pack.yaml`, frozen) and its `domain_param(key)` tool. It returns value, unit, kind, provenance and rationale for each expert parameter.
  - The runner (`kerala/bench/run_one.py`, `run_bench.py`), the scorer (`score.py`), the analyses and a trace viewer.
- **Sandbox isolation.** An agent run sees only `data/kerala/layers/`, linked as `dataset/`. The manifest, `meta/`, `kerala/bench/` and `kerala/pack/` are never visible to it, and the leak and frozen tests guard this. `run_one.py` removes `*_API_KEY` variables from the environment before the agent starts.

## 3. Data and gold

All data is free. Every raster is single-band, 30 m, in **EPSG:32643 (UTM 43N)**, and clipped to Ernakulam + Alappuzha. The grid is 2,765 × 4,400 = 12,166,000 pixels (`data/kerala/meta/data_manifest.json`).

| Layer | Source |
|---|---|
| `s1_vv_20180821_db.tif` | **Sentinel-1 RTC** VV backscatter, 21 Aug 2018 (two S1A slices), Microsoft Planetary Computer, windowed COG reads |
| `jrc_seasonality.tif` | **JRC Global Surface Water** seasonality (Pekel et al. 2016) |
| `dem_cop30.tif` | **Copernicus DEM GLO-30** |
| `districts.gpkg` (2), `taluks.gpkg` (13), `hospitals.geojson` (860), `schools.geojson` (2,295), `roads_major.gpkg` (6,075) | © **OpenStreetMap** contributors |
| `flood_extent_20180821.gpkg` | Derived: VV ≤ T, minus permanent water (JRC seasonality ≥ 10 months) and slopes > 5° |

**Water threshold T = −14.0 dB, chosen post-hoc.**
- The AOI histogram (4,806,014 valid pixels, 0.1 dB bins) has a water mode near −18.85 dB and a land mode near −5.15 dB.
- Otsu gave −11.65 dB and Kittler–Illingworth −12.55 dB. Both sit on the land-mode shoulder: water is only about 15 % of pixels (the Otsu water fraction is 15.26 %), and flooded vegetation (JRC seasonality 1–9) forms a tail between the modes.
- KI also failed the pre-set plausible range [−22, −13] dB by 0.45 dB.
- After **inspecting the histogram**, T was set to the 1 dB-smoothed valley, −13.95 dB, rounded to −14.0 dB. This is a post-hoc choice, and it is reported as one (`data/kerala/meta/cache/threshold_diagnostics.json`, `"post_hoc": true`).
- **±1 dB sensitivity** (`flood_stats.json`, `kerala/bench/gold_sensitivity.json`):

| T (dB) | Water pixel fraction | Flood, Ernakulam (km²) | Flood, Alappuzha (km²) | P06 gold (km²) |
|---:|---:|---:|---:|---:|
| −15 | 12.90 % | 51.25 | 265.95 | 51.2181 |
| **−14** | **13.56 %** | **57.66** | **279.02** | **57.6** |
| −13 | 14.23 % | 64.39 | 291.43 | 64.2897 |

**Facility flood buffer = 250 m** (project convention, in the frozen pack). SAR under-detects water at buildings (double bounce), and 30 m pixels mix land and water. So a hospital or school counts as flood-affected when its **representative point** lies within 250 m of the detected flood extent.

**Gold answers** come from an independent script, `kerala/bench/gold.py`. It uses plain GeoPandas, Shapely, Rasterio and NumPy, never imports the agent, and recomputes everything from the same visible layers.
- Examples: P01 = 93, P06 = 57.6 km², P07 = 56.236341 %, C01 = 1,417.757234 km².
- The full table is in `results/summary/matrix_gptoss_v1/results_tables.md` → "Gold reference".

## 4. Benchmark design

- **23 questions** (`kerala/bench/questions.yaml`, frozen):
  - 12 parameter questions (P01–P12) that each depend on one or more expert parameters;
  - 8 controls (C01–C08) that need none, of which C07 and C08 must be answered `cannot_answer`;
  - 3 development questions (D01–D03), not in the matrix.
- **Three arms.** Every arm sees the parameter **names** the question depends on, so A1 is not penalised for not knowing which decisions matter.
  - **A1 `noparam`**: the model chooses the values and must report them in `parameters_used`.
  - **A2 `inline`**: the values are written into the task.
  - **A3 `pack`**: the task has the pack keys and descriptions, but no values. The values come from the `domain_param(key)` tool.
  - Pre-registered expectation: **A2 ≥ A3** on small models.
- **Matrix:** P01–P12 × 3 arms (36) + C01–C08 × {noparam, pack} (16) = **52 runs**.
- **Scoring** (`kerala/bench/score.py`, tolerances in the frozen `rubric.yaml`):
  - counts must be exact;
  - km² and km within ±3 %;
  - percent within ±1 point;
  - metres within ±0.5 m;
  - names compared after normalisation.
- **`correct_given_own_params`** (A1 only): the gold function is re-run with the model's **own** reported parameters. If they are inside the rubric's defensible ranges and the answer matches, the model executed the GIS correctly and only chose different values. This is the measurement that separates "chose differently" from "could not execute".
- **Frozen and hashed.** `kerala/bench/frozen.json` holds SHA-256 hashes of the questions, rubric, gold, pack and every layer file. `tests/test_kerala_frozen.py` checks them, and the runner re-checks the layer hashes before and after every run.
- **Settings** (`kerala/models.yaml`): temperature 0, seed 1, 16 rounds, 300 s per sandbox call, 25-minute wall clock, 16,384-token context. For gpt-oss: `reasoning_effort: low`, `max_tokens: 8192`.

## 5. Model selection: the floor check

Before any matrix run, a model had to pass a **floor check**: P01 + P06 × 3 arms, with at least **2 of 6** correct (`correct_final` or `correct_given_own_params`). The two questions were fixed in advance and never changed. Source: `results/summary/matrix_gptoss_v1/results_tables.md` → "Floor check".

| Model | correct_final | Verdict |
|---|---:|---|
| qwen2.5-coder:7b (`local-qwen7b`, original laptop) | 0/6 | below the floor |
| qwen3.5:9b | 0/6 | below the floor |
| gpt-oss:20b, before F8 | 0/6 | **not a valid measurement**: every reply was lost before the parser (integration bug, fixed as F8) |
| **gpt-oss:20b, after F8** | **2/6** (P06/inline, P06/pack) | **passes, borderline** |
| gemini-3.5-flash-lite (cloud) | 1/6 (P06/inline) | below the floor |

- **A local 20B model beat Gemini Flash-Lite on the floor**, 2/6 vs 1/6. That is a one-cell difference, both of gpt-oss's passes are on P06, and gpt-oss is not repeatable at temperature 0 (P06/inline gave three different outcomes over three attempts on the floor). So the defensible claim is narrow: gpt-oss cleared the pre-set bar and Gemini did not.
- **Pre-committed re-run rule.** In the first F8 attempt, two cells ended on HTTP 500 errors from Ollama. Before re-running anything, a stop rule was written into `PROGRESS.md`:
  - integration problems (server 5xx, or a reply lost before it reaches the parser) are fixed; model behaviour is never patched;
  - a fix that only touches previously failed calls is re-run with `--resume` on the same batch, and only those cells;
  - if the floor still fails, the outcome is "nothing passes".
  
  Only the two `error` cells were re-run. One of them, P06/inline, became the second pass.
- **Decision:** run the local 52-run matrix on gpt-oss:20b. There was no cloud matrix, because Gemini did not pass.
- **P01 in the floor check.** No model produced 93. Gemini (inline and pack) and Qwen 3.5 (inline) returned exactly **96**, and Qwen 3.5 (noparam) returned exactly **161**. Those are the independent gold values for the **`intersects`** rule (whole hospital polygon) at 250 m and 500 m (`results/summary/floor_diagnostics.md`). The models tested whole polygons instead of the representative point. That is a different, defensible spatial predicate (`intersects` is on the rubric's allowed list), not a GIS execution error.

## 6. Engineering fixes

Fixes to upstream files were made only in `src/agent/geo_ops.py`, `react_agent.py` and `llm_engine.py`, each with regression tests in `tests/test_kerala_*.py`.

| Fix | Problem | Fix |
|---|---|---|
| **F1** (upstream GISclaw bug) | `count_in_polygon` reported **1** for a polygon with **no** points. A left `sjoin` keeps a null row per empty polygon, and `.size()` counts it. | Count non-null right-index values. Patch: `kerala/upstream/F1.patch` |
| **F2** (upstream GISclaw bug) | Slope/aspect/hillshade on a **geographic-CRS** DEM: the pixel size is in degrees and the elevations in metres, so a 0.57° ramp comes out at about 89.95°. | Refuse geographic DEMs with a clear "reproject first" message. Patch: `kerala/upstream/F2.patch` |
| F3 | Windows cp1252 crashes on "°" and Malayalam text | Explicit UTF-8 for file reads and writes |
| F4 | The conversation could exceed the context budget | Extra trimming stages that never cut the task header |
| F5 | Temperature 0 silently became 0.1 (`temperature or 0.1`); no backoff on 429/5xx | `is not None` check; retries that honour `Retry-After`; optional seed |
| F6 (documented upstream issue) | GISclaw's data block says files live in `data/`; the agent actually sees `dataset/<name>` | Fixed inside `kerala/` only: `dataset/` prefixes and an answer-contract example. `app/` is untouched |
| F7 | Runs mislabelled `paused_quota`, because the text "429" matched inside a numeric `gen_time_ms` | Quota is classified only from the error type, HTTP status or an explicit `RESOURCE_EXHAUSTED` field |
| F8 | gpt-oss answers through **native Harmony tool calls**. Ollama put them in `tool_calls` with empty `content`, which the engine ignored, and a placeholder was then parsed as a tool named `Args`. gpt-oss also sends `execute` code as raw text, which Ollama rejects with HTTP 500. | Render native tool calls as ReAct `Action`/`Args` text. Recover the exact raw-code 500 body as an `execute` call. `reasoning_effort: low`, `max_tokens: 8192` |

- A ready-to-paste upstream PR body for F1 and F2 is in `kerala/upstream/PR_F1_F2.md`.
- In repeat 1, F8 rendered **321** native tool calls and recovered **42** raw-code calls from Ollama 500s. There were 0 `error` exits and 0 quota errors (`failure_report.md` → "Run statistics").

**Raw-reply logging** (after repeat 1, logging only). `run_one.py` wraps the API client and stores each raw reply or error body in `trace.jsonl` as `raw_replies`. Prompts, parsing, retries and scoring are unchanged, and the scorer drops the field before the taxonomy runs. Repeat 1 traces therefore contain parsed actions, not raw model text.

**Runner MemoryError hang and resume.**
- With gpt-oss loaded, the PC was close to its memory limit: repeat 1 peaked at 23.62 GB system RAM and 7,237 MiB VRAM.
- During the second repeat, a memory spike made `run_bench` hit `MemoryError` in a subprocess reader thread, and it stopped making progress.
- The hung runner was killed, the frozen test re-run, and the batch resumed with the same detached launcher. `--resume` skips finished runs.
- This shows why the matrix is launched detached (WMI, `kerala/tools/launch_detached.ps1`) and is resumable. That repeat later ended for good when access to the PC was lost.

## 7. Results (repeat 1, `matrix_gptoss_v1`)

All 52 runs completed: 40 `finished`, 12 `max_rounds`, 0 errors, 0 timeouts. Total wall time was 3.04 h, a mean of 3.51 min per run. The largest per-call prompt was 10,388 tokens.

**12 of 52 correct.**

| Arm | Runs | Correct | Accuracy | correct_given_own_params | Parameter questions correct | Controls correct | Minutes per correct | Tokens per correct |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A1 noparam | 20 | 5 | 0.250 | 2 | 2/12 | 3/8 | 13.94 | 309,301 |
| A2 inline | 12 | 1 | 0.083 | 0 | 1/12 | — | 45.07 | 1,024,083 |
| A3 pack | 20 | 6 | 0.300 | 0 | 2/12 | 4/8 | 11.29 | 237,676 |

- **Correct cells:**
  - P07 inline;
  - P08 noparam and pack;
  - P10 noparam and pack;
  - C01, C03 and C08 in both arms;
  - C04 pack.
- A1's two `correct_given_own_params` (P08, P10) are also correct_final.
- **Paired comparisons** on the 12 parameter questions (`paired_tables.csv`; descriptive sign test):

| Comparison | Both right | Only first right | Only second right | Both wrong | p |
|---|---:|---:|---:|---:|---:|
| A3 vs A2 | 0 | 2 | 1 | 9 | 1.00 |
| A2 vs A1 | 0 | 1 | 2 | 9 | 1.00 |
| A3 vs A1, controls | 3 | 1 | 0 | 4 | 1.00 |

- **Pre-registered expectation A2 ≥ A3.** Repeat 1 is not in that direction: A3 was right on 2 parameter questions where A2 was wrong, and A2 on 1 where A3 was wrong. The difference is a single cell, and p = 1.00.
- **With about one run per question per arm, the arm differences are not statistically meaningful.** The floor check showed the same cell can change outcome between runs. These accuracy gaps are not a result. The defensible findings are the failure modes in §8.
- P06, the question gpt-oss passed twice in the floor check, is 0/3 here: no arm wrote an answer.

**P01 method analysis** (`analysis.md`, `p01_alt_grid.md`). Gold is 93. In repeat 1, gpt-oss answered 82 (noparam), 2 (inline) and 174 (pack). None of these equals an alternative-rule gold for Alappuzha, so **PARAM_IGNORED = 0 and PARAM_CHOICE = 0 in every arm**. The grid built from the gold helpers explains the misses:
- **82** is exactly `intersects` at 100 m **with the Alappuzha filter skipped** (both districts). The model chose a 100 m buffer and whole-polygon intersection, then "intersected" with the whole two-district layer (count 82 → 82).
- **174** (pack) retrieved `representative_point` and 250 m with `domain_param`, then spatial-joined **whole geometries** against a flood buffer clipped to both districts. It matches no cell in the grid.
- **2** (inline) was written into `answer.json` without any buffer, join or count in the trace.

So gpt-oss shows the same whole-geometry habit as the floor-check models, but its P01 misses also contain execution errors. The clean "different predicate" story (96, 161) belongs to Gemini and Qwen 3.5 in the floor check.

Representative traces (self-contained HTML):
- [P08/pack, correct](results/summary/matrix_gptoss_v1/traces/P08_pack.html);
- [P01/pack, rule retrieved but not applied](results/summary/matrix_gptoss_v1/traces/P01_pack.html);
- [P01/noparam, intersects @ 100 m without the district filter](results/summary/matrix_gptoss_v1/traces/P01_noparam.html);
- [C02/noparam, `load_vector`-as-op loop, no answer](results/summary/matrix_gptoss_v1/traces/C02_noparam.html);
- [P06/pack, `commentary` pseudo-tool, max_rounds](results/summary/matrix_gptoss_v1/traces/P06_pack.html).

## 8. Failure taxonomy

**Automatic labels** (`score.py`) over the 40 incorrect runs:

| Label | Count |
|---|---:|
| FORMAT (no valid answer.json) | 26 |
| TOOL_BUG | 11 |
| LOGIC | 2 |
| UNANSWERABLE_ANSWERED (C07/pack answered 5) | 1 |

- No run was labelled PARAM_CHOICE, CRS_UNIT, CONTEXT, TIMEOUT or CRASH.
- `TOOL_BUG` is a heuristic: a traceback in a trace that uses `geoprocess`. Reading the traces, these are the model misusing tools, not toolkit bugs.

**Main finding: tool-protocol confusion** (`failure_report.md`). **39 of 40** incorrect runs contain a call that the toolkit rejects before any GIS runs (36 of 40 when NameErrors are not counted).

| Error kind | Events | Incorrect runs |
|---|---:|---:|
| Unknown `geoprocess` op | 84 | 28 |
| Unexpected argument name | 25 | 13 |
| Unknown tool | 14 | 8 |
| `geoprocess` on a variable never loaded (NameError) | 54 | 31 |

- gpt-oss treats the separate **tools** as **ops of `geoprocess`**: `op=load_vector` 39 times, `list_files` 28, `inspect` 8, `load_raster` 7.
- It passes one tool's argument names to another (`geoprocess(path=…)`, `geoprocess(var_name=…)`, `list_files(path=…)`).
- It calls Harmony channel names as tools: `commentary` 10 times, sometimes with a whole Thought/Action/Args step inside, and `container` 4 times, with a bash command.
- It often begins with `geoprocess reproject` on a layer it never loaded, as if layers were preloaded as variables. A NameError is the first protocol error in 28 of the 40 incorrect runs.

The rejections use up rounds: 12 runs hit the 16-round limit, and **26 incorrect runs never wrote `answer.json`** (25 of them had a protocol error).

**Excerpts** (repeat 1; run, round: call → toolkit reply). Thirteen are listed in `findings_r1.md`; for example:
- `C02/noparam` r2: `geoprocess {'op': 'load_vector', 'inputs': {'path': 'dataset/districts.gpkg'}}` → `Unknown geoprocess op 'load_vector'`
- `P04/inline` r2: `geoprocess {'op': 'load_vector', 'inputs': 'dataset/taluks.gpkg', 'var_name': 'taluks'}` → `unexpected keyword argument 'var_name'`
- `P12/noparam` r7: `geoprocess {'op': 'load_vector', 'path': …}` → `unexpected keyword argument 'path'`
- `P06/pack` r3: `commentary {'Thought': 'Need max_flood_slope_deg and raster_area_rule', 'Action': 'domain_param', …}` → `Unknown tool 'commentary'`
- `P05/inline` r2: `container {'cmd': ['bash', '-lc', "python - << 'PY' …"]}` → `Unknown tool 'container'`
- `P11/pack` r1: `geoprocess {'op': 'reproject', 'inputs': {'layer': 'hospitals'}}` → `NameError: name 'hospitals' is not defined`

**Was the confusion the model's own, or an F8 artefact?**
- Repeat 1 traces contain parsed actions only.
- The earlier session recorded a raw-reply check in `PROGRESS.md` → "Session 2 → Repeat 2": "every 'Unknown geoprocess op' failure came back from Ollama as a native tool call named `geoprocess` whose own arguments contain `"op": "list_files"` or `"load_vector"` … (counted 13 of 13 at the time)."
- That check was made on early runs of the stopped second repeat, which are the only runs with raw-reply logging. It is quoted as recorded, as evidence that the malformed calls come from the model and are passed through faithfully. It is not used in any table.

**The pack was used, but its values were not always applied.**
- All **12 of 12** pack-arm parameter questions called `domain_param` (1–4 calls each).
- The **8 pack-arm controls made zero calls**, as they should, since they need no parameters. Those controls show the effect of the pack prompt alone: 4/8 correct in pack against 3/8 in noparam.
- P01/pack is the clearest case: it retrieved `representative_point`, then joined whole geometries.

**Bottom line.** For gpt-oss:20b on this benchmark, the dominant failure is **executing the GIS through the tool protocol**, not missing expert parameters. Supplying the parameters, inline or by tool, cannot help a run that never loads its layers correctly or never writes an answer.

## 9. Limitations

- **Single repeat, small n.** One run per question per arm (12 parameter questions, 8 controls). gpt-oss is not deterministic at temperature 0, so arm comparisons are descriptive only.
- **One model.** Only gpt-oss:20b passed the floor, and only just (2/6). The findings describe this model and this harness.
- **Post-hoc threshold.** T = −14.0 dB was chosen after looking at the histogram. ±1 dB changes P06 gold from 51.22 to 64.29 km².
- **DSM, not DTM.** Copernicus GLO-30 is a surface model: buildings and canopy raise "elevation". That biases "low-lying" (P08–P10) and the slope mask.
- **Single-date SAR.** One 21 Aug 2018 acquisition, and VV only. Flooded vegetation and urban flooding are under-detected; the 250 m facility buffer is a convention that partly compensates.
- **OSM completeness.** Hospital and school layers are only as complete as OSM. Counts are relative to the mapped facilities.
- **Gold validation.**
  - Gold was validated by two independent recomputations, sanity statements and a hand-check map (`kerala/bench/GOLD_REVIEW.md`), then approved and frozen.
  - It was not validated against official damage records. The NASA flood-extent cross-check returned HTTP 404 and was skipped (`data/kerala/meta/cache/nasa_crosscheck.json`).
- **Repeat 2 stopped.** A second repeat was started but stopped at 35/52 runs when access to the GPU machine was lost; it is not used in any result. There is therefore no run-to-run agreement statistic.

## 10. Future work

- **Repeats:** 3–5 per cell, with run-to-run agreement and Cohen's kappa. `kerala.bench.analysis --first … --second …` already computes these.
- **Fix the protocol, not the model.** Expose the GISclaw tools as native tool definitions with strict JSON schemas, so that `load_vector` cannot be sent as a `geoprocess` op. Then re-measure whether parameters matter once execution is reliable.
- **More models:** larger local models and an approved cloud matrix, to test whether the A2 ≥ A3 expectation holds above the floor.
- **Benchmark v2** (only with approval): make the P01-family facility rule harder to miss, and add a DTM-based "low-lying" variant.
- **Upstream:** submit the F1/F2 PR and report F6.

## Attributions

© OpenStreetMap contributors (ODbL). Contains modified Copernicus Sentinel data 2018 (RTC via Microsoft Planetary Computer). Copernicus DEM GLO-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA. JRC Global Surface Water (Pekel et al. 2016, *Nature* 540, 418–422). GISclaw © Han Jinzhen (AGPL-3.0).
