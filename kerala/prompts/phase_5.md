[Part A: Shared context](../MASTERPROMPT.md#part-a-shared-context-applies-to-every-session)

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
