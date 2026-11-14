# Working instructions

## Goal
Build KeralaFloodBench on GISclaw: an agent that answers plain-English questions about the August 2018 Kerala floods by writing and running real GIS code on satellite and map data, checks its own answer, and supports a measured study of whether sourced, tool-retrieved domain parameters help a small model. The three arms are noparam (parameter names only), inline (same values in the task), and pack (same values retrieved through a tool). Report paired outcomes and distinguish parameter choice from GIS execution without overstating small-sample evidence.

## Rules and boundaries
- The fork stays AGPL-3.0-or-later. Every new .py file gets the repo's SPDX header. Never copy code from the MIT-licensed paper-v2 branch. Do not recreate the planner, worker or orchestrator.
- Upstream files you may edit, and only for fixes F1–F5 in A5: src\agent\geo_ops.py, src\agent\react_agent.py, src\agent\llm_engine.py.
- Everything else you create goes in kerala\, tests\test_kerala_*.py, data\kerala\ (generated), results\ (generated), logs\, AGENTS.md, PROGRESS.md, REPORT.md, README_KERALA.md and INTERVIEW_PREP.md.
- Do not touch app\, desktop\, Dockerfile or install.*. Do not refactor, rename or reformat upstream code.
- Dependency additions are limited to pystac-client and planetary-computer, listed in kerala\requirements-kerala.txt; the existing requirements-dev.txt. Do not add xarray, stackstac, odc-stac, scikit-image, torch, langchain or similar.
- Never edit a frozen file, a gold value or a tolerance to make a test or score pass. Never hard-code answers in any code the agent can see. If you think a gold value is wrong, report it under Needs Kirito.
- Gold is independent: kerala\bench\gold.py uses plain geopandas, shapely, rasterio and numpy. It never imports src.agent.
- You build; Kirito runs the experiment. The only model runs you may make are the smoke runs listed in Phase 5. Never start the full matrix.
- Downloads use windowed reads from Cloud-Optimised GeoTIFFs, through signed URLs and /vsicurl/. Never download whole scenes. Abort if the total would pass about 1.5 GB.
- Every raster the agent sees is single-band, 30 m, clipped, and under 25 million pixels. GISclaw's load_raster reads the whole raster as float64.
- The agent never sees the answer key. Agent runs see only data\kerala\layers\. The manifest, cache, kerala\bench\ and kerala\pack\ stay outside its dataset folder.
- kerala\.env is git-ignored. run_one.py removes any *_API_KEY variables from the environment before the agent starts.
- GISclaw's built-in check (_validate_outputs, which catches blank PNGs and empty CSVs) is the output guard. Ours is the AnswerChecker. Never call either one "the validator".
- A phase is done only when its acceptance command has passed in this session. Paste the command and the last 15 lines of its output into PROGRESS.md. Report failures and anything skipped. For an irreversible or design-changing decision, ask under Needs Kirito and stop at the next STOP gate.

## Editable files
Besides the three upstream fix files above, create only the files listed in Part A/A6 and the phase instructions: kerala\, tests\test_kerala_*.py, generated data\kerala\, generated results\, logs\, AGENTS.md, PROGRESS.md, REPORT.md, README_KERALA.md, and INTERVIEW_PREP.md.

## Shell and Python
Use PowerShell. Set variables with $env:X="y"; use ; or new lines, not && unless PowerShell 7+. Always run Python as .\.venv\Scripts\python.exe; never use bare python. Run long commands in the background with stdout and stderr logs; make them resumable. Do not create a desktop shortcut.

## Phase acceptance
| Phase | Acceptance |
|---|---|
| 0 | Baseline test counts recorded; timing table filled; Ollama context confirmed at 16384; AGENTS.md and kerala\prompts\ exist. |
| 1 | .\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_fixes.py and full baseline .\.venv\Scripts\python.exe -m pytest -q tests --ignore=tests\test_ui.py; no regressions. |
| 2 | .\.venv\Scripts\python.exe -m kerala.prepare_data --check |
| 3 | .\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_pack.py tests\test_kerala_checker.py tests\test_kerala_leak.py |
| 4 | .\.venv\Scripts\python.exe -m kerala.bench.gold --check; STOP for Kirito's review and approval. |
| 5 | .\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_harness.py tests\test_kerala_frozen.py plus smoke results; STOP before matrix. |
| 6 | Report-number check described in Phase 6. |

## Session protocol
At the start of every session:
1. Read AGENTS.md, PROGRESS.md, and the output of git log --oneline -15.
2. Open kerala\prompts\phase_<current>.md.
3. Continue from the first unchecked sub-step.

While you work:
- Never redo a phase that has already been committed, unless PROGRESS.md marks it as broken.
- Make a wip: commit after each sub-step.

At the end of a phase:
1. Run the acceptance commands.
2. Update PROGRESS.md.
3. Commit with the message phase N: <summary>.
4. Stop if the phase has a STOP gate.

See kerala\MASTERPROMPT.md for the complete source prompt and full requirements.
