# KeralaFloodBench: an LLM GIS agent for the 2018 Kerala floods

An AI agent answers plain-English questions about the August 2018 Kerala floods. It writes and runs real GIS code on Sentinel-1 radar, elevation and OpenStreetMap data, and checks its own answers.
A frozen benchmark (20 test questions with independently computed, hash-locked gold answers) measures whether small models fail on expert parameters or on GIS execution.
The local model studied is gpt-oss:20b. Its dominant failure turned out to be tool-protocol confusion, not missing domain knowledge.

## Headline results (repeat 1, `matrix_gptoss_v1`, 52 runs)

| Arm | What the model gets | Correct | correct_given_own_params |
|---|---|---:|---:|
| A1 `noparam` | parameter names only; it chooses the values | 5 / 20 | 2 |
| A2 `inline` | values written into the question | 1 / 12 | — |
| A3 `pack` | values from a sourced `domain_param(key)` tool | 6 / 20 | — |
| **All** | | **12 / 52** | |

Sources: `results/summary/matrix_gptoss_v1/failure_report.md` and `per_run.csv`. There is about one run per question per arm, so the arm differences are **not** statistically meaningful (descriptive sign tests: p = 1.00).

**Floor check** (model selection; P01 + P06 × 3 arms; pass at ≥ 2/6):

| Model | Score |
|---|---|
| gpt-oss:20b after the F8 integration fix | **2/6** (borderline pass) |
| gemini-3.5-flash-lite | 1/6 |
| qwen3.5:9b | 0/6 |
| qwen2.5-coder:7b | 0/6 |

Details are in `results/summary/matrix_gptoss_v1/results_tables.md`.

## Key findings

- **Tool-protocol confusion dominates.** 39 of the 40 incorrect runs contain a call the toolkit rejects before any GIS runs:
  - `geoprocess op=load_vector` (39 events) and `op=list_files` (28), although these are separate tools;
  - wrong argument names;
  - calls to non-existent tools such as `commentary`.
  
  26 incorrect runs never wrote `answer.json`.
- **The pack was used, but not always applied.** All 12 pack-arm parameter questions called `domain_param`, and the 8 pack-arm controls made 0 calls. P01/pack retrieved the `representative_point` rule and then joined whole polygons.
- **P01 separates method errors from execution errors.**
  - In the floor check, Gemini and Qwen 3.5 returned exactly 96 and 161. Those are the gold values for whole-polygon `intersects`, so they chose a defensible but different predicate.
  - gpt-oss's 82 is exactly `intersects` at 100 m with the district filter skipped, a method choice plus an execution error.
- **Two upstream GISclaw bugs were found and fixed, each with a regression test:**
  - F1: `count_in_polygon` counted empty polygons as 1;
  - F2: slope on a geographic DEM gave about 89.95° for a 0.57° ramp.
  
  Patches are in [`kerala/upstream/`](kerala/upstream/).
- **Honest limitations:** a single repeat, small n, one model, a post-hoc radar threshold (T = −14.0 dB, ±1 dB sensitivity reported), and a DSM rather than a DTM. A second repeat was started but stopped at 35/52 runs when access to the GPU machine was lost; it is not used in any result.

## Quick start (Windows, PowerShell, repo root; no GPU or model needed)

```powershell
# 1. Environment (Python 3.11 via uv)
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe -r desktop\requirements-desktop.txt -r requirements-dev.txt -r kerala\requirements-kerala.txt

# 2. Tests: Kerala suite, frozen-hash check, independent gold check
$t = Get-ChildItem tests -Filter "test_kerala_*.py" | ForEach-Object FullName; .\.venv\Scripts\python.exe -m pytest -q $t
.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_frozen.py
.\.venv\Scripts\python.exe -m kerala.bench.gold --check

# 3. Re-score repeat 1 from the committed run files (expect "Scored 52 runs"; 12 correct)
.\.venv\Scripts\python.exe -m kerala.bench.score --batch matrix_gptoss_v1 --out results\summary\matrix_gptoss_v1
```

Running the agent itself needs Ollama and `gpt-oss:20b`; see [`README_KERALA.md`](README_KERALA.md). Re-scoring rewrites `results_tables.md` without the appended floor and gold sections; restore them with `git checkout -- results/summary/matrix_gptoss_v1/results_tables.md`.

## Documents

- [`REPORT.md`](REPORT.md): the full report (system, data, benchmark design, model selection, fixes, results, failure taxonomy, limitations).
- [`INTERVIEW_PREP.md`](INTERVIEW_PREP.md): plain-language explanations and Q&A.
- [`README_KERALA.md`](README_KERALA.md): full reproduction, layout and setup notes.
- [`PROGRESS.md`](PROGRESS.md): the session log of every decision, validation and fix.
- Trace pages (self-contained HTML; download them and open locally):
  - [P08/pack, correct](results/summary/matrix_gptoss_v1/traces/P08_pack.html);
  - [P01/pack](results/summary/matrix_gptoss_v1/traces/P01_pack.html);
  - [P01/noparam](results/summary/matrix_gptoss_v1/traces/P01_noparam.html);
  - [C02/noparam](results/summary/matrix_gptoss_v1/traces/C02_noparam.html);
  - [P06/pack](results/summary/matrix_gptoss_v1/traces/P06_pack.html).
- Analysis files: [`findings_r1.md`](results/summary/matrix_gptoss_v1/findings_r1.md), [`failure_report.md`](results/summary/matrix_gptoss_v1/failure_report.md), [`number_check.md`](results/summary/number_check.md).

## Credits and licence

- Built on [GISclaw](https://github.com/geumjin99/GISclaw), AGPL-3.0-or-later. GISclaw's original README is kept as [`README_GISCLAW.md`](README_GISCLAW.md).
- This project stays **AGPL-3.0-or-later**; see [`LICENSE`](LICENSE). New source files carry SPDX headers.
- Implemented with AI coding agents (Codex, Claude Code) under my direction; design decisions, validation and fixes are logged in PROGRESS.md.

## Data attributions

- Contains modified **Copernicus Sentinel-1** data (2018), accessed via **Microsoft Planetary Computer** (Sentinel-1 RTC).
- **JRC Global Surface Water** (Pekel et al. 2016, *Nature* 540, 418–422).
- **Copernicus DEM GLO-30** © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA.
- © **OpenStreetMap contributors**, licensed under the Open Database License (ODbL).
