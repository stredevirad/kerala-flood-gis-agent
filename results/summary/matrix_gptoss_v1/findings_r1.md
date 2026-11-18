# Repeat 1 findings (`matrix_gptoss_v1`, gpt-oss:20b)

Local analysis of the completed repeat 1 only (52 runs). No model was called. Repeat 2 (`matrix_gptoss_v1_r2`) was stopped partway and is **not used** here.

Sources (all under `results/summary/matrix_gptoss_v1/` unless noted):
- `per_run.csv`, `accuracy.csv`, `cost.csv`, `paired_tables.csv`, `taxonomy_auto.csv`: from `kerala.bench.score` (re-run on 2026-11-18 with identical output).
- `analysis.md`, `p01_method.csv`: from `kerala.bench.analysis --first matrix_gptoss_v1` (P01 part only).
- `p01_alt_grid.md`: from `kerala.tools.p01_alt_check` (independent gold helpers, with method choices varied).
- `failure_report.md`, `failure_runs.csv`: from `kerala.tools.failure_report`.
- Gold values: `kerala/bench/gold.json` (frozen). Tolerances: `kerala/bench/rubric.yaml` (frozen).

## 1. Per-arm results

| Arm | Runs | Correct | Accuracy | correct_given_own_params | finished / max_rounds | Minutes | Tokens | Minutes per correct |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| A1 noparam | 20 | 5 | 0.250 | 2 | 17 / 3 | 69.72 | 1,546,506 | 13.94 |
| A2 inline | 12 | 1 | 0.083 | 0 | 9 / 3 | 45.07 | 1,024,083 | 45.07 |
| A3 pack | 20 | 6 | 0.300 | 0 | 14 / 6 | 67.73 | 1,426,057 | 11.29 |
| **All** | **52** | **12** | | | 40 / 12 | | | |

- Parameter questions P01–P12: noparam 2/12, inline 1/12, pack 2/12.
  - Correct cells: P07 inline; P08 noparam and pack; P10 noparam and pack.
- Controls C01–C08: noparam 3/8, pack 4/8.
  - Correct cells: C01, C03 and C08 in both arms; C04 in pack only.
- `correct_given_own_params` applies to A1 only. It is 2/20 (P08 and P10, both also correct_final).
- **Pre-registered expectation: A2 ≥ A3.**
  - On the 12 parameter questions, A3 was right where A2 was wrong in 2 pairs, and the reverse in 1 pair. Both were right in 0 pairs and both wrong in 9 (`paired_tables.csv`, A3 vs A2; descriptive sign-test p = 1.00).
  - So repeat 1 is not in the expected direction, but only by a single cell.
- **This is not statistically meaningful.** There is one run per question per arm, a 1-pair net difference, and p = 1.00. The run-to-run variation seen on the floor check makes it worse: P06/inline gave three different outcomes in three attempts. Accuracy gaps between arms are not a finding. The defensible findings are the failure modes below.
- P06 passed the floor check twice (inline and pack, batch `floor_gptoss_f8`). In repeat 1 it is 0/3: no arm wrote an answer.

## 2. P01 method analysis

Gold for P01 is **93** (representative_point, 250 m, Alappuzha; `gold.json`). The gold helpers give these values under other method choices (`p01_alt_grid.md`):

| District filter | Rule | 0 m | 100 m | 250 m | 500 m |
|---|---|---:|---:|---:|---:|
| Alappuzha (as asked) | representative_point | 2 | 34 | **93** | 158 |
| Alappuzha (as asked) | centroid | 2 | 35 | 93 | 158 |
| Alappuzha (as asked) | intersects | 2 | 43 | 96 | 161 |
| both districts (filter skipped) | representative_point | 5 | 66 | 189 | 375 |
| both districts (filter skipped) | intersects | 9 | 82 | 201 | 383 |

**Repeat 1 (gpt-oss:20b): PARAM_IGNORED = 0 and PARAM_CHOICE = 0 in every arm** (`analysis.md`). None of the three failed P01 answers equals an alternative-rule gold for Alappuzha:

| Run | Answer | Parameters reported | What the trace shows | Diagnosis |
|---|---:|---|---|---|
| P01/noparam | 82 | rule `buffer`, 100 m | Buffers hospitals by 100 m and intersects them with the flood (whole geometries, i.e. `intersects`). Then it "intersects" with `districts`, which has both districts, and the count stays 82 → 82 (rounds 11–13). | **Exactly** intersects @ 100 m with the district filter skipped (grid: 82). A method choice (intersects, 100 m; `buffer` is not a valid rule name, so this is not correct_given_own_params) **plus an execution error** (no Alappuzha filter). |
| P01/inline | 2 | representative_point, 250 m (as given) | Loads layers and lists files, then writes `value: 2` in round 10. No buffer, join or count was run. | Execution failure: the answer was written without computing it. (2 equals the 0 m count, but the trace has no step that produces it.) |
| P01/pack | 174 | representative_point, 250 m (both retrieved with `domain_param`) | Buffers the flood by 250 m and clips it to `districts` (both). The thought says "clip … to the Alappuzha district polygon", but the overlay is the whole layer. Then it spatial-joins **whole hospital geometries**, not representative points, and selects the matches: 174. | It retrieved the rule and did not apply it, and it skipped the district filter. 174 matches no grid cell, so the scorer's label is empty. |

**Where the "96 / 161" story comes from.** In the floor check, other models returned exactly the `intersects` result (`results/summary/floor_diagnostics.md`; PROGRESS.md §7.3):
- Gemini 3.5 Flash-Lite inline 96 and pack 96, and Qwen 3.5 inline 96, are exactly intersects @ 250 m;
- Qwen 3.5 noparam 161 is exactly intersects @ 500 m.

Those models tested whole hospital polygons instead of the representative point. That is a different, defensible spatial predicate (`intersects` is in the rubric's allowed list), not an execution error.

gpt-oss in repeat 1 shows the same predicate habit in P01/noparam and P01/pack. Its misses are **mixed with execution errors**: a skipped district filter, and an answer written without computing it.

## 3. Failure taxonomy (all 40 incorrect runs)

The automatic labels from `score.py`:

| Label | noparam | inline | pack | All |
|---|---:|---:|---:|---:|
| FORMAT (no valid answer.json) | 11 | 4 | 11 | 26 |
| TOOL_BUG (heuristic: a traceback in a trace that uses geoprocess) | 4 | 6 | 1 | 11 |
| LOGIC | 0 | 1 | 1 | 2 |
| UNANSWERABLE_ANSWERED | 0 | 0 | 1 | 1 |

- No run was labelled PARAM_CHOICE, CRS_UNIT, CONTEXT, TIMEOUT or CRASH.
- `TOOL_BUG` is an automatic heuristic. Reading the traces, these are the model misusing tools, not GISclaw bugs.

**Main finding: tool-protocol confusion** (`failure_report.md`).
- **39 of 40** incorrect runs contain at least one call that the toolkit rejects before any GIS runs. **36 of 40** do if `geoprocess` NameErrors are excluded.
- **26** incorrect runs never wrote `answer.json`, and 25 of those had such an error.

| Error kind | Events | Incorrect runs with ≥ 1 |
|---|---:|---:|
| Unknown `geoprocess` op (e.g. `load_vector`, `list_files`, `inspect`, `load_raster`) | 84 | 28 |
| Unexpected argument name (e.g. `geoprocess(path=)`, `geoprocess(var_name=)`, `geoprocess(args=)`) | 25 | 13 |
| Unknown tool (`commentary`, `container`) | 14 | 8 |
| `geoprocess` on a variable that was never loaded (NameError) | 54 | 31 |

The pattern is consistent:
- gpt-oss treats the separate tools `load_vector`, `list_files`, `inspect` and `load_raster` as **ops of `geoprocess`**: `load_vector` 39 events, `list_files` 28, `inspect` 8, `load_raster` 7.
- It passes the arguments of one tool to another (`path`, `var_name`).
- It calls Harmony channel names as tools (`commentary` 10 times; `container` 4 times, with a bash command).
- Its most common first call is `geoprocess reproject` on `hospitals`/`schools`/`districts` before loading them, as if the layers were preloaded as variables.

It burns rounds on these rejections, so 12 runs hit the 16-round limit, and 26 runs end without a valid `answer.json`.

**Trace excerpts** (repeat 1; run id, round, action and arguments → toolkit reply; from `failure_report.md`):

1. `C02/noparam` r2 · `geoprocess {'op': 'load_vector', 'inputs': {'path': 'dataset/districts.gpkg'}, …}` → `Unknown geoprocess op 'load_vector'.` (max_rounds, no answer)
2. `C02/noparam` r5 · `geoprocess` with `op: 'inspect'` → `Unknown geoprocess op 'inspect'.`
3. `P04/inline` r2 · `geoprocess {'op': 'load_vector', 'inputs': 'dataset/taluks.gpkg', 'var_name': 'taluks'}` → `GISToolkit.geoprocess() got an unexpected keyword argument 'var_name'`
4. `P12/noparam` r7 · `geoprocess {'op': 'load_vector', 'path': 'dataset/flood_extent_20180821.gpkg', 'var_name': 'flood'}` → `got an unexpected keyword argument 'path'`
5. `C05/pack` r7–r9 · `geoprocess` three times in a row → `got an unexpected keyword argument 'path'` (finished without an answer)
6. `P01/noparam` r2 and r3 · `geoprocess {'op': 'list_files', 'inputs': {}, …}` twice → `Unknown geoprocess op 'list_files'.` Round 4 then calls the real `list_files` tool.
7. `P01/inline` r7 · `list_files {'path': 'pred_results'}` → `GISToolkit.list_files() got an unexpected keyword argument 'path'`
8. `P06/pack` r3 · `commentary {'Thought': 'Need max_flood_slope_deg and raster_area_rule', 'Action': 'domain_param', …}` → `Unknown tool 'commentary'.` The model wrapped a whole ReAct step inside a Harmony channel name (max_rounds).
9. `P05/inline` r2 · `container {'cmd': ['bash', '-lc', "python - << 'PY' …"]}` → `Unknown tool 'container'.` (max_rounds)
10. `P10/inline` r4 · `commentary {'Thought': 'Check pred_results directory to ensure answer.json exists', 'Action': 'list_files', …}` → `Unknown tool 'commentary'.`
11. `P11/pack` r1 · `geoprocess {'op': 'reproject', 'inputs': {'layer': 'hospitals'}, …}` → `NameError: name 'hospitals' is not defined`. This is a first-round call on a layer that was never loaded. A `geoprocess` NameError is the first tool-protocol error in 28 of the 40 incorrect runs.
12. `C05/noparam` r1 · `geoprocess {'op': 'zonal_statistics', 'inputs': {'raster': 'dem_cop30', 'zones': 'taluks'}, …}` → `NameError: name 'dem_cop30' is not defined`. It uses the file name as a variable name.
13. `P01/pack` r4 · `geoprocess {'op': 'load_vector', 'inputs': {'path': 'dataset/districts.gpkg'}, 'var_name': 'districts'}` → `got an unexpected keyword argument 'var_name'`. In round 5 it then calls the real `load_vector` tool with the same arguments, which succeeds.

**Pack arm.**
- All **12 of 12** pack-arm parameter questions called `domain_param` (1–4 calls each).
- The **8 pack-arm controls (C01–C08) made zero `domain_param` calls**, as expected, since controls need no parameters. They act as controls for the pack prompt itself: 4 of those 8 are correct, against 3 of 8 for the same controls in noparam.
- Calling the pack did not make the model apply what it retrieved. P01/pack retrieved `facility_point_rule = representative_point` and then joined whole geometries.

**Raw replies.**
- Raw-reply logging was added after repeat 1 (commit `1a13928`, logging only). Repeat 1 traces therefore show the **parsed** action, not the model's raw text.
- One cannot tell from repeat 1 alone whether a call such as `geoprocess op=load_vector` was the model's own call or an artefact of the F8 conversion.
- The earlier session recorded a check on this. In PROGRESS.md, "Session 2 → Repeat 2", it says: "every 'Unknown geoprocess op' failure came back from Ollama as a native tool call named `geoprocess` whose own arguments contain `"op": "list_files"` or `"load_vector"`, so that failure is the model's own call, faithfully passed through by F8 (counted 13 of 13 at the time)."
- That check was made on early runs of the stopped second repeat, which are the only runs with raw-reply logging. It is quoted as recorded, as evidence about the mechanism. It is not re-derived, and it is not used in any number or table here.

## 4. Representative traces (HTML)

Rendered with `kerala.bench.trace_html` into `traces/`:
- [`P08_pack.html`](traces/P08_pack.html): correct (278.806 km² vs gold 278.8056), one `domain_param` call.
- [`P01_pack.html`](traces/P01_pack.html): retrieves the facility rule, then joins whole geometries and skips the district filter (174 vs 93).
- [`P01_noparam.html`](traces/P01_noparam.html): `geoprocess op=list_files`/`load_vector` rejections, then intersects @ 100 m with no district filter (82).
- [`C02_noparam.html`](traces/C02_noparam.html): a loop of `geoprocess op=load_vector`/`inspect` rejections; max_rounds, no answer.
- [`P06_pack.html`](traces/P06_pack.html): `commentary` pseudo-tool calls; max_rounds, no answer.
