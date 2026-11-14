[Part A: Shared context](../MASTERPROMPT.md#part-a-shared-context-applies-to-every-session)

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
