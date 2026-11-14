# PROGRESS
## Status: Phase 1 — in progress
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
- [ ] Phase 1 — F1–F5 and regression tests
  - [x] F1 polygon count left-join regression
  - [ ] F2 terrain operations reject geographic CRS
  - [ ] F3 Windows UTF-8 file handling
  - [ ] F4 conversation trim respects context budget
  - [ ] F5 OpenAI retries, zero temperature and optional seed
  - [ ] Run targeted fixes tests
  - [ ] Run full baseline suite and compare with Phase 0
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
- Kerala threshold, flood areas, taluks, gold table and benchmark smoke scores: not started in Phase 0.

## Decisions made (with reason)
- Git was already installed (2.51.0.windows.1); no winget installation was needed.
- uv and Ollama were already installed. The venv used Python 3.11.16 and the exact desktop, dev and Kerala requirement files.
- The model pull and Ollama access needed elevation for the user model directory. The agent timing run needed elevation for Windows junction creation.
- Python timing output used PYTHONIOENCODING=utf-8 after GISclaw progress output failed under cp1252.
- Whole-system RAM was sampled because the Ollama model runner shares the Intel Arc system memory; Python-process memory alone is not representative.
- No Phase 0 acceptance item was skipped.

## Needs Kirito
- Phase 0 is at its STOP gate. The smoke task failed to complete on both backends: Vulkan reached the 12-round limit; CPU stopped on repeated-code detection. Review whether to continue with the current planned benchmark after Phase 1–5 validation. The projected local matrix is below 20 hours, so no cut is required by the prompt.
- No gold or benchmark design decisions are pending.

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

Context command:
.\.venv\Scripts\python.exe -c "from app.local_models import loaded_context; print(loaded_context('http://localhost:11434/v1','gisclaw-qwen7b-16k:latest'))"
Output: 16384

Timing commands used:
.\.venv\Scripts\python.exe -m kerala.tools.smoke_run --label vulkan_final --out logs/phase0_timing
.\.venv\Scripts\python.exe -m kerala.tools.smoke_run --label cpu_calls --out logs/phase0_timing
Both timing command summaries are in logs\phase0_timing\<mode>\summary.json; per-call records are in calls.jsonl.

Vulkan timing command:
.\.venv\Scripts\python.exe -m kerala.tools.smoke_run --label vulkan_final --out logs/phase0_timing
Last 15 output lines:
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
Last 15 output lines:
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
