# KeralaFloodBench on GISclaw — Claude Code context

KeralaFloodBench is an AI agent that answers plain-English questions about the August 2018 Kerala floods by writing and running real GIS code (GISclaw's ReAct loop, persistent Python sandbox and 28 geo ops) on satellite and map data, checks its own answer (AnswerChecker), and is the subject of a measured study: do small models fail on missing expert parameters or on GIS execution, and does a sourced, tool-retrieved domain pack (arm A3 `pack`) help more than the same values written into the question (A2 `inline`) or none (A1 `noparam`)? Our layer lives in `kerala/`; the benchmark is 20 test questions (P01–P12, C01–C08) plus D01–D03, with independent gold in `kerala/bench/gold.py`. Owner: Kirito (B.Tech AI & DS student, resume project — keep explanations plain). Full handoff: `kerala/HANDOFF_CLAUDE.md` (supersedes `kerala/MASTERPROMPT.md` where they disagree).

@AGENTS.md

## Hard rules (condensed)
1. Never edit frozen files: `kerala/bench/questions.yaml`, `rubric.yaml`, `gold.json`, `frozen.json`, `kerala/pack/kerala_pack.yaml`, `data/kerala/layers/*`. Never change gold values or tolerances, never hard-code answers. Benchmark changes = new "bench v2" only after Kirito's explicit approval.
2. `gold.py` never imports `src.agent`.
3. Upstream edits only in `src/agent/geo_ops.py`, `react_agent.py`, `llm_engine.py`, only for documented fixes with regression tests. Never touch `app/`, `desktop/`, `Dockerfile`, `install.*`.
4. Agent runs see only `data/kerala/layers/` (as `dataset/`). Never expose manifest, `meta/`, `kerala/bench/`, `kerala/pack/`. Leak and frozen tests must pass.
5. Secrets: `kerala/.env` holds `GEMINI_API_KEY` (git-ignored). Never print, log or commit it; check it only by length. `kerala/.env.example` must stay blank.
6. AGPL-3.0-or-later with SPDX headers on new files. Copy nothing from GISclaw's `paper-v2` branch.
7. Honesty: a step is done only when its command passed this session; record command + output tail in `PROGRESS.md`; report failures and skips.
8. Names: GISclaw's `_validate_outputs` = **output guard**; ours = **AnswerChecker**.
9. STOP and wait for Kirito before: any matrix (unless he pre-approved it), any benchmark change, any GitHub push.

## Windows notes
- Python: `.venv/Scripts/python.exe` (Git Bash) or `.\.venv\Scripts\python.exe` (PowerShell). Windows tools (`attrib`, `powercfg`, `taskkill`) via `powershell.exe -NoProfile -Command "…"` from Git Bash.
- Long jobs (pulls, smoke/floor runs, matrix) run in the background, logging to `logs/`; poll logs, don't stream. The matrix is launched detached with `powershell.exe Start-Process` and redirected logs; `kerala.bench.run_bench --resume` continues after any interruption.
- Commit after each completed step (`wip:`, `phase N:`, `fix:`, `diag:`). Save usage: targeted reads, no huge outputs (`kerala/prepare_data.py` is 68 KB).
- Ollama runs as the tray app; check context via `GET http://localhost:11434/api/ps` (expect 16384) and GPU split with `ollama ps`.

## Session protocol
At start: read PROGRESS.md and `git log --oneline -15`; continue from the first unchecked item; never redo committed work unless PROGRESS.md marks it broken.
