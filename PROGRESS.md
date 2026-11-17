# PROGRESS
## Morning summary (Claude Code, unattended session 2026-11-17)

**Status:** **gpt-oss:20b passed the Phase 5 floor gate (2/6)** once its integration was fixed. The **local 52-run matrix `matrix_gptoss_v1` is running detached** (launched 06:10 IST). Gemini scored 1/6, so there is no cloud matrix. Phase 6 has not started, and nothing was pushed.

### §7 floor table (P01 + P06 × 3 arms; rule: ≥ 2/6 correct)

| Model | QID / arm | exit_reason | format_ok | correct_final | correct_given_own_params | value vs gold | first error in trace |
|---|---|---|---:|---:|---:|---|---|
| gpt-oss:20b (F8, official) | P01 / noparam | finished | no | no | no | — vs 93 | `geoprocess` op `list_files` (not an op); force-terminated on repeats |
| gpt-oss:20b (F8, official) | P01 / inline | finished | yes | no | no | 0 vs 93 | `geoprocess` got unexpected argument `path` |
| gpt-oss:20b (F8, official) | P01 / pack | finished | yes | no | no | 86 vs 93 | `geoprocess` got unexpected argument `path`; `op=load_vector` |
| gpt-oss:20b (F8, official) | P06 / noparam | finished | no | no | no | — vs 57.6 | `clip` missing `overlay` |
| gpt-oss:20b (F8, official) | P06 / inline | finished | yes | **yes** | no | 57.254 vs 57.6 | first `execute` failed (rasterio mask); recovered |
| gpt-oss:20b (F8, official) | P06 / pack | finished | yes | **yes** | no | 57.221 vs 57.6 | pseudo-tool `commentary` (Harmony quirk) |
| gemini-3.5-flash-lite | P01 / noparam | finished | yes | no | no | 2 vs 93 | `execute` called without `code`; chose a 0 m buffer |
| gemini-3.5-flash-lite | P01 / inline | finished | yes | no | no | 96 vs 93 | `execute` failed; final = `intersects`-rule result |
| gemini-3.5-flash-lite | P01 / pack | finished | yes | no | no | 96 vs 93 | `execute` failed; final = `intersects`-rule result |
| gemini-3.5-flash-lite | P06 / noparam | finished | yes | no | no | 28.52 vs 57.6 | chose `jrc_seasonality > 0` (removes the seasonal flood) |
| gemini-3.5-flash-lite | P06 / inline | finished | yes | **yes** | no | 57.25 vs 57.6 | `geoprocess` missing `op` |
| gemini-3.5-flash-lite | P06 / pack | max_rounds | no | no | no | — vs 57.6 | `execute` given `geoprocess`/`finish` payloads → SyntaxError ×5 |
| qwen3.5:9b | P01 / noparam | finished | yes | no | no | 161 vs 93 | `sjoin` failed; final = `intersects` at 500 m |
| qwen3.5:9b | P01 / inline | finished | yes | no | no | 96 vs 93 | `execute` failed; final = `intersects`-rule result |
| qwen3.5:9b | P01 / pack | finished | yes | no | no | 0 vs 93 | index-aligned `within(GeoSeries)`, then hard-coded 0 |
| qwen3.5:9b | P06 / noparam | max_rounds | no | no | no | — vs 57.6 | tuple has no `.minx` |
| qwen3.5:9b | P06 / inline | finished | no | no | no | — vs 57.6 | `select` missing `layer` |
| qwen3.5:9b | P06 / pack | finished† | no | no | no | — vs 57.6 | malformed `execute` payload |
| gpt-oss:20b (before F8, invalid) | all six | finished (P06/pack †) | no | no | no | — | empty reply parsed as unknown tool `Args` (integration bug) |
| qwen2.5-coder:7b (laptop) | all six | see Phase 5 table | 1/6 | 0/6 | 0/6 | run folders not on this PC | GIS argument errors, 300 s buffer timeout |

Totals: gpt-oss after F8 **2/6** · Gemini **1/6** · Qwen 3.5 **0/6** · Qwen2.5-Coder 7B **0/6** · gpt-oss before F8 0/6 (not a valid measurement). † relabelled from a false `paused_quota` (F7). Full table with `parameters_used`: `results/summary/floor_diagnostics.md`.

**P01 pattern (no model has produced 93).** The independent gold gives 93 for both representative_point and centroid at 250 m, **96 for `intersects` at 250 m**, and 161 for `intersects` at 500 m. Three runs from two models returned exactly 96, and one returned exactly 161. Those runs tested whole hospital polygons instead of the representative point the parameter specifies. This is a method choice, not a CRS or execution error. The benchmark is unchanged.

### Which model was chosen, and why
- **Primary model: gpt-oss:20b (local).** It is the only model at ≥ 2/6 on the unchanged floor. Your rule says: if gpt-oss passes, run the local 52-run matrix, and run the cloud matrix afterwards only if Gemini also passes. Gemini scored 1/6, so only the local matrix runs, and Gemini's floor goes into the "below the floor" comparison.
- gpt-oss's earlier 0/6 was an integration failure, now fixed as **F8**. gpt-oss answers through native Harmony tool calls; Ollama returned these in `tool_calls` with empty `content`, which the engine ignored. gpt-oss also sends `execute` code as raw text, which Ollama rejects with HTTP 500. Both cases are now converted to ReAct `Action`/`Args` text, with `reasoning_effort=low` and `max_tokens=8192`.
- **Caveat:** in the first F8 floor attempt, 2 cells ended on Ollama 500s, leaving 1 correct out of 4 valid cells. I wrote a stop rule into this file before re-running anything, and under it only those two cells were re-run (`--resume`) after the 500 fix. One of them, P06/inline, became the second pass. The pass is narrow: 2/6, both on P06.

### Matrix progress
- Batch `matrix_gptoss_v1`, model `pc-gptoss20b`, 52 runs: P01–P12 × 3 arms, plus C01–C08 × noparam/pack. It was launched detached through WMI at 06:10 IST, so it survives this session ending. Frozen hashes were verified before launch, and the runner checks them before and after every run.
- ETA ≈ 3.2 h (floor mean 3.7 min/run), so around 09:20 IST. The worst case, at the 25-min per-run cap, is much longer. Progress is in `logs/claude_runs/matrix_gptoss_v1.20261117_061003.out.log` (`done N/52 …; ETA … min` lines). The latest status I recorded is in the matrix section at the bottom of this file.

### Exact commands (PowerShell, from the repo root)
- Resume or continue the matrix after any interruption (finished runs are skipped):
  `powershell -NoProfile -ExecutionPolicy Bypass -File kerala\tools\launch_detached.ps1 -Model pc-gptoss20b -Batch matrix_gptoss_v1`
- Check whether it is running: `Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'run_bench' }`
- Score it when done: `.\.venv\Scripts\python.exe -m kerala.bench.score --batch matrix_gptoss_v1 --out results\summary\matrix_gptoss_v1`
- If you later approve a cloud matrix: `powershell -NoProfile -ExecutionPolicy Bypass -File kerala\tools\launch_detached.ps1 -Model cloud-flashlite -Batch matrix_cloud_v1`. The runner stops by itself after 3 consecutive quota-paused runs. Google resets free-tier daily quotas at midnight Pacific time (13:30 IST); run the same command again after that.

### Needs Kirito
1. **Cloud model substitution.** `gemini-2.5-flash-lite` now returns 404 "no longer available to new users". I switched `cloud-flashlite` to **`gemini-3.5-flash-lite`**, which Google names as its successor, and removed `seed` because the endpoint rejects it. Please confirm this or name another model.
2. **API key hygiene.** Your Gemini key had been pasted into the *tracked* `kerala/.env.example`. I confirmed `kerala/.env` holds the same key, then restored `.env.example` to blank. The key was never staged or committed.
3. **Harness changes made before the matrix** (details below): **F7** labels quota from structured errors only, enforces the RPM limit per call, and writes the heartbeat file. **F8** handles gpt-oss tool calls, recovers raw-code 500s, sets `reasoning_effort=low` and `max_tokens=8192`, and fixes the empty-reply placeholder. The placeholder fix applies to every model, so the Qwen floors were measured under the older harness; it only affects empty replies.
4. **The floor pass is narrow:** 2/6, both on P06, and no model has ever produced P01's 93. If the matrix shows the same `intersects`-rule pattern on P01/P02/P11/P12, consider whether the facility-rule wording needs a bench v2. **Nothing in the benchmark was changed.**
5. **Observability gap:** `trace.jsonl` does not store the raw model reply, so tool/argument mismatches (such as Gemini P06/pack) cannot be fully diagnosed. I did not change this mid-matrix; it is worth adding before Phase 6.
6. Phase 6 (score, read at least 10 failed traces, write REPORT/README/INTERVIEW_PREP) and the GitHub push are waiting for you.

## Earlier status (superseded by the Morning summary): Phase 5 STOP — all candidate models were below the 2/6 floor before F8

## Model selection

### Qwen2.5-Coder:7B — below the floor

- The original nine approved smoke runs were D01–D03 × pack plus P01/P06 × all three arms. D01 and D02 passed; D03 was format-invalid. The six floor cells scored 0/6 `correct_final` and 0/6 `correct_given_own_params`, below the 2/6 rule.
- Failure modes were repeated GIS argument errors: `clip` lacked `overlay`, `attribute_join` lacked `layer`, P01/noparam's `buffer` call exceeded 300 s, P06/pack used an unknown `threshold` operation, and P01/inline returned `cannot_answer` for an answerable question. The complete nine-row table is under Phase 5 execution below.
- Kirito authorized a PC-only candidate selection with the same P01/P06 questions and unchanged floor. `pc-gptoss20b` scored 0/6, so `pc-qwen35-9b` was run and also scored 0/6. No candidate is selected; the Phase 5 STOP rule remains in force and no matrix was started.

## Current PC setup and verification

- PC: NVIDIA GeForce RTX 4060 Laptop GPU, 8,188 MiB VRAM, driver 591.66; 24 GB system RAM.
- Installed uv 0.13.8 and Ollama 0.40.16 with winget. Python 3.11 was present; `uv python install 3.11` and the Phase 0 venv build completed in the background. Venv reports Python 3.11.18. Logs: `logs/machine_setup/`.
- Set user `OLLAMA_CONTEXT_LENGTH=16384` with `[Environment]::SetEnvironmentVariable` before Ollama was installed/launched. `server.log` confirms `OLLAMA_CONTEXT_LENGTH:16384` and reports `library=CUDA`, NVIDIA GeForce RTX 4060 Laptop GPU, compute capability 8.9, and 6.9 GiB initially available VRAM. During the pilots, `ollama ps` showed `gpt-oss:20b` at `59%/41% CPU/GPU`, context `16384`, and `qwen3.5:9b` at `16%/84% CPU/GPU`, context `16384`.
- Verified the exact tags on the official [gpt-oss library page](https://ollama.com/library/gpt-oss/tags) and [qwen3.5 library page](https://ollama.com/library/qwen3.5/tags): `gpt-oss:20b` and `qwen3.5:9b`.
- `powercfg /change standby-timeout-ac 0` was applied. AC sleep was already Never (index 0); restore to the original value with the same command: `powercfg /change standby-timeout-ac 0`.
- Frozen check command: `.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_frozen.py`; output: `1 passed in 0.75s`.
- Reapplied read-only attributes with `attrib +R data\kerala\layers\*`; all nine top-level layer files show `ReadOnly`.
- Phase 5 acceptance command: `.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_harness.py tests\test_kerala_frozen.py`; last output lines: `....... [100%]` / `7 passed in 3.78s`.
- Full Kerala suite command: `$keralaTests = Get-ChildItem -LiteralPath tests -Filter 'test_kerala_*.py' | Sort-Object Name | ForEach-Object { $_.FullName }; & .\.venv\Scripts\python.exe -m pytest -q $keralaTests`; last output lines: `............................................... [100%]` / `47 passed in 5.92s`.
- Final post-pilot frozen check: `.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_frozen.py`; output: `.` / `1 passed in 0.58s`. The runner also checked frozen hashes before and after every candidate run.
- Exact model tags were verified on the official [gpt-oss tags page](https://ollama.com/library/gpt-oss/tags) and [qwen3.5 tags page](https://ollama.com/library/qwen3.5/tags). Both are installed; pull and run logs are under `logs/machine_setup/`.

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
- [x] Phase 4 — questions, gold, review (STOP gate)
  - [x] Questions and rubric
  - [x] Independent gold and sensitivity results
  - [x] GOLD_REVIEW.md
  - [x] Gold acceptance and review STOP
  - [x] Freeze after "gold approved"
- [x] Phase 5 — runner, scorer, demo, smoke tests (STOP gate after F6 rerun)
  - [x] run_one and run_bench
  - [x] Scorer, tables, taxonomy, figures
  - [x] Demo CLI
  - [x] Offline harness tests
  - [x] Approved smoke runs only
  - [x] Rerun D01–D03 development smoke and unchanged P01/P06 floor check
  - [x] Apply floor rule: 0/6; STOP before matrix
  - [x] User-authorized PC model-selection pilots, same P01/P06 floor rule; both candidates scored 0/6; STOP before matrix
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

### Ollama (original Phase 0 laptop)
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
- F6 (documented upstream issue): GISclaw's `app.runner.DATA_BLOCK` says the layer listing is complete for `data/`, and `app.data_profile` renders bare layer names, while the GISReActAgent exposes files under `dataset/<name>`. Kerala now prefixes each profile listing path with `dataset/` and includes identical input/output path guidance plus an `execute`/`json.dump` example in every arm's answer contract. The upstream mismatch is documented only; `app/` and `src/` remain untouched.
- Whole-system RAM was sampled because the Ollama model runner shares the Intel Arc system memory; Python-process memory alone is not representative.
- Kirito authorized a pre-matrix PC model-selection pilot after the original Qwen2.5-Coder:7B floor scored 0/6. Real benchmark models now use `max_rounds=16` in every arm; the offline `stub` remains at 2 rounds for its bounded harness tests. The runner records output tokens/s and samples system RAM and NVIDIA VRAM while each isolated run is active.
- OpenAIEngine drops `<think>` blocks and serialized Harmony analysis channels before returning text to the ReAct parser; separate `reasoning_content` and `thinking` fields are ignored. Focused reasoning coverage is included in the full Kerala test suite.
- For the authorized PC pilots, the model configs used `max_rounds=16` for all real models and all three arms. No full matrix was started because neither new candidate reached the unchanged floor.
- The two P06/pack runs marked `paused_quota` are false-positive exit labels from the existing broad `"429" in serialized trace` check: their metadata has no error and zero backoff, the local Ollama request returned HTTP 200, and the trace's numeric `gen_time_ms` contained the substring `429`. Keep the recorded `exit_reason` in the per-run tables, but do not interpret those two labels as an external rate limit.
- Earlier, Kirito approved rebuilding only the Sentinel-1 VV mosaic and selecting KI if its range/agreement gate passed; the subsequent decision below supersedes KI as the selected method. Otsu and KI remain diagnostics.
- Kirito superseded the KI-gated threshold selection after reviewing the histogram: choose T=-14.0 dB from T_valley=-13.95 dB using conventional half-up rounding. T_ki=-12.55 dB missed the prior range by 0.45 dB; the water/land trough is selected because the seasonality 1–9 flooded-vegetation tail biases Otsu and breaks KI's Gaussian-class assumption. Keep the [-22,-13] plausible range and all rubric ranges unchanged. Pack provenance is updated as instructed. This is a post-hoc threshold choice to describe in REPORT.md during Phase 6.
- Kirito revised the Phase 4 facility definition before approval: a facility is flood-affected when its selected representative point/centroid, or its polygon under `intersects`, lies within a 250 m buffer of the detected flood extent. The new project-convention pack key is `facility_flood_buffer_m`, with a 50–1,000 m defensible range and 100/250/500 m sensitivity.
- The Phase 4 P06 reconciliation keeps the 64,000-pixel visible-layer result. Phase 2's 64,069-pixel reference uses a full DEM before AOI clipping for slope gradients; 121 AOI-edge slope classifications differ (95 Phase-2-only and 26 gold-only), yielding the 69-pixel net difference. This is not caused by the district mask, VV/JRC/DEM nodata, or rounding, and is documented in GOLD_REVIEW.md rather than changing the source layers or threshold.
- Kirito approved the revised gold review. `kerala/bench/frozen.json` now records the approved hashes for questions, rubric, gold, and pack plus the complete top-level layer listing, sizes, and hashes. The frozen integrity test passed before the Phase 4 freeze commit.
- No Phase 0 acceptance item was skipped.

- 2026-11-17 (Claude Code, unattended, pre-approved by Kirito up to Phase 6): **gpt-oss:20b chosen as the primary model; local 52-run matrix `matrix_gptoss_v1` launched; no cloud matrix.** Reason: on the unchanged P01/P06 floor, gpt-oss after the F8 integration fix scored 2/6 (meets >=2/6); gemini-3.5-flash-lite 1/6, qwen3.5:9b 0/6, qwen2.5-coder:7b 0/6. Kirito's instruction: gpt-oss passes -> local matrix; cloud matrix only if Gemini also passes.
- 2026-11-17: cloud model `gemini-2.5-flash-lite` (404, retired for new users) replaced by `gemini-3.5-flash-lite`, without `seed` (rejected with HTTP 400). Pending Kirito's confirmation.
- 2026-11-17: gpt-oss uses `reasoning_effort: low` (lowest gpt-oss level; `none`/`minimal` accepted by Ollama but not lower) and `max_tokens: 8192`.
- 2026-11-17: matrix batches are launched with `kerala/tools/launch_detached.ps1` (WMI `Win32_Process.Create`, outside the agent session's job object; always `--resume`). The first `Start-Process` launch was stopped after ~1 min and its partial P01/noparam folder deleted (no meta.json); layers verified intact (9 files, frozen test passed).

## Needs Kirito
- Gold was approved and frozen. Do not edit `questions.yaml`, `rubric.yaml`, `gold.json`, `kerala_pack.yaml`, or the top-level `data/kerala/layers/` files; the frozen test guards their approved hashes and layer listing.
- The approved post-F6 rerun scored 0/6 correct on the unchanged P01/P06 floor check (0/6 correct under own defensible parameters). The two-of-six rule requires STOP; do not run the matrix. The detailed table and first trace errors are recorded below and in `REPORT.md`.
- If Kirito later authorizes another floor pilot, consider replacing P01/P06 with the simpler raster-only P05/P08 pair (VV open-water area and low-lying area). This is a proposal only; no question, gold value, or current STOP decision was changed.
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
- Phase 3 acceptance passed: 27 offline tests after adding the facility-flood-buffer pack and leak coverage. Tests use a temporary manifest value inside the declared range; with Phase 2 accepted, the production pack resolves T=-14.0 dB from the manifest.

## Phase 4 execution (gold-review STOP gate)
- Created `kerala/bench/questions.yaml` with the exact 12 parameter, 8 control, and 3 development questions; created `rubric.yaml` with the instructed tolerances and defensible parameter ranges.
- `kerala/bench/gold.py` is independent of `src.agent`, reads the nine agent-visible layers directly with GeoPandas, Shapely, Rasterio, and NumPy, and resolves the accepted `T=-14.0 dB` through the pack/manifest. P06 and P07 recompute the VV/JRC/DEM flood rule from the visible rasters rather than reuse a Phase 2 cache result.
- The revised facility definition adds `facility_flood_buffer_m=250` m to the pack and rubric. P01, P02, P11, and P12 use point/centroid-to-flood distance or polygon-to-flood distance for `intersects`; their default gold values are 93, 226, 68, and 215 respectively.
- The complete deterministic answer table is in `kerala/bench/gold.json` and `kerala/bench/GOLD_REVIEW.md`. P06 is exactly 64,000 pixels or 57.600000 km2; the review records the 69-pixel, AOI-edge slope difference from Phase 2's full-DEM calculation. P07=56.236341% and C01=1,417.757234 km2; all 23 results have status/unit validation and a documented sanity statement.
- `kerala/bench/gold_sensitivity.json` records P05/P06 at -15/-14/-13 dB, P03 at 1/3/5 km, P09 at 5/10/15 m, and P01/P02/P11/P12 at 100/250/500 m flood buffers. The review also contains the requested hospital/school buffer counts for Alappuzha, Ernakulam, and Kuttanad. The P01 hand-check map is `data/kerala/meta/cache/gold_P01.png`.
- The Phase 4 artifacts were later frozen after Kirito's explicit approval. `kerala/bench/frozen.json` and `tests/test_kerala_frozen.py` are committed in `3b39507 phase 4: frozen`.

## Phase 4 acceptance
Command:
`.\.venv\Scripts\python.exe -m kerala.bench.gold --check`

Last 15 output lines:
```text
Gold check passed: 23 answers, 8 sensitivity groups
P01: 93 count
P07: 56.236341 percent
C01: 1417.757234 km2
P06: 64,000 pixels
P01 250 m buffer: 93 count
Both independent recomputations matched; all sanity statements passed
```

Phase 4 freeze command:
`.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_frozen.py`

Output:
```text
.                                                                        [100%]
1 passed in 0.08s
```

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
...........................                                              [100%]
27 passed in 1.20s

## Phase 5 execution and STOP gate

- Implemented and committed the isolated runner (`run_one.py`, `run_bench.py`), scorer, demo CLI, model registry, offline harness, and frozen-layer guard. Each real run used `data/kerala/layers` only; the manifest, pack, cache and gold files remained outside its dataset work directory.
- Initial pre-F6 local development smoke (`phase5_local_dev`) and floor batch (`phase5_local_floor`) failed; the following approved rerun supersedes their smoke scores.
- Maximum per-call prompt-token count was 5,645 (D02), below the 14,500 limit. The floor batch maximum was 5,577. `results/summary/` holds the floor CSVs, tables and figures. Run artifacts remain git-ignored under `results/runs/`.
- Cloud smoke was skipped as Kirito directed; `kerala/.env` does not exist yet.
- The first local floor launch produced zero-call `PermissionError: [WinError 5] Access is denied` entries because the restricted shell could not create the Windows dataset junction. The authorized external runner retried those `error` entries, created the temporary junctions and produced the six completed run artifacts above. The same limitation affected the in-sandbox test invocation; the required acceptance command passed in the external runner.
- Per the Phase 5 rule, fewer than two successful floor cells requires STOP. The initial failure is superseded by the approved F6 rerun results below; the matrix remains prohibited.

### F6 prompt path fix and approved rerun

- Root cause: upstream `app.runner.DATA_BLOCK` describes a complete listing for `data/`, `app.data_profile.build_block` emits bare layer names, and the agent's working directory exposes layers at `dataset/<name>`. This is documented as upstream issue F6 only; no `app/` or `src/` file is changed.
- Kerala's `build_data_text` now prefixes each listed profile path with `dataset/`. The shared answer contract tells all arms that input paths start with `dataset/`, outputs belong in `pred_results/`, and provides a three-line `execute` example using `json.dump` for `pred_results/answer.json`.
- Prompt-equality/leak coverage verifies the common contract across all arms and verifies prefixed layer paths. `kerala.bench.prompt_preview` saves the rendered system prompt and task for inspection without a model call.
- Focused acceptance command `pytest -q tests/test_kerala_pack.py tests/test_kerala_checker.py tests/test_kerala_leak.py tests/test_kerala_harness.py tests/test_kerala_frozen.py` passed: 35 tests. The exact P01/noparam system prompt and task were saved to `results/_profile/example_prompt_P01_noparam.txt`; it contains `dataset/` in all nine listed layer paths and in the shared contract.
- Kirito approved the unchanged Phase 5 smoke set: D01–D03 × pack × local-qwen7b, then P01/P06 × all three arms × local-qwen7b. The D01–D03 group ran first as `phase5_f6_dev`; the six-cell floor ran second as `phase5_f6_floor`. Cloud smoke was skipped until `kerala/.env` is added.
- A first scheduler invocation briefly selected D01/noparam by mistake. It was terminated before the Ollama server was started, produced no `meta.json` or trace, and is excluded from the nine approved runs.
- D01 and D02 were format-valid and correct. D03 was format-invalid. On the unchanged six-cell floor, no run was correct: `correct_final=0/6`, `correct_given_own_params=0/6`. This fails the >=2/6 requirement and triggers the Phase 5 STOP gate; no matrix was run.
- Largest per-call prompt was 8,270 tokens (P06/inline), below 14,500. Development-smoke times were D01 4.84, D02 5.17, D03 5.28 minutes. Floor times were P01/noparam 24.60, P01/inline 14.37, P01/pack 10.01, P06/inline 13.55, P06/pack 8.30, P06/noparam 6.85 minutes.

### Model selection: Qwen2.5-Coder:7B — below the floor

These are the nine original smoke runs; the failure modes show that the below-floor result reflects a mix of output format, GIS argument, timeout, and answer refusal failures.

| QID / arm | exit_reason | format_ok | correct_final | correct_given_own_params | rounds | minutes | First error in trace, if failed |
|---|---|---:|---:|---:|---:|---:|---|
| D01 / pack | finished | yes | yes | n/a | 5 | 4.84 | — |
| D02 / pack | finished | yes | yes | n/a | 9 | 5.17 | — |
| D03 / pack | finished | no | no | n/a | 11 | 5.28 | geoprocess `clip`: missing required `overlay` input |
| P01 / noparam | finished | no | no | no | 12 | 24.60 | geoprocess `buffer`: execution exceeded the 300 s limit and was stopped |
| P01 / inline | finished | yes | no | no | 12 | 14.37 | geoprocess `clip`: missing required `overlay` input |
| P01 / pack | finished | no | no | no | 11 | 10.01 | geoprocess `clip`: missing required `overlay` input |
| P06 / noparam | finished | no | no | no | 10 | 6.85 | geoprocess `attribute_join`: missing required `layer` input |
| P06 / inline | max_rounds | no | no | no | 12 | 13.55 | geoprocess `attribute_join`: missing required `layer` input |
| P06 / pack | finished | no | no | no | 12 | 8.30 | unknown geoprocess operation `threshold` |

### Model selection: PC candidates — both below the floor

The authorized selection script ran the same six cells for each candidate in sequence and stopped after the second score. Commands:

```powershell
.\.venv\Scripts\python.exe -m kerala.bench.run_bench --model pc-gptoss20b --batch selection_pc_gptoss20b --questions P01,P06 --arms noparam,inline,pack --resume
.\.venv\Scripts\python.exe -m kerala.bench.run_bench --model pc-qwen35-9b --batch selection_pc_qwen35_9b --questions P01,P06 --arms noparam,inline,pack --resume
```

The supervisor log is `logs/machine_setup/wait_then_run_selection.out.log`; each score is saved under `results/summary/model_selection/<model>/per_run.csv`. `pc-gptoss20b` scored 0/6 `correct_final` and 0/6 `correct_given_own_params`; all six runs were format-invalid. Every trace began with an empty response that the ReAct loop interpreted as the unknown tool `Args`. This indicates a response-format/integration failure on this setup and does not measure the model's GIS skill.

`pc-qwen35-9b` scored 0/6 for both correctness measures, with 3/6 format-valid outputs. Its P01 answers used parameters or GIS execution that did not match the gold; the P06 runs failed with a missing `select` input, a tuple `.minx` access, and a malformed Python payload. No candidate clears the floor.

| Model | QID / arm | exit_reason | format_ok | correct_final | correct_given_own_params | rounds | minutes | tokens/s | Peak RAM (GB) | Peak VRAM (MiB) | First error in trace |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| pc-gptoss20b | P01 / noparam | finished | no | no | no | 9 | 10.68 | 15.41 | 18.67 | 6707 | empty response; parsed as unknown tool `Args` |
| pc-gptoss20b | P01 / inline | finished | no | no | no | 6 | 3.95 | 21.85 | 18.46 | 6707 | empty response; parsed as unknown tool `Args` |
| pc-gptoss20b | P01 / pack | finished | no | no | no | 5 | 7.24 | 20.96 | 18.76 | 6707 | empty response; parsed as unknown tool `Args` |
| pc-gptoss20b | P06 / noparam | finished | no | no | no | 6 | 13.14 | 21.25 | 19.28 | 6708 | empty response; parsed as unknown tool `Args` |
| pc-gptoss20b | P06 / inline | finished | no | no | no | 6 | 12.00 | 22.06 | 18.88 | 6708 | empty response; parsed as unknown tool `Args` |
| pc-gptoss20b | P06 / pack | finished* | no | no | no | 5 | 6.70 | 21.91 | 19.10 | 6708 | empty response; parsed as unknown tool `Args` |
| pc-qwen35-9b | P01 / noparam | finished | yes | no | no | 16 | 5.32 | 13.83 | 19.22 | 7004 | first `geopandas.sjoin` execution failed; trace truncates the exception |
| pc-qwen35-9b | P01 / inline | finished | yes | no | no | 16 | 3.32 | 20.71 | 13.46 | 7004 | execution failed after flood/hospital bounds; traceback truncated |
| pc-qwen35-9b | P01 / pack | finished | yes | no | no | 16 | 5.89 | 22.28 | 16.54 | 7004 | failed selecting a joined column; traceback truncates the `KeyError` |
| pc-qwen35-9b | P06 / noparam | max_rounds | no | no | no | 16 | 3.36 | 23.13 | 16.34 | 7005 | `AttributeError`: tuple has no `.minx` |
| pc-qwen35-9b | P06 / inline | finished | no | no | no | 16 | 3.30 | 23.05 | 15.50 | 7004 | `select` missing required `layer` input |
| pc-qwen35-9b | P06 / pack | finished* | no | no | no | 16 | 2.28 | 22.48 | 15.43 | 7005 | malformed `execute` payload; `SyntaxError` |

\* Originally labelled `paused_quota`: false positives from the old trace substring check (a "429" inside `gen_time_ms`). Re-labelled `finished` by F7 on 2026-11-17; the original label is kept in each `meta.json` as `exit_reason_original`.

The 52-run serial extrapolations from each six-run mean are 7.76 hours for `pc-gptoss20b` and 3.39 hours for `pc-qwen35-9b`. These are timing-only estimates from below-floor candidates, not authorization to run a matrix. No model is selected, so there is no runnable matrix command; the 52-run matrix remains stopped pending Kirito's next decision.

#### Needs Kirito

Both PC candidates scored 0/6, so keep the STOP gate. A next pilot could first fix and verify the local reasoning/tool-call response path before repeating the same P01/P06 floor, or use the previously proposed raster-only P05/P08 pair. This proposal changes no gold value or tolerance. The model configs, `max_rounds=16`, and documented per-run tables are ready for review.

Phase 5 acceptance command:
`.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_harness.py tests\test_kerala_frozen.py`

Last output:
```text
.......                                                                  [100%]
7 passed in 1.61s
```

Prompt/leak and combined acceptance command:
`.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_pack.py tests\test_kerala_checker.py tests\test_kerala_leak.py tests\test_kerala_harness.py tests\test_kerala_frozen.py`

Output: `35 passed in 2.04s`.

## Session: Claude Code handoff (2026-11-17)

- Took over from Codex. Read `kerala/HANDOFF_CLAUDE.md`, AGENTS.md, PROGRESS.md and the runner/agent code. Kirito pre-approved unattended work up to (not including) Phase 6, with no GitHub push.
- Created `CLAUDE.md` (imports `@AGENTS.md`) and saved the handoff as `kerala/HANDOFF_CLAUDE.md`.
- Secret hygiene: the tracked `kerala/.env.example` had the real Gemini key pasted into it (uncommitted working-tree change). Verified `kerala/.env` holds the same key (compared in Python without printing), then restored `.env.example` to its blank committed version with `git checkout -- kerala/.env.example`. The key was never staged or committed. `kerala/.env` is git-ignored (`.gitignore:45`) and has a `GEMINI_API_KEY=` line with length > 20.
- Kerala suite: `.venv/Scripts/python.exe -m pytest -q tests/test_kerala_*.py` → `47 passed in 11.31s`.
- Frozen hashes: `.venv/Scripts/python.exe -m pytest -q tests/test_kerala_frozen.py` → `1 passed in 0.49s`.

### §7.1 F7 — `paused_quota` false positive fixed

- Root cause: `run_one.py` labelled a run `paused_quota` when the string "429" appeared anywhere in the serialized trace; both affected runs had `gen_time_ms` values containing those digits.
- Fix (upstream file `src/agent/llm_engine.py`, documented as Kerala F7): new `describe_api_error()` classifies an exception as quota only by type (`openai.RateLimitError`), HTTP status 429, or an explicit `RESOURCE_EXHAUSTED` status field in the error body. `OpenAIEngine` keeps `last_error` and a `quota_errors` counter when a call finally fails. `run_one.classify_exit()` uses only those structured signals; no text search remains. `meta.json` now records `quota_errors`, `last_api_error`, `throttle_seconds`.
- Also fixed in `run_one.py`: the cloud requests-per-minute limit (`rpm_limit`) is now enforced per model call (previously only between runs), and `heartbeat.json` is now written after each call. `run_bench` already read that file to extend the wall-clock limit by backoff time, but nothing wrote it.
- Regression tests: `tests/test_kerala_f7_f8.py` (includes a run whose trace has `"gen_time_ms": 41429.512` → `finished`).
- Re-labelled with `.venv/Scripts/python.exe -m kerala.tools.relabel_quota --apply` (keeps `exit_reason_original` in meta): `selection_pc_gptoss20b/.../P06/pack` paused_quota → finished; `selection_pc_qwen35_9b/.../P06/pack` paused_quota → finished (16 rounds, no `finish` call, but real output files, so GISclaw's `success` is true). Re-scored both with `kerala.bench.score --batch <batch> --out results/summary/model_selection/<model>`; only those two rows changed (taxonomy CRASH → FORMAT). Correctness unchanged.
- `kerala.bench.score` gained `--out` so per-model summaries do not overwrite `results/summary/`.

### §7.2 F8 — gpt-oss integration fixed

- Raw probe: `.venv/Scripts/python.exe -m kerala.tools.gptoss_probe` sends the real D01/pack system prompt and task to `gpt-oss:20b` through `OpenAIEngine`'s client; full responses are in `results/_profile/gptoss_raw.json` (git-ignored profile folder; log `logs/claude_diag/gptoss_probe.out.log`).
- Finding: with the exact floor parameters (max_tokens 4096, stop list) the reply had `finish_reason="tool_calls"`, **empty `content`**, a separate `reasoning` field (518 chars), and a valid native tool call `geoprocess {"op":"load_vector","inputs":{"path":"dataset/hospitals.geojson"},...}`; 165 completion tokens. This was **not** budget exhaustion: gpt-oss answers through the Harmony tool channel, Ollama moves that into `tool_calls`, and the engine read only `content`. The engine then substituted the placeholder `"Thought: (empty response from model)\nAction: \nArgs: {}"`, which GISclaw's action regex (`Action:\s*(\w+)`) read across the line break as a tool named `Args` — the "unknown tool `Args`" error in all six old gpt-oss floor runs.
- Reasoning level: Ollama 0.40.16 accepts `reasoning_effort` = `none`, `minimal`, `low`, `medium` without error, but `none`/`minimal` are not gpt-oss levels (Harmony defines low/medium/high) and did not reason less than `low` (D01 prompt: minimal 66 tokens, low 47, medium 165; `none` on a trivial prompt reasoned more than `low`). Chosen: `reasoning_effort: low`, `max_tokens: 8192` for `pc-gptoss20b`.
- Fix (`src/agent/llm_engine.py`, Kerala F8): optional `reasoning_effort` constructor argument; when the reply has no `Action:` text but has native `tool_calls`, the first call is rendered as `Thought: (native tool call)` / `Action: <name>` / `Args: <json>`; separate `reasoning`/`reasoning_content`/`thinking` fields are never forwarded; the empty-response placeholder no longer contains an `Action:` line, so the loop gives its normal format reminder. `meta.json` records `reasoning_effort` and `native_tool_calls`. Tests in `tests/test_kerala_f7_f8.py`.
- Harness note (honesty): the placeholder change applies to every model, so the earlier Qwen floor runs were measured under the previous harness. It only affects empty replies.

### §7.4 setup — cloud model

- `gemini-2.5-flash-lite` (configured) now returns HTTP 404 "no longer available to new users"; the message names `gemini-3.5-flash-lite` as the replacement. The key authenticates (model listing works). `gemini-3.5-flash-lite` answered the real D01/pack prompt in clean ReAct text (`finish_reason=stop`, 73 completion tokens, no hidden thinking; raw response in `results/_profile/gemini_raw.json`).
- The Gemini OpenAI-compatible endpoint rejects `seed` for this model (HTTP 400 `Unknown name "seed"`), so `cloud-flashlite` no longer sends one; determinism relies on temperature 0. `rpm_limit: 8` is kept and now enforced per call.
- **Exact cloud model ID: `gemini-3.5-flash-lite`** (echoed back as `model` in every response).
- Cloud D01 × pack (`diag_cloud_d01`): finished, 3 rounds, 24.3 s, value 860 = gold 860 (correct).

### §7.4 cloud floor (`floor_cloud`, gemini-3.5-flash-lite)

- Command (detached, `Start-Process`, logs `logs/claude_runs/floor_cloud.{out,err}.log`): `.venv/Scripts/python.exe -u -m kerala.bench.run_bench --model cloud-flashlite --batch floor_cloud --questions P01,P06 --arms noparam,inline,pack --resume`. Frozen test passed before launch; the runner re-checks frozen layer hashes before and after every run.
- Output tail: `done 1/6 P01/noparam: finished` … `done 5/6 P06/pack: max_rounds` / `done 6/6 P06/noparam: finished; ETA 0.0 min`. 0 quota errors; ~2 min per run.
- Score: `.venv/Scripts/python.exe -m kerala.bench.score --batch floor_cloud --out results/summary/model_selection/cloud-flashlite` → `Scored 6 runs`. **1/6 correct_final** (P06/inline 57.25 vs 57.6 km², inside the 3 % tolerance); 0/6 correct_given_own_params. Below the 2/6 floor.

### §7.3 answer-vs-gold diagnostics

- Tool: `.venv/Scripts/python.exe -m kerala.tools.floor_diag --batches <batches> --p01-variants`, writing `results/summary/floor_diagnostics*.md/json`. It reuses the scorer's `collect()` and evaluates the independent gold function for P01 under every facility rule.
- P01 gold under alternative rules: representative_point 250 m = 93, centroid 250 m = 93, **intersects 250 m = 96**, representative_point/centroid 500 m = 158, **intersects 500 m = 161**.
- P01 misses, attributed:
  - Gemini inline 96 and pack 96, Qwen 3.5 inline 96: exactly the `intersects` (whole-geometry) result at the correct 250 m. The models reported `representative_point` but tested the full hospital polygons → **method choice (facility rule)**, not execution or CRS. All worked in EPSG:32643.
  - Qwen 3.5 noparam 161: exactly gold for `intersects` at 500 m. Its own parameters were `facility_point_rule: "buffer"` (not a valid rule name) and 500 m, so the scorer cannot accept them as defensible → **method choice (rule + distance)**; the GIS execution itself was right for what it chose.
  - Qwen 3.5 pack 0: **execution** — `GeoSeries.within(GeoSeries)` aligns row-by-row by index instead of testing against the flood union, then the model hard-coded `value: 0`.
  - Gemini noparam 2: chose `facility_flood_buffer_m: 0` and rule "intersect" → **method choice** (no buffer; question says "within the facility flood buffer"), plus an `execute` call without `code` along the way.
- P06: Gemini noparam 28.52 vs 57.6 — chose `jrc_seasonality > 0` (removes all seasonal water, i.e. much of the flood) and slope 10° → **parameter choice**. Gemini pack hit max_rounds: five `execute` calls whose arguments were `geoprocess`/`finish` payloads (tool/argument mismatch; the parser then wrapped the JSON into `code` → `SyntaxError`); its round-9 summary claimed 201.59 km². The raw model reply is not stored in `trace.jsonl`, which limits this diagnosis (observability gap, noted for Phase 6). Qwen P06 runs produced no answer (GIS argument and code-format errors, as before).
- Old gpt-oss runs (`selection_pc_gptoss20b`): no values; every run failed on the unknown tool `Args` (the F8 integration bug).
- Qwen2.5-Coder:7B: run folders are not on this PC (`results/runs/` is git-ignored and was not copied from the laptop), so value-level diagnostics for it are **skipped**; its first-error table above stands.

### §7.2 gpt-oss floor after F8 (`floor_gptoss_f8`) and the pre-committed stop rule

- Command (detached): `.venv/Scripts/python.exe -u -m kerala.bench.run_bench --model pc-gptoss20b --batch floor_gptoss_f8 --questions P01,P06 --arms noparam,inline,pack --resume`. D01 × pack first (`diag_gptoss_d01_f8`): finished, format_ok, 860 = gold, 4 rounds, 56 s, loaded context 16384.
- Result: 1 correct of 4 valid cells (P06/pack 57.221 vs 57.6 km²). **P01/pack and P06/inline ended `error` on HTTP 500 from Ollama**: these are infrastructure failures, not measurements. Ollama's `server.log` shows 33 × `500 POST /v1/chat/completions`, each just after `harmony parser: no reverse mapping found for function name` (gpt-oss Harmony tool calls to functions the request did not declare). Other valid-cell failures are model behaviour: `geoprocess` with `op=load_vector`/`list_files`, wrong argument names (`path`), missing `clip` overlay, and calls to a pseudo-tool `commentary` (a Harmony channel name; cost rounds in P06/pack, did not change its result; recorded as a known quirk, not patched).
- **Stop rule, written before any re-run:** integration problems (server 5xx, or a reply lost before it reaches the ReAct parser) are fixed; model behaviour (wrong op/tool names, missing arguments, forced termination after repeats, `commentary` calls) is never patched. A fix that only changes calls that previously failed is re-run with `--resume` on `floor_gptoss_f8` (only the two `error` cells run). A fix that changes every request (e.g. declaring `tools`) gets a new batch with all six cells, and that batch alone is the official floor; cells are never mixed across batches. If the official floor still has `error` exits or is below 2/6, the outcome is "nothing passes" and gpt-oss is reported as n correct of m valid cells. Gemini's 1/6 is final (clean, no API errors); it is not re-run.
- **500 root cause (reproduced directly, deterministic):** asked with a plain prompt to use `execute`, gpt-oss passes the code as raw Python rather than JSON; Ollama answers HTTP 500 `error parsing tool call: raw='import numpy as np ...', err=invalid character 'i' looking for beginning of value` (6/6 probe calls). The reply never reached GISclaw's parser, so by the stop rule this is integration. (Two re-runs of the failing cells in `diag_gptoss_500` happened not to hit it: P06/inline max_rounds, P01/pack finished; diagnostic only, not scored.)
- **Fix (Kerala F8, `llm_engine.py`):** `recover_unparsed_tool_call()` recognises only that exact 500 body; non-JSON raw arguments are rendered as `Action: execute` / `Args: {"code": raw}` (raw code can only belong to the code tool, and `server.log` names `execute` before these 500s); a malformed JSON object (tool unknown) becomes a reply with no Action, which gets the normal format reminder. There are no retries for it. Counted in `meta.json` as `recovered_tool_calls`. Tests: `tests/test_kerala_f7_f8.py` (3 new; Kerala suite 69 passed). Live check against Ollama: action `execute`, recovered 1, backoff 0.
- The fix changes only calls that previously failed; the four valid cells had no lost replies (rounds = successful LLM calls). So per the rule, `floor_gptoss_f8` is resumed with `--resume`, which re-runs only P01/pack and P06/inline. The original error artifacts are archived in `results/runs/_archive_floor_gptoss_f8_errors/`.
- Resume output: `skip resumed P01/noparam`, `skip resumed P01/inline`, `done 3/6 P01/pack: finished`, `done 4/6 P06/inline: finished`, `skip resumed P06/pack`, `skip resumed P06/noparam`. P01/pack: 16 rounds, no API error, value 86 vs 93 (wrong). P06/inline: 3 rounds, 1 recovered raw-code call, 57.254 vs 57.6 km² (correct).
- **Official gpt-oss floor (`floor_gptoss_f8`): 2/6 correct_final (P06/inline, P06/pack), 0/6 correct_given_own_params, zero `error` exits. Passes the ≥2/6 rule.** Score: `.venv/Scripts/python.exe -m kerala.bench.score --batch floor_gptoss_f8 --out results/summary/model_selection/pc-gptoss20b-f8`.

## Phase 5 matrix: `matrix_gptoss_v1` (gpt-oss:20b, local)

- Launch: `powershell -NoProfile -ExecutionPolicy Bypass -File kerala\tools\launch_detached.ps1 -Model pc-gptoss20b -Batch matrix_gptoss_v1` at 2026-11-17 06:10 IST (commit `c6f8e08`; frozen test `1 passed` just before). Plan verified with `--dry-run`: 52 runs. Note: `--questions all` would plan 58, because it includes D01–D03, so the launcher passes P01–P12 and C01–C08 explicitly.
- Status at 06:13: 1/52 done; last line: `done 1/52 P01/noparam: finished; ETA 133.3 min`.
