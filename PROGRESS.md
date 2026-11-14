# PROGRESS
## Status: Phase 0 — in progress
## Checklist
- [ ] Phase 0
  - [x] 0.1 git init + .gitignore + upstream snapshot commit
  - [x] 0.2 save prompt verbatim and split Part B into phase files
  - [x] 0.3 write AGENTS.md
  - [x] 0.4 write PROGRESS.md phase checklist
  - [x] 0.5 create small Kerala files
  - [x] 0.6 build venv in background
  - [x] 0.7 run baseline tests
  - [ ] 0.8 set up Ollama and confirm 16K context
  - [ ] 0.9 measure default and CPU-only timing
- [ ] Phase 1 — F1–F5 and regression tests
  - [ ] Implement F1–F5
  - [ ] Run targeted and full baseline tests
- [ ] Phase 2 — data preparation
  - [ ] Area of interest and district boundaries
  - [ ] Taluk boundaries and verification
  - [ ] Target grid
  - [ ] Vector and raster layers
  - [ ] Reference flood and Otsu threshold
  - [ ] Manifest and cache outputs
  - [ ] Optional NASA cross-check
  - [ ] Lock layers and acceptance check
- [ ] Phase 3 — pack, AnswerChecker, agent, prompt
  - [ ] Pack schema and tool
  - [ ] KeralaAgent and AnswerChecker
  - [ ] Prompt construction and task composition
  - [ ] Offline tests
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
- Baseline: 9 passed, 5 failed; failures: test_local_probe_add_test_run, test_run_to_completion, test_cancel_busy_and_rejoin, test_toolbox_is_recorded, test_settings_mask_keys.
- Ollama context: pending
- Timing: pending (Vulkan/default and CPU-only)
- Peak RAM/backend: pending
- Kerala threshold, flood areas, taluks, gold table, smoke results: pending
## Decisions made (with reason)
- Git is installed (2.51.0.windows.1), so no installation was needed.
- uv and Ollama are already installed. The Ollama server was not running at inspection.
## Needs Kirito
- None yet.
## Last acceptance output
Command: .\.venv\Scripts\python.exe -m pytest -q tests --ignore=tests\test_ui.py
Last 15 lines:
    E         - 0o600
    E         + 0o666

tests\test_smoke.py:142: AssertionError
---------------------------- Captured stderr call -----------------------------
2026-11-14 12:11:11,041 [INFO] stored API key for openai (sk-ab…1234)
------------------------------ Captured log call -----------------------------
INFO     gisclaw:server.py:176 stored API key for openai (sk-ab…1234)
=========================== short test summary info ===========================
FAILED tests/test_local.py::test_local_probe_add_test_run - assert (False is ...
FAILED tests/test_smoke.py::test_run_to_completion - AssertionError: assert (...
FAILED tests/test_smoke.py::test_cancel_busy_and_rejoin - assert (None)
FAILED tests/test_smoke.py::test_toolbox_is_recorded - assert (False)
FAILED tests/test_smoke.py::test_settings_mask_keys - AssertionError: assert ...
5 failed, 9 passed in 31.58s
