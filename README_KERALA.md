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

# 7. Score (one batch or several repeats), analyses, and a trace viewer
.\.venv\Scripts\python.exe -m kerala.bench.score --batch matrix_gptoss_v1,matrix_gptoss_v1_r2
.\.venv\Scripts\python.exe -m kerala.bench.analysis --first matrix_gptoss_v1 --second matrix_gptoss_v1_r2
.\.venv\Scripts\python.exe -m kerala.bench.trace_html results\runs\matrix_gptoss_v1\pc-gptoss20b\P06\pack
```

Model settings live in `kerala/models.yaml` (temperature 0, seed 1, 16 rounds, 300 s sandbox limit, 25-minute wall clock). The primary model is `gpt-oss:20b` with `reasoning_effort: low` and `max_tokens: 8192`. `cloud-flashlite` (`gemini-3.5-flash-lite`) is kept only to reproduce its floor-check record; it needs a `GEMINI_API_KEY` in the git-ignored `kerala/.env` and is not used by any default command.

## Layout

```
kerala/agent.py            KeralaAgent, AnswerChecker, prompt construction
kerala/pack/               domain pack (frozen) and the domain_param tool
kerala/bench/              questions, rubric, gold (frozen), runner, scorer, analysis, trace viewer
kerala/tools/              probes, diagnostics, detached launcher
kerala/upstream/           F1/F2 patches and a ready-to-paste PR body for GISclaw
results/summary/           scored tables and figures (run folders under results/runs/ are git-ignored)
```

## Attributions

- © OpenStreetMap contributors (ODbL).
- Contains modified Copernicus Sentinel data 2018 (RTC via Microsoft Planetary Computer).
- Copernicus DEM GLO-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA; all rights reserved.
- JRC Global Surface Water (Pekel et al. 2016, *Nature* 540, 418–422).
- GISclaw © Han Jinzhen (AGPL-3.0).

## Licence

AGPL-3.0-or-later, the same as GISclaw (see `LICENSE`). Every new source file carries an SPDX header.
