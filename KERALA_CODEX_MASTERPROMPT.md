# MASTER PROMPT: KeralaFloodBench on GISclaw (for Codex)

You are Codex (GPT-6 Luna, high effort) working on my Windows 11 laptop inside an unzipped copy of the GISclaw repository. Read this whole prompt once before you start.

- Follow it literally.
- If this prompt and your own judgement disagree, follow the prompt. Write the disagreement into `PROGRESS.md` under **Needs Kirito**.
- The prompt has two parts:
  - **Part A** holds the rules and facts that apply in every session.
  - **Part B** describes the phases.
- In Phase 0 you split this prompt into small files, so that later sessions (after my usage resets) only need to read `AGENTS.md`, `PROGRESS.md` and one phase file.

---

# PART A: Shared context (applies to every session)

## A1. What we are building

**Pitch:** "An AI agent that answers plain-English questions about the August 2018 Kerala floods by writing and running real GIS code on satellite and map data. It checks its own answer. Alongside it is a measured study of why a small local model succeeds or fails at this."

**Research question.** Small models cannot know expert parameters, such as the radar water threshold or what counts as "low-lying". If we give them those parameters as a structured, sourced, tool-retrieved **domain pack**, do they do better than if we simply write the same numbers into the question? And when they fail, is it because they chose a different parameter, or because they could not carry out the GIS?

**Three arms:**

| Arm | Code | What the agent gets |
|---|---|---|
| A1 | `noparam` | The question, plus the **names** of the parameters it needs (no values). It must choose the values itself and report them. |
| A2 | `inline` | The question, the parameter names, and the **values** written inline. |
| A3 | `pack` | The question and the parameter names, plus a "Domain pack" section listing the same keys with one-line descriptions (no values), plus a `domain_param(key)` tool that returns value, unit, kind, provenance and rationale. |

**Pre-registered expectation.** Write this into `REPORT.md` before any results exist: *On a 7B model, A2 ≥ A3 is plausible, because every `domain_param` call costs a round and adds context.* A null or negative A3 result is a valid finding.

**Headline deliverables:**
- a per-question results table;
- paired comparisons (A3 vs A2, A2 vs A1);
- `correct_given_own_params` for A1, which separates "chose different parameters" from "could not execute";
- a failure taxonomy with example traces.

With about 20 questions we report counts and paired wins and losses. We do not claim significance we don't have.

**Reuse, don't rewrite.** GISclaw supplies the ReAct loop, the persistent Python sandbox, the 28 deterministic geoprocessing ops, the operating-discipline skill, the data profile and the LLM engines. We add a thin `kerala\` layer and fix only the upstream bugs that would corrupt the measurement.

## A2. Environment facts

### Machine
- Lenovo IdeaPad Slim 5 14IMH9, Intel Core Ultra 5 125H.
- **16 GB RAM**, shared with an **Intel Arc iGPU**. There is no NVIDIA GPU and no CUDA.
- Windows 11, about 380 GB free disk.

### Shell
**PowerShell.**
- Use `$env:X="y"` to set variables, not `export`.
- Separate commands with `;` or new lines, and do not use `&&` unless `$PSVersionTable` shows version 7 or later.
- Paths use backslashes.

**Python.**
- Always run Python as `.\.venv\Scripts\python.exe`. Never call a bare `python`.

**Long commands.** Some commands run for minutes: `uv` installs, `ollama pull`, data download, smoke runs. Do not run these in the foreground. Start each in the background, writing to a log:
```
Start-Process -NoNewWindow -FilePath ... -RedirectStandardOutput logs\X.out.log -RedirectStandardError logs\X.err.log
```
Then poll the log. Make every long step resumable: it must skip work that is already done.

### Repository
**What it is.** GISclaw `main` v2.0.x, licensed AGPL-3.0-or-later. I unzipped it from a GitHub ZIP, so there is no `.git` folder.

**VERIFY** these before starting:
- `CHANGELOG.md` mentions 2.0.1;
- these files exist: `src\agent\react_agent.py`, `src\agent\geo_ops.py`, `app\runner.py`, `app\data_profile.py` and `app\skills_store.py`.

**Licence rules.**
- Our fork stays AGPL-3.0-or-later. Every new `.py` file gets the repo's SPDX header.
- Never copy code from the MIT-licensed `paper-v2` branch.
- Do not recreate the planner, worker or orchestrator.

### Local LLM (Ollama for Windows)
- **Model:** `qwen2.5-coder:7b`, Q4_K_M, about 4.7 GB.
- **Context window:** Ollama's default context is 4096 tokens on machines with less than 24 GB of VRAM, and it silently cuts the front of the prompt. So we build a derived model, `gisclaw-qwen7b-16k`, whose Modelfile sets `num_ctx 16384`.
- **GPU backend:** the Vulkan backend may or may not work on this iGPU, and may or may not be faster than CPU. Phase 0 measures both.
  - On Windows the server is the tray app. To test CPU only, quit every `ollama*` process, then start the server yourself in a separate window:
    ```
    $env:OLLAMA_VULKAN="0"; ollama serve
    ```
  - Read which backend is in use from the server log. Do not assume it.
- **Base URL:** configurable in `kerala\models.yaml`, so I can point it at Ollama on another PC.

### Cloud LLM (the ceiling)
- **Provider:** Google Gemini free tier, through its OpenAI-compatible endpoint `https://generativelanguage.googleapis.com/v1beta/openai/`.
- **Model:** a current Flash-Lite model. List the available models and record the exact model ID.
- **Free-tier limits:** about 500 requests per day, plus a requests-per-minute cap. HTTP 429 or RESOURCE_EXHAUSTED responses will happen.
- **The API key:**
  - It is read from the file `kerala\.env`, which is git-ignored.
  - It is passed to the engine object only.
  - Never put it in `os.environ` for agent runs. Never print, log or commit it.
- **Do not use Groq.** Its free tier allows 8,000 tokens per minute, which is less than one of our prompts.

### Data (all free, existence verified)

**Microsoft Planetary Computer STAC.**
- Endpoint: `https://planetarycomputer.microsoft.com/api/stac/v1`.
- Sign anonymously with `planetary_computer.sign`. Re-sign each asset immediately before reading it, because tokens expire.
- Set these GDAL options:
  - `GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR`
  - `GDAL_HTTP_MAX_RETRY=5`
  - `GDAL_HTTP_RETRY_DELAY=2`

**Collections:**
- **`sentinel-1-rtc`**: scenes over the area of interest exist for 2018-08-09, **2018-08-21** and 2018-08-27.
  - Use the two 2018-08-21 descending S1A slices, `S1A_IW_GRDH_1SDV_20180821T004044_…_rtc` and `S1A_IW_GRDH_1SDV_20180821T004109_…_rtc`.
  - The published study (Vishnu et al. 2019, *Geomatics, Natural Hazards and Risk*) mapped this flood with the S1A scene of 21 Aug 2018. It also notes the water had partly receded by then.
  - **VERIFY the units.** We expect linear gamma0, with land values around 0.01–0.5. If so, resample in linear units, then compute `10*log10`. If the values already look like dB, do not convert. Record which case it was.
  - Nodata is −32768.
- **`jrc-gsw`**: use the `seasonality` asset (months per year with water, 0–12). The UN-SPIDER recommended practice masks seasonality ≥ 10 as permanent water.
- **`cop-dem-glo-30`**: Copernicus DEM, 30 m, EGM2008 heights.

**OpenStreetMap via `osmnx`** (already in the venv):
- Districts Ernakulam and Alappuzha (`admin_level=5`) and their taluks (`admin_level=6`).
- Hospitals: `amenity=hospital` OR `healthcare=hospital`.
- Schools: `amenity=school`.
- Major roads: `highway` = motorway, trunk, primary or secondary.
- This is today's OSM. Record the retrieval time. Do not use historical Overpass queries.
- `features_from_*` returns a MultiIndex and list columns. Always `reset_index()` and keep only the fields we name.

### Usage and resets
- I have a limited Codex budget. Work in phases.
- Inside a phase, tick sub-step checkboxes in `PROGRESS.md` and make `wip:` commits often.
- A new session must be able to resume from `AGENTS.md`, `PROGRESS.md` and `git log` alone.

## A3. Hard rules (and do-not-do list)

1. **Upstream files you may edit**, and only for fixes F1–F5 in A5:
   - `src\agent\geo_ops.py`
   - `src\agent\react_agent.py`
   - `src\agent\llm_engine.py`

   Everything else you create goes in `kerala\`, `tests\test_kerala_*.py`, `data\kerala\` (generated), `results\` (generated), `logs\`, `AGENTS.md`, `PROGRESS.md`, `REPORT.md`, `README_KERALA.md` and `INTERVIEW_PREP.md`.
2. **Do not touch** `app\`, `desktop\`, `Dockerfile` or `install.*`. Do not refactor, rename or reformat upstream code.
3. **Dependency additions** are limited to:
   - `pystac-client` and `planetary-computer`, listed in `kerala\requirements-kerala.txt`;
   - the existing `requirements-dev.txt`.

   Do not add xarray, stackstac, odc-stac, scikit-image, torch, langchain or similar.
4. **Frozen files.** Once I write "gold approved" (end of Phase 4), these are frozen:
   - `kerala\bench\questions.yaml`
   - `kerala\bench\rubric.yaml`
   - `kerala\bench\gold.json`
   - `kerala\pack\kerala_pack.yaml`
   - the top-level files in `data\kerala\layers\`

   Their SHA-256 hashes, and the directory listing of `layers\`, go in `kerala\bench\frozen.json`, and a test checks them.
   - **Never edit a frozen file, a gold value or a tolerance to make a test or score pass.**
   - **Never hard-code answers** in any code the agent can see.
   - If you think a gold value is wrong, report it under **Needs Kirito**.
5. **Gold is independent.** `kerala\bench\gold.py` uses plain geopandas, shapely, rasterio and numpy. It never imports `src.agent`.
6. **You build; I run the experiment.** The only model runs you may make are the smoke runs listed in Phase 5. **Never start the full matrix.**
7. **Downloads.** Use windowed reads from Cloud-Optimised GeoTIFFs, through signed URLs and `/vsicurl/`. Never download whole scenes. Abort if the total would pass about 1.5 GB.
8. **Raster size.** Every raster the agent sees is single-band, 30 m, clipped, and under 25 million pixels. GISclaw's `load_raster` reads the whole raster as float64.
9. **The agent never sees the answer key.** Agent runs see only `data\kerala\layers\`. The manifest, the cache, `kerala\bench\` and `kerala\pack\` stay outside its `dataset\` folder.
10. **Secrets.** `kerala\.env` is git-ignored. `run_one.py` removes any `*_API_KEY` variables from the environment before the agent starts.
11. **Naming.**
    - GISclaw's built-in check (`_validate_outputs`, which catches blank PNGs and empty CSVs) is the **output guard**.
    - Ours is the **AnswerChecker**.
    - Never call either one "the validator".
12. **Honesty.**
    - A phase is done only when its acceptance command has passed in this session. Paste the command and the last 15 lines of its output into `PROGRESS.md`.
    - Report failures and anything you skip.
    - For an irreversible or design-changing decision, ask under **Needs Kirito** and stop at the next STOP gate.

## A4. The GISclaw parts that matter (verified; skip everything else)

**`src\agent\react_agent.py`: `GISReActAgent`**
- A text ReAct loop: `Thought:` / `Action:` / `Args: {json}`.
- Constructor arguments:
  - `llm_engine`
  - `timeout` (per-snippet sandbox timeout)
  - `max_rounds`
  - `system_prompt_builder(tool_descriptions) -> str`
  - `extra_tools={name: (callable, description_text)}`
  - `context_chars`
- `run(instruction, data_dir, work_dir, on_step=None, should_stop=None)`:
  - links `data_dir` as `work_dir\dataset`, which is a junction on Windows;
  - writes `work_dir\pred_results\` and, after the loop ends, `work_dir\code.py`.
- **On `finish`:**
  1. It refuses if `pred_results` is empty.
  2. It calls `self._validate_outputs(work_dir)`.
  3. If that returns a non-empty string, `finish` is rejected, at most 2 times (counter `self._finish_retries`).

  We subclass this agent and override `_validate_outputs`.
- The override cannot reach the sandbox: it is a local variable inside `run()`.
- Retry counters live on the instance and never reset, so create a **new agent per run**.
- If `generate()` returns text starting with `Error during`, the loop sleeps 5 s, and gives up after 3 such errors in a row.

**`src\agent\sandbox.py`**
- An in-process `exec` in a thread, with a timeout implemented as an async exception.
- It cannot kill code stuck inside GDAL or NumPy C calls. That is why every run gets its **own subprocess** with a hard kill.

**`src\agent\tools.py`: `GISToolkit`**
- Tools: `list_files`, `load_vector`, `load_raster` (whole raster to float64, nodata to NaN), `geoprocess`, `execute`, `inspect`, `finish`.
- `toolkit.run(name, args)` calls `fn(**args)`. Extra tools take keyword arguments and return a string.

**`src\agent\llm_engine.py`: `OpenAIEngine(model, api_key, temperature, max_tokens, base_url, cost_per_m)`**
- **You must call `load_model()` before `generate()`.**
- `generate()` returns errors as text. It does not raise.

**`app\runner.py`**
- Product code. **Never use it to run benchmarks.** It has an LLM intent gate and per-project LOG and journal files that would leak between questions.
- **Do** import its template strings: `SYSTEM_PROMPT`, `SKILLS_BLOCK`, `DATA_BLOCK`.
- `SYSTEM_PROMPT` has these slots: `{tool_descriptions}`, `{skill_rule}`, `{skills_block}`, `{catalog_block}`, `{data_block}`, `{memory_block}`, `{context_block}`.

**`app\skills_store.py`**
- `SkillsStore(workspace=<temp dir>, builtin_dir="app\\skills").build_always_block()` returns the always-on `gis-analysis-discipline` skill text.

**`app\data_profile.py`**
- `profile_project(pdir)` walks `pdir\data` **recursively** and treats `.json` files as vector layers.
- `build_block(profile)` renders the result as text.

**`app\local_models.py`**
- `loaded_context(base_url, model_id)` uses `/api/ps`.

**`tests\conftest.py`**
- Contains a scripted `StubEngine` pattern. Copy that pattern for offline tests.

## A5. Upstream fixes (each one gets a regression test in `tests\test_kerala_fixes.py`)

**F1. `geo_ops._b_count_in_polygon` counts empty polygons as 1.**
- Cause: `sjoin(how="left")` followed by `groupby(index).size()` counts the null match row.
- Fix: count non-null right-index values, using `groupby(level=0)[<index_right col>].count()`. Find the column by its name prefix.
- Test: 2 polygons and 2 points, both points inside A. Expect A=2, B=0. The old code gives B=1; I reproduced this.

**F2. `geo_ops._terrain` (slope, aspect, hillshade) on a geographic-CRS DEM.**
- Cause: pixel size is in degrees, so a 0.57° slope comes out as 89.95°. I reproduced this.
- Fix: in the generated code, if `_meta['crs']` is geographic, print one line starting with `❌` saying the DEM must be reprojected to a projected CRS, and compute nothing.
- Test: projected 1% ramp gives about 0.57°; the geographic case prints the `❌` line.

**F3. Windows encoding in `react_agent.py`.**
- Writing `code.py` must use `encoding="utf-8"`.
- The CSV line count in `_validate_outputs` must open with `encoding="utf-8", errors="replace"`.
- Test: code containing "°" and Malayalam text is written without error.

**F4. `_format_conversation` can exceed `context_chars`.**
- Cause: the trim loop never goes below the last 14 entries.
- Fix: add these steps after the existing loop, applied in order and only while the text is still over budget:
  1. Shorten every entry except the last 4 to its first 300 + last 300 characters, joined with `…(trimmed)…`.
  2. Keep only the header and the last 4 entries.
  3. Cap each of the last 4 entries at `context_chars // 5` characters, keeping head and tail.
- Never cut the header (the task).
- Test: `context_chars=4000`, 20 entries of 1,500 characters each. Expect `len(output) <= 4000 + len(header) + 300`. The header and the tail of the last entry must be present.

**F5. `OpenAIEngine` robustness.**
- Construct the client as `OpenAI(..., max_retries=0, timeout=request_timeout)`.
- Our own retry loop handles `RateLimitError`, `APIConnectionError`, `APITimeoutError` and `InternalServerError`:
  - up to 6 attempts;
  - wait for `Retry-After` if present, otherwise `min(60, 2**attempt) + random.random()`;
  - add each sleep to `self.backoff_seconds`.
- Temperature: use `temperature if temperature is not None else self.temperature`. The current `or` turns 0 into 0.1.
- New optional constructor arguments: `seed=None` (sent only when not None) and `request_timeout=600`.
- Test: a fake client raises `RateLimitError` twice, then succeeds, with `time.sleep` patched. Expect 3 calls and `backoff_seconds > 0`.

**Document these in REPORT.md, but do not fix them:**
- `ErrorMemory.record` is dead code: its condition is checked after `last_action_failed` has already been overwritten.
- `_raster_tail` writes multi-band output with `count=1`.
- `load_raster` loads the whole raster as float64.
- There are no `area` or `nearest` ops.

## A6. Folder layout

```
kerala\
  __init__.py  requirements-kerala.txt  .env.example  Modelfile  models.yaml  config.py
  MASTERPROMPT.md                 (this prompt, saved verbatim)
  prompts\phase_0.md … phase_6.md (Part B split per phase, verbatim)
  tools\smoke_run.py              (Phase 0 timing)
  prepare_data.py                 (Phase 2)
  pack\kerala_pack.yaml  pack\pack.py
  agent.py                        (KeralaAgent, AnswerChecker, build_system_prompt, compose_task)
  bench\questions.yaml  rubric.yaml  gold.py  gold.json  gold_sensitivity.json  frozen.json
  bench\run_one.py  run_bench.py  score.py
  ask.py                          (demo CLI)
data\kerala\layers\   agent-visible files only (read-only after Phase 2)
data\kerala\meta\     data_manifest.json, cache\ (quicklook, masks), never linked to the agent
results\runs\<batch>\<model>\<qid>\<arm>\   per-run outputs (git-ignored)
results\summary\      tables, figures (committed)
logs\                 background command logs (git-ignored)
tests\test_kerala_fixes.py  test_kerala_pack.py  test_kerala_checker.py  test_kerala_leak.py
tests\test_kerala_frozen.py  test_kerala_harness.py
AGENTS.md  PROGRESS.md  REPORT.md  README_KERALA.md  INTERVIEW_PREP.md
```

## A7. Run settings (identical across arms; local and cloud as similar as possible)

| Setting | `local-qwen7b` | `cloud-flashlite` |
|---|---|---|
| base_url | `http://localhost:11434/v1` | Gemini OpenAI-compatible endpoint |
| model | `gisclaw-qwen7b-16k` | the exact Flash-Lite ID you found |
| temperature | 0 | 0 |
| seed | 1 | only if the API accepts it (test it once; record the result) |
| max_tokens | 1536 | 1536 |
| max_rounds | 12 | 12 |
| sandbox timeout per snippet | 300 s | 300 s |
| context_chars | 24000 | 24000 |
| wall clock per run | 25 min | 25 min, plus the time spent in backoff sleeps |
| rpm limit | — | value from AI Studio; default 8 |

**Acceptance for the context budget:** across all smoke runs, the largest `prompt_tokens` value must be ≤ 14,500.

**`kerala\models.yaml`** has three entries: `local-qwen7b`, `cloud-flashlite` and `stub`. The `stub` entry is the scripted engine used by tests.

## A8. Session protocol (also goes into AGENTS.md)

**At the start of every session:**
1. Read `AGENTS.md`, `PROGRESS.md`, and the output of `git log --oneline -15`.
2. Open `kerala\prompts\phase_<current>.md`.
3. Continue from the first unchecked sub-step.

**While you work:**
- Never redo a phase that has already been committed, unless `PROGRESS.md` marks it as broken.
- Make a `wip:` commit after each sub-step.

**At the end of a phase:**
1. Run the acceptance commands.
2. Update `PROGRESS.md`.
3. Commit with the message `phase N: <summary>`.
4. Stop if the phase has a STOP gate.

---

# PART B: Phases

## Phase 0: Setup, split this prompt, and measure (STOP gate)

1. **Back up and initialise git.**
   - Run `git init`.
   - Create `.gitignore`. It must include: `.venv/`, `kerala/.env`, `results/runs/`, `data/kerala/meta/cache/`, `logs/` and `__pycache__/`.
   - Commit everything as `upstream: GISclaw main (zip)`.
2. **Save the prompt and split it.**
   - Save this entire prompt verbatim to `kerala\MASTERPROMPT.md`.
   - Copy each Phase section of Part B verbatim into `kerala\prompts\phase_N.md`, and add a link to Part A at the top of each file.
3. **Write `AGENTS.md`** (at most 120 lines). It contains:
   - A1's goal in one paragraph;
   - all of A3's rules, condensed, with the do-not-do items kept verbatim;
   - the editable-files list;
   - the PowerShell and venv conventions;
   - the table of phases with their acceptance commands;
   - A8's session protocol;
   - a pointer to `kerala\MASTERPROMPT.md`.
4. **Write `PROGRESS.md`** using the template in Phase 6's appendix, with sub-step checkboxes for every phase.
5. **Create the small files:**
   - `kerala\requirements-kerala.txt`, containing `pystac-client` and `planetary-computer`;
   - `kerala\.env.example`, containing `GEMINI_API_KEY=`;
   - `kerala\Modelfile`, containing:
     ```
     FROM qwen2.5-coder:7b
     PARAMETER num_ctx 16384
     ```
6. **Build the venv in the background, with a log.** Do not create any desktop shortcut.
   1. Install `uv` if it is missing.
   2. `uv python install 3.11`
   3. `uv venv --python 3.11 .venv`
   4. `uv pip install --python .venv\Scripts\python.exe -r desktop\requirements-desktop.txt -r requirements-dev.txt -r kerala\requirements-kerala.txt`
7. **Record the baseline tests.** Run `.\.venv\Scripts\python.exe -m pytest -q tests --ignore=tests\test_ui.py` and write the pass/fail counts into `PROGRESS.md`.
8. **Set up Ollama.**
   1. If Ollama is missing, run `winget install Ollama.Ollama`.
   2. Run `ollama pull qwen2.5-coder:7b` in the background.
   3. Run `ollama create gisclaw-qwen7b-16k -f kerala\Modelfile`.
   4. After one call, check `loaded_context` and confirm it is **16384**.
9. **Measure timing.** `kerala\tools\smoke_run.py` runs a plain `GISReActAgent` once on `examples\urban-heat-madison` with the task "Compute the mean temperature per block and save a choropleth PNG", using `gisclaw-qwen7b-16k`.
   - For every call, log prompt tokens, completion tokens and wall time.
   - Do this twice: once with the Vulkan default, and once CPU-only (`OLLAMA_VULKAN=0`, server restarted as described in A2).
   - Record in `PROGRESS.md`:
     - seconds per call;
     - number of calls;
     - minutes per run;
     - peak RAM;
     - which backend was used (from the server log);
     - which backend you recommend.

**Acceptance:**
- the baseline test counts are recorded;
- the timing table is filled in;
- the context window is confirmed at 16384;
- `AGENTS.md` and `kerala\prompts\` exist.

**STOP. Report to me:**
- minutes per run;
- projected hours for the 52-run local matrix in Phase 5 (and the cloud matrix too);
- the projected share of runs that would hit the 25-minute limit.

If the local projection is over 20 h, propose cuts. Wait for my decision.

## Phase 1: Upstream fixes F1–F5 (A5)

**Acceptance:**
```
.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_fixes.py
.\.venv\Scripts\python.exe -m pytest -q tests --ignore=tests\test_ui.py
```
The second command must show no regressions against the Phase 0 baseline.

## Phase 2: Data preparation (`kerala\prepare_data.py`, resumable; run it in the background)

Sub-steps (each one caches its output and is skipped if already done):

1. **Area of interest.** Geocode the two districts with `osmnx.geocode_to_gdf` using "Ernakulam district, Kerala, India" and "Alappuzha district, Kerala, India". If that fails, fall back to `boundary=administrative`, `admin_level=5`.
2. **Taluks.**
   - Take `admin_level=6` features. Keep Polygon and MultiPolygon only.
   - Keep a taluk only if its representative point lies inside the area of interest.
   - Fields:
     - `name`: OSM `name:en` if present, otherwise `name`;
     - `name_local`;
     - `district`.
   - **VERIFY:**
     - there are about 13 taluks (7 in Ernakulam, 6 in Alappuzha);
     - one of them is named like "Kuttanad";
     - names are ASCII.

   If not, stop under **Needs Kirito**. Do not invent boundaries.
3. **Target grid.** EPSG:32643, 30 m pixels, covering the area-of-interest bounding box snapped to 30 m. Pixels outside the area of interest are nodata.
4. **Write the layers** to `data\kerala\layers\`, using exactly these names:

| File | CRS | Fields and notes |
|---|---|---|
| `districts.gpkg` | EPSG:32643 | `name` |
| `taluks.gpkg` | EPSG:32643 | `name`, `name_local`, `district` |
| `hospitals.geojson` | **EPSG:4326** | `osm_id`, `name`, `geom_kind`. Keep the OSM mix of Points and Polygons, and keep features that intersect the area of interest. |
| `schools.geojson` | **EPSG:4326** | Same as hospitals. |
| `roads_major.gpkg` | EPSG:32643 | `highway`, `name`. LineStrings only. |
| `s1_vv_20180821_db.tif` | EPSG:32643 | float32, NaN nodata. Mosaic the two slices, average-resample in linear units, then convert to dB. |
| `jrc_seasonality.tif` | EPSG:32643 | uint8, nodata 255, nearest-neighbour resampling. |
| `dem_cop30.tif` | EPSG:32643 | float32 metres, bilinear resampling. |
| `flood_extent_20180821.gpkg` | EPSG:32643 | The reference flood, built in sub-step 5. |

   The CRS mix is deliberate: CRS handling is part of what we test.
5. **Reference flood.**
   1. Compute `T_raw` = the Otsu threshold of VV dB over valid pixels inside the area of interest. Use numpy only, with 256 bins over [−30, 5].
   2. Set **T = round(T_raw, 1)** and use the rounded value everywhere from here on.
   3. **VERIFY** that −22 ≤ T ≤ −13. If not, stop.
   4. Water = `VV_dB ≤ T`.
   5. Permanent water = `seasonality ≥ 10`.
   6. Steep = slope > 5°, computed from `dem_cop30.tif` with `np.gradient` at 30 m spacing.
   7. Flood = water AND NOT permanent AND NOT steep, inside the area of interest.
   8. Polygonize the flood mask with `rasterio.features.shapes`, dissolve the result, and write it with the field `source="S1A 2018-08-21 VV Otsu T=<T>"`.
   9. Do not simplify the polygons.
6. **Meta outputs** go in `data\kerala\meta\`:
   - `data_manifest.json`, containing:
     - STAC item IDs, unsigned asset hrefs and acquisition times;
     - the RTC units you found;
     - `T_raw` and `T`;
     - pixel counts and km² for water, permanent water, steep ground and flood, per district;
     - feature counts per layer;
     - the OSM retrieval time;
     - library versions;
     - the SHA-256 of every layer file.
   - `cache\flood_mask_20180821.tif`.
   - `cache\quicklook.png`: VV dB with flood in blue and permanent water in dark blue over the outlines.
7. **Optional cross-check** (time-boxed to 20 minutes).
   - Export a PNG over the same bounding box from the NASA Disasters MapServer: `https://maps.disasters.nasa.gov/ags03/rest/services/Kerala_India_Flood/Sentinel1_20180821_water_extent/MapServer/export`
   - Save it as `meta\cache\nasa_compare.png`, placed next to the quicklook.
   - Skip this step if it fails.
8. **Lock the layers.** Run `attrib +R` on every file in `layers\`.

**Acceptance:** `.\.venv\Scripts\python.exe -m kerala.prepare_data --check` exits 0. It checks:
- the files exist;
- each layer has the right CRS;
- every raster is under 25 million pixels;
- T is within range;
- flood km² is greater than 0 and less than the area of interest;
- the manifest hashes match.

**Report in `PROGRESS.md`:** T, flood km² per district, and the taluk list.

## Phase 3: Pack, AnswerChecker, KeralaAgent, prompt (offline tests only)

### `kerala\pack\kerala_pack.yaml` (schema v1)

Each parameter has these fields:
- `value`
- `unit`
- `description` (one line, no value in it)
- `kind`: one of `calibrated`, `standard_practice`, `project_convention`
- `provenance`
- `rationale`
- `plausible_range` (or null)

Label conventions honestly.

| Key | Value | Kind | Note |
|---|---|---|---|
| `project_crs` | EPSG:32643 | standard_practice | UTM 43N covers 72–78°E |
| `flood_date` | 2018-08-21 | calibrated | S1A descending; same date as Vishnu et al. 2019; water had partly receded |
| `water_threshold_vv_db` | T from the manifest | calibrated | Otsu on the area-of-interest VV histogram; plausible range [−22, −13] |
| `permanent_water_rule` | `jrc_seasonality >= 10` | standard_practice | UN-SPIDER recommended practice |
| `max_flood_slope_deg` | 5 | standard_practice | Slope mask from the same practice |
| `low_lying_max_elevation_m` | 10 | project_convention | Copernicus DEM heights (EGM2008) |
| `relief_camp_hospital_access_m` | 3000 | project_convention | Straight-line distance; sensitivity is reported |
| `facility_point_rule` | `representative_point` | project_convention | Reduce polygon facilities with shapely `representative_point()` |
| `raster_area_rule` | `pixel_count * 900 m2, pixel centre inside zone` | project_convention | |

### `kerala\pack\pack.py`

- `load_pack()` validates the schema.
- `index_text(keys)` lists only the keys you pass it, each with its description and **no values**.
- `domain_param(key: str = "")` is the agent tool:
  - it returns value, unit, kind, provenance and rationale;
  - for an unknown or empty key, it returns the list of available keys;
  - every call is appended to `pack_calls.jsonl` in the work directory.

### `kerala\agent.py`

**`build_system_prompt(tool_descriptions, arm, needs_params, data_text)`** returns `SYSTEM_PROMPT.format(...)` with exactly these slot values:
- `tool_descriptions=tool_descriptions`
- `skill_rule=""`
- `skills_block=SKILLS_BLOCK.format(skills=<SkillsStore always block>)`
- `catalog_block=""`
- `data_block=DATA_BLOCK.format(data=data_text)`
- `memory_block=""`
- `context_block=""`

**For `arm == "pack"` only**, append this section:
```
## Domain pack (Kerala 2018)
<index_text(needs_params)>
Call domain_param(key) to get a value before you use it; cite the key in parameters_used.
```

If `needs_params` is empty (control questions), the section says "This question needs no pack parameters." The `domain_param` tool is still available. This lets us measure whether the pack distracts the agent.

**`data_text`** is computed **once per batch**:
1. Create a temporary folder `results\_profile\data`, as a junction to `data\kerala\layers`.
2. Run `profile_project` on `results\_profile`, then `build_block`.
3. Save the result to `results\_profile\data_block.txt`. This text is identical for every run.

**`compose_task(question, arm)`** builds: the question text + the parameter section + the answer contract.

The parameter section depends on the arm:

| Arm | Parameter section |
|---|---|
| all arms | "Parameters this question depends on: <needs_params key names>." |
| A1 | "Choose a value for each, state it in `parameters_used` using exactly these key names." |
| A2 | "Use these values: <key = value unit, …>." |
| A3 | "Get their values with `domain_param`." |

Control questions with an empty `needs_params` get no parameter section.

**The answer contract** is identical in every arm. The agent must write `pred_results\answer.json`:
```json
{"question_id": "<id>", "status": "ok" | "cannot_answer",
 "value": <number | string | null>, "unit": "<count|km2|km|percent|m|name>" | null,
 "parameters_used": {"<key>": <value>},
 "assumptions": "<one sentence>", "method": "<one sentence>"}
```
If the data cannot support an answer, use `status: "cannot_answer"` and `value: null`, and give the reason in `assumptions`.

**`KeralaAgent(GISReActAgent)`** overrides `_validate_outputs(work_dir)`:
1. Increment an attempt counter n, starting at 1.
2. Copy `pred_results\answer.json` to `work_dir\attempts\answer_<n>.json`. If the file is missing, write `{"missing": true}` there instead.
3. Run `super()._validate_outputs(work_dir)`.
4. Run the AnswerChecker.
5. Append the result to `work_dir\checker.jsonl`.
6. Return the combined issues string.

**The AnswerChecker** is **pack-free** and identical in every arm. It never mentions parameter values. It checks:
- the file exists and parses, and all keys are present;
- `status` is valid;
- if the question's `expected_status` is `ok`, then `value` is not null and `unit` equals `expected_unit`;
- counts are integers ≥ 0;
- percentages are between 0 and 100;
- for km²:
  - values must be ≥ 1 and ≤ the area of interest's area;
  - anything under 1 is rejected with the message "looks like an area computed in degrees or the wrong unit; work in a projected CRS".
  - The area of interest's area is passed in by `run_one` from the manifest; the agent never sees the manifest.

There is **no** in-loop geographic-CRS code scan, because the sandbox cannot be reached from this hook. That check lives in `score.py`.

### Tests

**`tests\test_kerala_pack.py`, `tests\test_kerala_checker.py` and `tests\test_kerala_leak.py`**, all offline using the StubEngine. They cover:
- the pack schema;
- `domain_param` output;
- `index_text` contains no values;
- the checker accepts a valid answer and rejects each invalid case;
- attempt snapshots are numbered from 1;
- the A1, A2 and A3 system prompts differ only in the pack section;
- the A1, A2 and A3 tasks differ only in the parameter section.

**Leak test.** For every arm, the system prompt and task must not contain:
- `manifest`
- `flood_mask`
- `quicklook`
- the string of T to 1 decimal place (except in A2's inline values)

The same test also checks that listing the agent's `dataset\` folder shows only the nine layer files: nothing from `meta\`, `kerala\bench\` or `kerala\pack\`.

**Acceptance:**
```
.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_pack.py tests\test_kerala_checker.py tests\test_kerala_leak.py
```

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

## Phase 5: Runner, scorer, demo, smoke tests

### `kerala\bench\run_one.py`

Arguments: `--qid --arm --model --out`.

1. Load the model entry from `models.yaml` and read the API key from `kerala\.env` if needed.
2. Remove `*_API_KEY` from `os.environ`.
3. Build `OpenAIEngine`, then **call `load_model()`**.
4. Create a fresh work directory.
5. Create a fresh `KeralaAgent` with `data_dir=data\kerala\layers` and the A7 settings.
6. Compose the task and run.

**Write to `--out`:**
- `answer.json`
- `attempts\`
- `code.py`
- `trace.jsonl` (every `on_step` event)
- `pack_calls.jsonl`
- `checker.jsonl`
- `meta.json`

**`meta.json` fields:**
- model ID;
- Ollama model digest (from `/api/show`) or the cloud model ID;
- arm;
- rounds;
- LLM calls;
- prompt and completion tokens;
- maximum prompt tokens;
- wall seconds;
- `backoff_seconds`;
- `exit_reason`, one of:
  - `finished`
  - `max_rounds`
  - `timeout`
  - `error`
  - `paused_quota`
- git commit;
- pack hash.

Classify text containing `429` or `RESOURCE_EXHAUSTED` as `paused_quota`.

### `kerala\bench\run_bench.py`

Arguments: `--model --batch --questions --arms --resume --dry-run`.

- **One subprocess per run.** Start it with `subprocess.Popen([".venv\\Scripts\\python.exe", "-m", "kerala.bench.run_one", ...], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)`.
- **On the wall-clock limit**, kill the process tree with `taskkill /PID <pid> /T /F` and record `timeout`. For cloud runs, extend the limit by the backoff time reported in a heartbeat file.
- **Before and after each run**, verify the `layers\` hashes and the directory listing against `frozen.json`. If anything has changed, abort the batch.
- **`--resume`** skips only runs whose `exit_reason` is `finished`, `max_rounds` or `timeout`. Runs that ended in `paused_quota` or `error` are re-run.
- **Quota.** For cloud models:
  - apply a client-side requests-per-minute limiter;
  - after 3 consecutive `paused_quota` results, stop the batch cleanly and print "quota exhausted, resume tomorrow".
- **Order.** Group runs by question, keeping all arms of one question next to each other. Rotate the arm order with the question index to counterbalance drift.
- **ETA.** Print an estimated time remaining after every run.

### `kerala\bench\score.py`

Writes everything to `results\summary\`.

**Per-run columns:**
- `format_ok`
- `correct_final`
- `correct_first_attempt` (from `attempts\answer_1.json`)
- `checker_rejections`
- `pack_calls`
- `params_reported`
- `params_in_code` (a reported value appears literally in `code.py`)
- `geographic_measure_flag`: a regex over `code.py` finds `.area`, `.length`, `.buffer(` or `.distance(` used on a variable loaded from `hospitals.geojson` or `schools.geojson`, with no `to_crs` applied to that variable before it.
- For A1 only:
  - `assumption_stated`
  - `assumption_defensible`
  - `correct_given_own_params` = the answer equals `gold_fn(qid, own_params)` when every reported value is defensible.
- `minutes`
- `tokens`

**Aggregates:**
- accuracy per question × arm;
- paired tables (both right / only X right / only Y right / both wrong) for:
  - A3 vs A2 on the P questions;
  - A2 vs A1 on the P questions;
  - A3 vs A1 on the C questions;
- an exact sign-test p-value, labelled "descriptive";
- minutes per correct answer and tokens per correct answer, by arm and model.

**Taxonomy.** One primary label per failed run, using the same label set for every arm. Apply the first label that matches, in this order:
1. `TIMEOUT` (excluding timeouts where backoff took more than 50% of the time; those are `RATE_LIMIT`)
2. `CRASH`
3. `FORMAT`
4. `CONTEXT` (the run shows trim markers)
5. `UNANSWERABLE_ANSWERED`
6. `REFUSED_ANSWERABLE`
7. `CRS_UNIT` (a checker degrees rejection or `geographic_measure_flag`)
8. `PARAM_CHOICE` (wrong against the pack, but correct given its own parameters)
9. `TOOL_BUG` (a traceback inside a geoprocess template)
10. `LOGIC`

`pack_calls == 0` in A3 is reported as a separate diagnostic column, not as a label.

Write `taxonomy_auto.csv` with an empty `manual_label` column for me to fill in.

**Figures** (PNG):
- accuracy by arm, with a dot for each question;
- a stacked taxonomy bar per arm;
- first-attempt vs final accuracy (the AnswerChecker effect);
- sensitivity: P05/P06 against T, P03 against distance, P09 against elevation, with A1-chosen values marked.

**Tables:** also write `results_tables.md`.

### `kerala\ask.py` (demo)

```
.\.venv\Scripts\python.exe -m kerala.ask "<question>" --model local-qwen7b
```
- Runs the pack arm.
- Prints the answer, the `domain_param` calls and the checker log.
- Renders `results\demo\<timestamp>\map.png` from the outputs, with district outlines drawn on top.

### Tests

`tests\test_kerala_harness.py`, offline, using the `stub` model. It must cover:
- `run_bench` end to end;
- resume;
- the timeout kill, using a stub that sleeps;
- `paused_quota` handling;
- a hash change aborting the batch;
- `score.py` producing every output file.

### Smoke tests (these are the only model runs you may make; run them in the background)

1. D01, D02 and D03 × the pack arm × `local-qwen7b`.
2. D01 × the pack arm × `cloud-flashlite`.
3. **Floor check:** P01 and P06 × all three arms × `local-qwen7b` (6 runs).

Report:
- the smoke scores;
- the largest `prompt_tokens` value (it must be ≤ 14,500);
- minutes per run.

**If fewer than 2 of the 6 floor-check runs are `correct_given_own_params` or `correct_final`, STOP.** Propose a smaller or easier P set, and do not run the matrix.

**Acceptance:**
```
.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_harness.py tests\test_kerala_frozen.py
```
and the smoke results recorded.

**STOP.** Give me the matrix commands:
- local:
  - P01–P12 × {noparam, inline, pack} = 36 runs;
  - C01–C08 × {noparam, pack} = 16 runs;
  - 52 runs in total;
- cloud: the same 52 runs, spread over about 2 days with `--resume`.

Also include:
- the expected hours, based on the Phase 0 timing;
- `powercfg /change standby-timeout-ac 0` to stop sleep, and the command to restore it;
- how to watch progress;
- a reminder to commit to git and back up before each batch.

## Phase 6: After I say "matrix done": score, analyse, write

1. Run `score.py`.
2. Read at least 10 failed traces spread across the taxonomy labels.
3. **Draft `REPORT.md`** with real numbers only, and leave `TODO(Kirito)` markers for the manual taxonomy and interpretation. Sections:
   1. **Problem.**
   2. **Related work.**
      - GISclaw (arXiv 2603.26845): single-agent was best on large models; 14B improved from 52% to 79% with planner+worker; domain parameters were a failure point.
      - GeoAnalystBench.
      - The UN-SPIDER practice.
      - Vishnu et al. 2019.
   3. **System.**
      - A Mermaid diagram.
      - What was reused vs added.
      - F1–F5 with before/after.
      - The documented upstream issues.
   4. **Data and pack.**
      - Sources, CRS, the reference-flood method and T.
      - Each parameter with its kind and provenance.
   5. **Benchmark design.**
      - The arms, and why parameter names are given to every arm.
      - Controls, the independence of gold, tolerances, the freeze.
      - The pre-registered expectation.
   6. **Results.**
      - The per-question table and the paired tables.
      - First attempt vs final.
      - `correct_given_own_params`.
      - The cloud ceiling.
      - Cost (minutes and tokens per correct answer) on a 16 GB laptop.
   7. **Failure taxonomy.** Three annotated traces.
   8. **Limitations.**
      - 20 questions, one seed;
      - SAR misses water under vegetation and in urban areas (Ernakulam);
      - partial recession by 21 Aug;
      - OSM data is from today, not 2018;
      - conventions are choices, with a sensitivity figure.
   9. **Future work.**
   10. **Attributions:**
       - © OpenStreetMap contributors (ODbL);
       - Copernicus Sentinel data 2018 (RTC via Microsoft Planetary Computer);
       - Copernicus DEM GLO-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA;
       - JRC Global Surface Water (Pekel et al. 2016);
       - GISclaw © Han Jinzhen (AGPL-3.0).
4. **Write `README_KERALA.md`.** Cover what the project is, exact reproduction commands, the attributions, and the licence.
5. **Write `INTERVIEW_PREP.md`.** It holds plain-language explanations I must be able to give:
   - SAR backscatter and dB;
   - the Otsu threshold;
   - why UTM is used for areas;
   - representative point vs centroid;
   - the three arms and why parameter names go to every arm;
   - `correct_given_own_params`;
   - the sign test, and why it is only descriptive;
   - F1–F5;
   - the top 3 failure modes, each with its trace path;
   - 10 likely interviewer questions with short answers drawn from our actual results.
6. **Extras** (in this order, only after 1–5 are done):
   1. `kerala\upstream\F1.patch`, `F2.patch` and `PR_F1_F2.md`, a ready-to-paste PR body with before/after numbers. Do not push.
   2. `kerala\bench\trace_html.py`: a standard-library-only HTML viewer for a `trace.jsonl` file. Link the three annotated traces from `REPORT.md`.

**Acceptance:** every number in `REPORT.md` appears in `results\summary\results_tables.md` or in the manifest. Run a small script that checks this and paste its output.

### Appendix: `PROGRESS.md` template
```
# PROGRESS
## Status: Phase <n> — <in progress | done | blocked | STOP: waiting for Kirito>
## Checklist
- [ ] Phase 0
  - [ ] 0.1 git init + .gitignore …  (one line per sub-step)
- [ ] Phase 1 …
## Numbers so far
(timing table, baseline tests, T, flood km² per district, taluks, gold table, smoke results)
## Decisions made (with reason)
## Needs Kirito
## Last acceptance output
(command + last 15 lines)
```

---

## Start now

Do Phase 0. Stop at its STOP gate.
