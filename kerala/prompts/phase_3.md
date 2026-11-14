[Part A: Shared context](../MASTERPROMPT.md#part-a-shared-context-applies-to-every-session)

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
