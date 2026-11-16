# HANDOFF: KeralaFloodBench on GISclaw (Codex → Claude Code)

You are Claude Code (Opus 5.5, high effort). You are taking over this project from OpenAI Codex, which built it across several sessions. You have full access to this Windows PC.

Read this whole file first. Then follow §6 (session start), and §7 (the next task).

- This handoff file **supersedes** `kerala/MASTERPROMPT.md` wherever they disagree.
- Everything else in the master prompt still applies.

---

## 1. What this project is

**Pitch.** An AI agent that answers plain-English questions about the August 2018 Kerala floods by writing and running real GIS code on satellite and map data. It checks its own answer. Alongside it is a measured study of why models succeed or fail at this.

**The base.** It is built on the open-source agent **GISclaw** (`main`, AGPL-3.0-or-later):
- ReAct loop: `src/agent/react_agent.py`
- persistent Python sandbox
- 28 deterministic geoprocessing ops: `src/agent/geo_ops.py`
- LLM engines: `src/agent/llm_engine.py`

Our own layer lives in `kerala/`.

**Research question.** Do small models fail because they lack expert parameters (radar water threshold, "low-lying", access distance…) or because they cannot execute the GIS? And does a structured, sourced, tool-retrieved **domain pack** help more than writing the same values into the question?

**Three arms**, all of which see the parameter *names* the question depends on:

| Arm | What it gets |
|---|---|
| A1 `noparam` | Must choose and report values itself |
| A2 `inline` | Values written into the task |
| A3 `pack` | A pack section (keys + descriptions, no values) and a `domain_param(key)` tool that returns value, unit, kind, provenance and rationale |

The pre-registered expectation is that A2 ≥ A3 on small models.

**Benchmark:**
- 20 test questions: 12 parameter questions P01–P12 and 8 controls C01–C08 (C07/C08 must answer `cannot_answer`).
- 3 dev questions D01–D03.
- Gold answers come from an independent `kerala/bench/gold.py`.

**Headline deliverables:**
- per-question table;
- paired comparisons;
- `correct_given_own_params` for A1;
- failure taxonomy.

**Owner:** Kirito, a 3rd-year B.Tech AI & DS student. This is a resume project, so he must be able to explain every part in interviews. Keep explanations plain.

## 2. Where things stand (verify all of this; do not trust it blindly)

**Repo location.** This folder is the repo. It was copied from his laptop as `GISclaw_bundle` and has a full `.git` history.
- Run `git log --oneline -20` and `git status` first.
- Some older docs mention `C:\Projects\GISclaw`. Ignore that path; always work relative to the repo root.

**Machine.** This PC:
- NVIDIA RTX 4060 (8 GB VRAM) with CUDA confirmed;
- 24 GB RAM;
- Windows.

Already installed:
- uv 0.13.8;
- Python 3.11.18;
- `.venv` rebuilt;
- Ollama 0.40.16 with `gpt-oss:20b` and `qwen3.5:9b` pulled;
- user env var `OLLAMA_CONTEXT_LENGTH=16384`;
- AC sleep set to Never.

The old laptop is not used any more.

**Phases (from `kerala/MASTERPROMPT.md`):**

| Phase | State | Detail |
|---|---|---|
| 0 Setup + timing | done | |
| 1 Upstream fixes F1–F5 | done | count_in_polygon zero-count; terrain on a geographic CRS; UTF-8; context truncation; engine 429/5xx backoff and temperature 0 |
| 2 Data | done, layers read-only | 9 layers in `data/kerala/layers/`; manifest in `data/kerala/meta/` |
| 3 Pack, AnswerChecker, prompts | done | |
| 4 Questions and gold | **approved and frozen** | `kerala/bench/frozen.json`; test `tests/test_kerala_frozen.py` |
| 5 Runner, scorer, smoke | built (`run_one.py`, `run_bench.py`, `score.py`, `ask.py`) | **Stopped at the floor gate. No matrix has been run.** |
| 6 Report | not started | |

**Decisions made after the master prompt** (all binding):
1. **Water threshold T = −14.0 dB.**
   - It is the histogram valley between the water mode (≈ −19 dB) and the land mode (≈ −5 dB).
   - Otsu (−11.65) and Kittler–Illingworth (−12.55) were rejected because they are biased toward the land mode: water is about 15% of pixels, and there is a flooded-vegetation tail.
   - This choice was made *after* inspecting the histogram, and must be reported as post-hoc, with ±1 dB sensitivity.
2. **Facility layers.** A hospital null-geometry bug (an index-misalignment problem) was fixed. Counts:
   - hospitals: 510 Point + 350 Polygon;
   - schools: 426 + 1,869;
   - roads: 6,075.
3. **Flood buffer.** Added `facility_flood_buffer_m = 250` (project convention, because SAR cannot see water at building footprints).
   - P01, P02, P11 and P12 were reworded to "flood-affected (within the facility flood buffer…)".
   - New gold for those four: 93, 226, 68 and 215.
4. **Reference values** for sanity checks:
   - P07 = 56.24%;
   - P06 = 57.600 km² (64,000 pixels; the 69-pixel gap to the Phase 2 count is explained by AOI-edge slope);
   - C06 = 57.604 km²;
   - C01 = 1,417.76 km².
5. **F6 (upstream GISclaw issue, documented only).**
   - GISclaw's `DATA_BLOCK` says data lives in `data/` and lists bare filenames, but the agent's files are at `dataset/<name>`.
   - Fixed inside `kerala/` only: `dataset/` prefixes in the data listing, plus an answer-contract example.
6. **`max_rounds = 16`** for all real models; this is a pre-matrix change.

**Floor check (the gate in front of the matrix).**
- Questions: P01 + P06 × 3 arms. Rule: at least 2 of 6 must be correct (`correct_final` or `correct_given_own_params`). The question choice must not be changed after the fact.

| Model | Score | What happened |
|---|---|---|
| `qwen2.5-coder:7b` (laptop) | 0/6 | Real GIS failures: wrong geoprocess args (clip without `overlay`, attribute_join without `layer`, unknown `threshold` op); a 300 s timeout from buffering the giant flood MultiPolygon; running out of rounds. Dev questions D01/D02 were correct after the F6 fix. |
| `gpt-oss:20b` (PC) | 0/6 | **Not a valid measurement.** Empty responses and `Args` parser errors point to a response-format / reasoning-field integration failure. |
| `qwen3.5:9b` (PC) | 0/6 | P01 wrote valid answers that were wrong; P06 had GIS and code-format failures. |
| Cloud (Gemini Flash-Lite) | never run | The API key was missing. |

**Known harness bug.** Two runs were mislabelled `paused_quota`, because a `"429"` substring matched inside a numeric `gen_time_ms` field.

The open "Needs Kirito" items are in `PROGRESS.md`, around line 368 and line 400.

## 3. Hard rules (carried over; do not break them)

1. **Never edit frozen files** to make a test or score pass. Frozen files are:
   - `kerala/bench/questions.yaml`, `rubric.yaml`, `gold.json`, `frozen.json`;
   - `kerala/pack/kerala_pack.yaml`;
   - `data/kerala/layers/*`.

   Never edit a gold value or a tolerance, and never hard-code answers. If you believe a gold value or question is wrong, stop and ask Kirito. Any change to the benchmark becomes a new versioned "bench v2" with an honest changelog, and only after his explicit approval.
2. **Gold stays independent:** `gold.py` never imports `src.agent`.
3. **Upstream edits** are allowed only in `src/agent/geo_ops.py`, `react_agent.py` and `llm_engine.py`, and only for documented fixes with regression tests. Never edit `app/`, `desktop/`, `Dockerfile` or `install.*`.
4. **Agent runs see only `data/kerala/layers/`** (linked as `dataset/`).
   - Never expose the manifest, `meta/`, `kerala/bench/` or `kerala/pack/` to the agent.
   - The leak and frozen tests must keep passing.
5. **Secrets.**
   - `kerala/.env` holds `GEMINI_API_KEY`. It is git-ignored.
   - Never print, log or commit it.
   - `run_one.py` strips `*_API_KEY` from the environment before the sandbox starts.
6. **Licence.** Our fork stays AGPL-3.0-or-later, with SPDX headers on new files. Copy nothing from GISclaw's `paper-v2` branch.
7. **Honesty.** A step is done only when its command passed in this session. Record the command and its output tail in `PROGRESS.md`. Report failures and anything skipped.
8. **Keep the two checks' names distinct.** GISclaw's `_validate_outputs` is the **output guard**; ours is the **AnswerChecker**.
9. **STOP gates** (stop and wait for Kirito's explicit reply):
   - after the §7 diagnostics;
   - before starting any matrix;
   - before any benchmark change;
   - before pushing to GitHub.

## 4. Windows and Claude Code working notes

**Shell.** Check which shell your Bash tool uses (Git Bash or PowerShell) and write commands for it.
- Always call Python as `.venv/Scripts/python.exe` (Git Bash) or `.\.venv\Scripts\python.exe` (PowerShell).
- Windows-only tools (`attrib`, `powercfg`, `taskkill`) go through `powershell.exe -NoProfile -Command "…"` or `cmd /c` when you are in Git Bash.

**Long jobs.** Ollama pulls, smoke/floor runs and the matrix:
- Run them as background processes, logging to `logs/`. Poll the logs; don't stream them.
- **The matrix must be launched detached**, with `powershell.exe Start-Process` and redirected logs, so it survives this session ending. `run_bench.py --resume` must be able to continue after any interruption.

**Tracking work.**
- Use your todo list for multi-step work.
- Commit after each completed step: `wip:` for intermediate steps, and `phase N:` / `fix:` / `diag:` for finished ones.

**Saving usage.** Kirito is on a limited Claude plan.
- Don't read huge files in full (e.g. `kerala/prepare_data.py` is 68 KB); use search and targeted reads.
- Don't print large outputs.

**Ollama.**
- The server runs as the tray app.
- Check the loaded context with `GET http://localhost:11434/api/ps` (expect 16384) and the GPU split with `ollama ps`.

## 5. Files to read, in this order

1. This file.
2. `AGENTS.md`: the rules digest Codex maintained.
3. `PROGRESS.md`: the full history. Read the "Needs Kirito" and "Decisions made" sections carefully.
4. `kerala/MASTERPROMPT.md`: the original spec. Skim it; read Part A §A3–A8 and the Phase 5–6 sections closely.
5. `kerala/models.yaml`, `kerala/bench/run_one.py`, `kerala/bench/run_bench.py`, `kerala/agent.py`.
6. Read `src/agent/llm_engine.py` only as needed for §7.

## 6. Session start (do this once now)

1. **Create `CLAUDE.md`** at the repo root, so future Claude Code sessions load the context automatically. It should contain:
   - a one-paragraph project summary;
   - the line `@AGENTS.md` (import);
   - the hard rules from §3, condensed;
   - the Windows notes from §4;
   - the session protocol: "At start: read PROGRESS.md and `git log --oneline -15`; continue from the first unchecked item; never redo committed work unless PROGRESS.md marks it broken."
2. **Save this file** as `kerala/HANDOFF_CLAUDE.md`, then commit both as `chore: Claude Code handoff`.
3. **Verify the environment.**
   - Run the full Kerala test suite, `tests/test_kerala_*.py`; it was 47 passed on this PC.
   - Run the frozen-hash test.
   - Confirm `kerala/.env` exists and contains a `GEMINI_API_KEY=` line. Check this **without printing the value**, for example by testing whether the length is greater than 20.
   - If the file is missing, tell Kirito exactly how to create it, then continue with the local-only steps:
     1. go to https://aistudio.google.com/apikey;
     2. open `kerala/.env.example` in Notepad and paste the key after the `=`;
     3. Save As `.env` with type "All files", in the `kerala` folder.
4. **Add a "Session: Claude Code handoff" entry** to `PROGRESS.md`.

## 7. The next task: fix, diagnose, validate the benchmark (then STOP)

Do these in order.

**1. Fix the `paused_quota` false positive.**
- Classify quota only from the HTTP status code or exception type (`openai.RateLimitError`), or an explicit `RESOURCE_EXHAUSTED` error field.
- Never classify by substring-searching a whole log or trace.
- Add a regression test with `"429"` inside a numeric field.
- Re-label the two affected runs.

**2. Fix the gpt-oss integration.**
1. Send one raw chat call to `gpt-oss:20b` through `OpenAIEngine`. Save the full raw response to `results/_profile/gptoss_raw.json`: content vs reasoning fields, `finish_reason` and token counts.
2. Make reasoning never consume the visible answer:
   - Use the lowest reasoning level Ollama's OpenAI-compatible API accepts for gpt-oss. Check the Ollama docs or the server's behaviour for the exact parameter.
   - Set `max_tokens` = 8192 for this model.
   - Make sure only the final content reaches the ReAct parser.
   - Add a test.
3. Verify with D01 × pack. It must be `format_ok`.
4. Re-run the gpt-oss floor check: P01 + P06 × {noparam, inline, pack}.

**3. Run answer-vs-gold diagnostics** for every floor run that produced a value (Qwen 3.5, gpt-oss, and the 7B if its run folders exist):
- show `value` vs gold and `parameters_used`;
- for P01, say whether each miss came from method choice (facility rule, distance vs buffer, CRS) or from execution.

**4. Check the benchmark is solvable at all, using the cloud model.** This is the decisive test: 0 of 18 local runs have passed, so first confirm that *any* model can solve these questions.
- Using `cloud-flashlite` (Gemini free tier via its OpenAI-compatible endpoint), run D01 × pack, then the same floor check: P01 + P06 × 3 arms.
- Record the exact model ID.
- Respect the requests-per-minute limit in `models.yaml`.

**5. Report and STOP.**
- One table covering every floor run: model, qid, arm, exit_reason, format_ok, correct_final, correct_given_own_params, value vs gold, first error.
- Your recommendation, based on this decision table:

| Outcome | Meaning | Proposed next step |
|---|---|---|
| gpt-oss ≥ 2/6 | It was only the integration | Local matrix on gpt-oss on this PC |
| Only Gemini passes | Benchmark is valid; small local models are below the floor | Three-arm matrix on Gemini as the primary study; the local failures become a "below the floor" report section |
| Nothing passes, values close to gold | Tolerances or definitions are too strict | Propose a bench v2 change for approval |
| Nothing passes, values far off | The task is too hard for this setup | Propose a simplified question set for approval |

## 8. After Kirito approves the next step

**Matrix.**
- Local is 52 runs:
  - P01–P12 × {noparam, inline, pack} = 36;
  - C01–C08 × {noparam, pack} = 16.
- Cloud is the same 52 runs, spread over the daily quota with `--resume`.
- Launch detached (§4) with ETA printing.
- Before each batch, `git commit` and verify the frozen hashes.
- Monitor it, and report when it finishes or pauses for quota.

**Phase 6, as specified in the master prompt:**
- run `score.py`;
- read at least 10 failed traces;
- write `REPORT.md`, `README_KERALA.md` and `INTERVIEW_PREP.md`;
- in `REPORT.md`:
  - add a "Model selection" section covering the 7B/9B/20B floor results and why the primary model was chosen;
  - report T as a post-hoc choice;
  - list F1–F6 and the documented upstream issues;
- extras: `kerala/upstream/F1.patch`, `F2.patch`, `PR_F1_F2.md`, and the trace HTML viewer.

**GitHub (STOP first and ask).**
1. Add a `.gitattributes` marking the frozen files and `data/kerala/layers/*` as `-text`, so line endings can't change their hashes. Then confirm the frozen test still passes.
2. Check that `.venv/`, `logs/`, `kerala/.env` and large `results/runs/**/pred_results` files (over 5 MB) are ignored, and run a secret scan of tracked files.
3. Kirito runs `gh auth login` once himself.
4. Create a **private** repo `kerala-flood-gis-agent` with `gh repo create --private --source . --push`, and report the URL.

## 9. Start now

Do §6, then §7. Stop at the §7 STOP gate with the table and your recommendation.
