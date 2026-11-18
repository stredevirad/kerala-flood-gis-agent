# KeralaFloodBench on GISclaw

An AI agent that answers plain-English questions about the **August 2018 Kerala floods** by writing and running real GIS code on satellite and map data, checks its own answer, and a small measured study of *why* models succeed or fail at this.

It is built on the open-source agent GISclaw (arXiv 2603.26845; ReAct loop, persistent Python sandbox, 28 deterministic geoprocessing operations). Everything project-specific lives in `kerala/`. The full write-up is [`REPORT.md`](REPORT.md); plain-language explanations are in [`INTERVIEW_PREP.md`](INTERVIEW_PREP.md).

## What it does

- **Question → GIS code → answer.** For example: *"Using the Sentinel-1 VV image of 21 August 2018, excluding permanent water bodies and steep slopes, what area of Ernakulam district (km²) was flooded?"* The agent loads the layers, thresholds the radar image, masks permanent water and slopes, counts pixels and writes `answer.json`.
- **It checks itself.** The **AnswerChecker** rejects malformed or implausible answers (wrong unit, area in degrees, area larger than the study region) and lets the agent retry. GISclaw's own **output guard** catches blank outputs.
- **The study.** Do small models fail because they lack expert parameters (radar water threshold, "low-lying" height, flood buffer…) or because they cannot execute the GIS? Three arms see the same question and the same parameter *names*:
  - **A1 `noparam`**: the model must choose and report the values;
  - **A2 `inline`**: the values are written into the question;
  - **A3 `pack`**: a sourced domain pack is available through a `domain_param(key)` tool (value, unit, provenance, rationale).
- **Benchmark:** 12 parameter questions (P01–P12), 8 controls (C01–C08, two of which must answer `cannot_answer`), 3 development questions (D01–D03). Gold answers come from an independent script (`kerala/bench/gold.py`) that never imports the agent. Questions, rubric, gold, pack and data layers are **frozen** by hash (`kerala/bench/frozen.json`).

## Data (all free)

| Layer | Source |
|---|---|
| `s1_vv_20180821_db.tif` | Sentinel-1 RTC VV backscatter, 21 Aug 2018, via Microsoft Planetary Computer (windowed COG reads) |
| `dem_cop30.tif` | Copernicus DEM GLO-30 |
| `jrc_seasonality.tif` | JRC Global Surface Water seasonality (Pekel et al. 2016) |
| `flood_extent_20180821.gpkg` | Derived: VV ≤ −14.0 dB, minus permanent water and slopes > 5° |
| `districts.gpkg`, `taluks.gpkg`, `hospitals.geojson`, `schools.geojson`, `roads_major.gpkg` | © OpenStreetMap contributors |

Every raster is single-band, 30 m, EPSG:32643 (UTM 43N), clipped to Ernakulam + Alappuzha. The agent sees **only** `data/kerala/layers/` (as `dataset/`).

## Reproduce (Windows, PowerShell, repo root)

```powershell
# 1. Environment (Python 3.11 via uv)
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe -r desktop\requirements-desktop.txt -r requirements-dev.txt -r kerala\requirements-kerala.txt

# 2. Local model (Ollama, 16K context)
[Environment]::SetEnvironmentVariable("OLLAMA_CONTEXT_LENGTH", "16384", "User")   # then restart Ollama
ollama pull gpt-oss:20b

# 3. Data (resumable; windowed downloads, < 1.5 GB) and its check
.\.venv\Scripts\python.exe -m kerala.prepare_data
.\.venv\Scripts\python.exe -m kerala.prepare_data --check

# 4. Gold answers and tests
.\.venv\Scripts\python.exe -m kerala.bench.gold --check
$t = Get-ChildItem tests -Filter 'test_kerala_*.py' | ForEach-Object FullName; .\.venv\Scripts\python.exe -m pytest -q $t

# 5. One question, one arm (demo)
.\.venv\Scripts\python.exe -m kerala.bench.run_one --qid P06 --arm pack --model pc-gptoss20b --out results\runs\demo\P06_pack

# 6. The 52-run matrix, detached and resumable (re-run the same command to continue)
powershell -NoProfile -ExecutionPolicy Bypass -File kerala\tools\launch_detached.ps1 -Model pc-gptoss20b -Batch matrix_gptoss_v1

# 7. Score, analyse and view traces (local only, no model calls); see "Reproduce the results" below
.\.venv\Scripts\python.exe -m kerala.bench.score --batch matrix_gptoss_v1 --out results\summary\matrix_gptoss_v1
```

## Final state (2026-11-18)

- **Model:** gpt-oss:20b, the only model that passed the floor check (2/6). See `REPORT.md` §5.
- **Results:** repeat 1, `matrix_gptoss_v1`. 52/52 runs; **12 correct** (noparam 5/20, inline 1/12, pack 6/20).
- **Main finding:** tool-protocol confusion. 39 of the 40 incorrect runs contain a tool call the toolkit rejects before any GIS runs. See `REPORT.md` §8.
- A second repeat was started but stopped at 35/52 runs when access to the GPU machine was lost; it is not used in any result.
- **Write-up:**
  - `REPORT.md`;
  - `INTERVIEW_PREP.md`;
  - `results/summary/matrix_gptoss_v1/` (`results_tables.md`, `findings_r1.md`, `failure_report.md`, `analysis.md`, `p01_alt_grid.md`, `traces/*.html`);
  - `results/summary/number_check.md` (the source of every number).

## Reproduce the results (no model calls)

Repeat 1's run files are committed: `results/runs/matrix_gptoss_v1/**/` holds `meta.json`, `answer.json`, `attempts/`, `code.py`, `trace.jsonl`, `checker.jsonl` and `pack_calls.jsonl`, with the PC user name in local paths replaced by `pc-user`. The other batches (floor checks, diagnostics, the stopped repeat 2), `pred_results/`, the `dataset` links and `heartbeat.json` stay git-ignored. The committed summaries in `results/summary/` can be regenerated from a fresh clone on any machine, including one without a GPU or Ollama:

```powershell
# Scores, tables, figures for repeat 1 (identical to the committed files)
.\.venv\Scripts\python.exe -m kerala.bench.score --batch matrix_gptoss_v1 --out results\summary\matrix_gptoss_v1
# P01 method analysis on repeat 1 only (--second is optional; agreement/kappa only with two repeats)
.\.venv\Scripts\python.exe -m kerala.bench.analysis --summary results\summary\matrix_gptoss_v1 --first matrix_gptoss_v1
# P01 under alternative rules, buffers and district filters (independent gold helpers)
.\.venv\Scripts\python.exe -m kerala.tools.p01_alt_check --out results\summary\matrix_gptoss_v1\p01_alt_grid.md
# Failure report: per-arm results, tool-protocol errors, domain_param calls, excerpts, run statistics
.\.venv\Scripts\python.exe -m kerala.tools.failure_report --batch matrix_gptoss_v1 --summary results\summary\matrix_gptoss_v1
# One trace as HTML
.\.venv\Scripts\python.exe -m kerala.bench.trace_html results\runs\matrix_gptoss_v1\pc-gptoss20b\P01\pack --out results\summary\matrix_gptoss_v1\traces\P01_pack.html
```

Run them in this order. `score.py` rewrites `results_tables.md`; `analysis.py` then appends its P01 section. The floor-check and gold tables at the end of `results_tables.md` were appended by hand from `results/summary/**/per_run.csv` and `kerala/bench/gold.json`, so re-append them if you re-score.

The gold and test checks need only the layers in `data/kerala/layers/`:

```powershell
.\.venv\Scripts\python.exe -m kerala.bench.gold --check
$t = Get-ChildItem tests -Filter 'test_kerala_*.py' | ForEach-Object FullName; .\.venv\Scripts\python.exe -m pytest -q $t
```

## Setup (Windows laptop)

The project moved from the GPU PC to a Windows laptop (Intel Core Ultra 5, 16 GB RAM, no NVIDIA GPU, no Ollama) on 2026-11-18. On the laptop only local scoring, analysis and writing are done. No model is ever called.

- The `.venv` copied from the PC did not work: its `pyvenv.cfg` pointed to the PC user's uv Python (`uv trampoline failed to spawn Python child process`). It was renamed to `.venv_pc_stale/` and later deleted; the name is still git-ignored. A fresh venv was built with the commands in step 1 above: `uv venv --python 3.11 .venv`, then the same `uv pip install` line. uv 0.13.8 was already installed (WinGet).
- Result: CPython 3.11.16, geopandas 1.2.0, rasterio 1.4.4 (GDAL 3.10.3). All geospatial wheels installed directly, so no fallback was needed. PowerShell 5.1 shows uv's normal stderr output as a red `NativeCommandError`; that is harmless.
- Use **Windows git** (`git` in PowerShell; system `core.autocrlf=true`) for this checkout. The working tree has CRLF line endings, and the frozen hash of `kerala/bench/gold.json` was computed on its CRLF form. A git without autocrlf (for example WSL's) reports about 68 files as modified even though only line endings differ. Do not commit from such a git.
- Checks on the laptop: Kerala suite `75 passed` (76 after the single-repeat analysis test was added in Step 2), frozen-hash test `1 passed`, `kerala.bench.gold --check` passed. Re-scoring `matrix_gptoss_v1` gives the committed summary byte-for-byte (line endings aside).

Model settings live in `kerala/models.yaml` (temperature 0, seed 1, 16 rounds, 300 s sandbox limit, 25-minute wall clock). The primary model is `gpt-oss:20b` with `reasoning_effort: low` and `max_tokens: 8192`. `cloud-flashlite` (`gemini-3.5-flash-lite`) is kept only to reproduce its floor-check record; it needs a `GEMINI_API_KEY` in the git-ignored `kerala/.env` and is not used by any default command.

## Layout

```
kerala/agent.py            KeralaAgent, AnswerChecker, prompt construction
kerala/pack/               domain pack (frozen) and the domain_param tool
kerala/bench/              questions, rubric, gold (frozen), runner, scorer, analysis, trace viewer
kerala/tools/              probes, diagnostics, detached launcher
kerala/upstream/           F1/F2 patches and a ready-to-paste PR body for GISclaw
results/summary/           scored tables and figures
results/runs/matrix_gptoss_v1/  repeat 1 run files (other batches are git-ignored)
```

## Attributions

- © OpenStreetMap contributors (ODbL).
- Contains modified Copernicus Sentinel data 2018 (RTC via Microsoft Planetary Computer).
- Copernicus DEM GLO-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA; all rights reserved.
- JRC Global Surface Water (Pekel et al. 2016, *Nature* 540, 418–422).
- GISclaw © Han Jinzhen (AGPL-3.0).

## Licence

AGPL-3.0-or-later, the same as GISclaw (see `LICENSE`). Every new source file carries an SPDX header.
