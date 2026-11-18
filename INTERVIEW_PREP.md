# Interview prep: KeralaFloodBench

Plain-language explanations you should be able to give without notes. Every number here comes from the repo:
- `results/summary/matrix_gptoss_v1/` (`results_tables.md`, `findings_r1.md`, `failure_report.md`, `p01_alt_grid.md`);
- `results/summary/floor_diagnostics.md`;
- the frozen gold files.

`results/summary/number_check.md` lists the source of each number. The main results are from **repeat 1** (`matrix_gptoss_v1`, 52 runs) of gpt-oss:20b.

## The 30-second pitch

"I built an AI agent that answers questions about the 2018 Kerala floods by writing and running real GIS code on satellite radar, elevation and OpenStreetMap data, and it checks its own answers. Around it I built a frozen benchmark with independently computed gold answers, to test one question: when a small model fails at GIS, is it missing expert parameters, or is it failing to execute the GIS? I compared three ways of giving it the parameters. On the 52-run study the answer was clear. The model, gpt-oss 20B, got 12 right. Almost every failure, 39 of 40, involved a tool call the toolkit rejects, not a bad parameter. Along the way I found and fixed two real bugs in the open-source agent I built on."

## The 2-minute version

1. **Problem.** In GIS, flood questions need expert choices: which radar value counts as water, how close to the flood a hospital must be to count as affected, whether to test a building's footprint or a point inside it. When an LLM agent gets these wrong, you want to know whether it lacked the knowledge or just couldn't do the GIS.
2. **System.** I built on GISclaw, an open-source ReAct agent with a Python sandbox and 28 geoprocessing ops. I added:
   - a Kerala data pipeline: Sentinel-1 radar, Copernicus DEM, JRC surface water and OSM, all on a 30 m UTM grid;
   - an AnswerChecker that rejects implausible answers;
   - a "domain pack" tool that returns sourced expert parameters.
3. **Benchmark.** There are 12 parameter questions and 8 controls. Gold answers come from a separate script that never imports the agent. Everything is frozen by SHA-256 hash. There are three arms: the model chooses the parameters, the parameters are written into the question, or the model looks them up with a tool. A1 is also scored on `correct_given_own_params`: if it chose different but defensible values, I recompute the gold with *its* values.
4. **Model selection.** Each model had to pass a pre-set floor: 2 of 6 on two fixed questions.
   - Qwen 2.5-Coder 7B and Qwen 3.5 9B scored 0. Gemini 3.5 Flash-Lite scored 1.
   - gpt-oss 20B first scored 0, but that was an integration bug I found and fixed (F8). After the fix it scored 2, a borderline pass.
5. **Result.** 12/52 correct: noparam 5/20, inline 1/12, pack 6/20. With one run per cell, those arm gaps are noise; the sign tests give p = 1.0. The real finding is *how* it failed:
   - it treats tools as ops of another tool (`geoprocess op=load_vector`, 39 times);
   - it uses wrong argument names;
   - it calls non-existent tools such as `commentary`;
   - 26 of the 40 failed runs never wrote an answer at all.
6. **Takeaway.** For this model the bottleneck is the tool protocol, not domain knowledge. The next step would be strict native tool schemas, and then re-measuring.

## Core concepts

### SAR backscatter and dB
- Sentinel-1 is a **radar** satellite: it sends microwaves and measures how much comes back (*backscatter*). It works through clouds and at night, which matters in a monsoon flood.
- Calm water acts like a mirror and reflects the pulse away from the satellite, so water looks **dark** (low backscatter). Rough land, buildings and vegetation scatter energy back and look brighter.
- Backscatter spans orders of magnitude, so it is expressed in **decibels**: `dB = 10·log10(linear value)`. In our image, open water sits around −19 dB and land around −5 dB.
- I used **VV** polarisation (vertical send, vertical receive), the standard choice for open-water mapping.

### The threshold (Otsu, Kittler–Illingworth, and the valley we chose)
- To map water you pick a threshold T: pixels darker than T are water.
- **Otsu** picks the T that best separates the histogram into two groups (it maximises the variance *between* the groups). **Kittler–Illingworth** assumes two Gaussian classes and minimises classification error.
- Here both were pulled toward the land mode (Otsu −11.65 dB, KI −12.55 dB), because water is only about 15 % of the pixels and flooded vegetation forms a tail between the two peaks.
- We chose **T = −14.0 dB**, the valley (minimum) between the water and land peaks. **This choice was made after looking at the histogram, so it is post-hoc**, and the report says so, with a ±1 dB sensitivity analysis.

### Why UTM for areas
- Latitude/longitude are angles. A "square degree" has no fixed area, and its size changes with latitude. Computing `.area` on lat/lon data gives meaningless numbers.
- **UTM zone 43N (EPSG:32643)** is a projected coordinate system in metres for Kerala's longitudes, so areas come out in m² and distances in m.
- The AnswerChecker rejects any area below 1 km² with the hint "looks like an area computed in degrees", which catches the most common mistake.

### Representative point vs centroid
- A **centroid** is the geometric centre of a shape. For an L-shaped or crescent-shaped building it can fall *outside* the shape.
- A **representative point** (Shapely's `representative_point()`) is guaranteed to lie *inside* the shape.
- Our convention reduces every hospital/school polygon to its representative point before testing whether it is flood-affected, so each facility counts once and consistently.
- For P01 both give the same answer (93); testing the **whole polygon** (`intersects`) gives 96. That difference is the heart of the P01 story below.

### The three arms, and why every arm sees the parameter names
- **A1 `noparam`**: the model must choose the values itself and report them.
- **A2 `inline`**: the values are written into the question ("use water_threshold_vv_db = −14.0 dB").
- **A3 `pack`**: the model gets a `domain_param(key)` tool that returns value, unit, provenance and rationale from a sourced "domain pack".
- **Every arm sees the parameter *names*.** Otherwise A1 would fail just by not knowing *which* decisions matter, and we would be measuring that instead of whether it can pick good *values*. Giving names to all arms isolates the value question.
- Pre-registered expectation: A2 ≥ A3 on small models (writing the value in is the most direct help; a tool call adds a step that can fail).

### `correct_given_own_params`
- In A1 the model may choose different but **defensible** values, for example a 500 m flood buffer instead of 250 m.
- Rather than mark that as simply wrong, we recompute the gold answer **with the model's own reported parameters** (using the independent `gold.py`). If its answer matches, the model executed the GIS correctly and only its parameter choice differed.
- That is how the study separates "chose different parameters" (PARAM_CHOICE) from "could not execute the GIS".

### The sign test, and why it is only descriptive
- For paired comparisons (same question, arm X vs arm Y), we count questions where only X was right and only Y was right, ignore ties, and ask how surprising that split is if both arms were equally good. That is a binomial (sign) test.
- With 12 parameter questions, most pairs are ties (both wrong), so the test has very little power. We report the p-value but label it **descriptive**: it describes this sample and supports no general claim.

## Engineering fixes (good "tell me about a bug" material)

| Fix | What was wrong | How I found it | Fix |
|---|---|---|---|
| **F1** | GISclaw `count_in_polygon` returned 1 for polygons with **no** points | A 2-polygon test: B should be 0 and came out 1 | A left join keeps a null row per empty polygon and `.size()` counted it; count non-null matches instead |
| **F2** | Slope on a lat/lon DEM gave ~89.95° for a 0.57° ramp | Unit test on a synthetic 1 % ramp | Pixel size was in degrees, elevations in metres; refuse geographic DEMs with a clear message |
| **F3** | Windows crashes on "°" or Malayalam text | Writing `code.py` under cp1252 | Explicit UTF-8 on file writes and reads |
| **F4** | Conversation could exceed the context budget | Trim loop never went below the last 14 entries | Extra trimming stages, never cutting the task header |
| **F5** | Temperature 0 silently became 0.1; no backoff on rate limits | Code reading (`temperature or 0.1`) | `is not None` check; retry loop honouring `Retry-After`; optional seed |
| **F6** | The agent was told data lives in `data/`, but it was at `dataset/` | Agents looked for files that did not exist | Prefix the data listing with `dataset/` in our layer (documented upstream issue, `app/` untouched) |
| **F7** | Runs mislabelled "quota exhausted" | Two local runs, with no API at all, said `paused_quota` | The check searched the whole trace for the text "429", which matched a timing value like `41429.5 ms`. Now quota is detected only from the error *type*, HTTP 429 status, or an explicit `RESOURCE_EXHAUSTED` field, and only if the run *ended* on it |
| **F8** | gpt-oss scored 0/6 with empty replies | Saved the raw API response | gpt-oss answers through **native tool calls**; Ollama put them in `tool_calls` with empty `content`, which the agent ignored. A placeholder then parsed as a tool named `Args`. It also sends code as raw text, which Ollama rejected with HTTP 500. I convert both into the agent's text format |

The lesson to say out loud: **two of my "model failures" were really integration bugs** (F6, F8). Before blaming the model, check what it actually received and returned.

**The two upstream bugs (F1, F2), in one breath each:**
- **F1.** GISclaw's `count_in_polygon` said an empty polygon contained 1 point. A left spatial join keeps one null row per unmatched polygon, and `.size()` counts it. Fix: count non-null matches. Test: two polygons, both points inside A; B must be 0, and it came out 1.
- **F2.** Slope on a lat/lon DEM gave about 89.95° for a 0.57° ramp. The pixel size was in degrees while the heights were in metres. Fix: refuse geographic DEMs with a "reproject first" message.
- Both have patches and a ready PR body in `kerala/upstream/`.

## The P01 story (practise this one)

- **P01** asks: "How many mapped hospitals in Alappuzha district were flood-affected (within the facility flood buffer of the flood extent)?" Gold is **93**: each hospital's representative point, within 250 m of the detected flood.
- **Floor check (other models).** No model ever produced 93.
  - Gemini (inline and pack) and Qwen 3.5 (inline) returned exactly **96**. Qwen 3.5 (noparam) returned exactly **161**.
  - Recomputing the independent gold under other rules gives whole-polygon `intersects` at 250 m = **96** and at 500 m = **161**.
  - So those "wrong" answers were exactly right for a *different, defensible spatial predicate*. The models tested whole hospital polygons instead of a point inside them, even when the rule was written into the question or returned by the tool.
- **Repeat 1 (gpt-oss).** I ran the same check, and it did **not** fit the neat story.
  - Its P01 answers were 82, 2 and 174, so 0 matched an alternative rule exactly. I then built a grid that varies the rule, the buffer and the district filter.
  - **82** is exactly `intersects` at 100 m with the Alappuzha filter skipped. It chose a defensible predicate *and* made an execution error.
  - **174** (pack) fetched "representative_point" from the tool, then joined whole polygons anyway, and also skipped the district filter.
  - **2** (inline) was written without any computation in the trace.
- **Why it matters.** The benchmark can separate *method* errors from *execution* errors. And I report what the data says even when it breaks the story I expected.

## "A local 20B model beat Gemini Flash-Lite on the floor check"

- **The floor:** P01 + P06 in all three arms, at least 2 of 6 correct. The questions were fixed in advance.
- **Scores:** gpt-oss:20b (local, Ollama) **2/6**; Gemini 3.5 Flash-Lite (cloud) **1/6**; Qwen 3.5 9B **0/6**; Qwen2.5-Coder 7B **0/6**. gpt-oss before the F8 fix scored 0/6, which is not a valid measurement.
- **What to say:** "it cleared the bar and Gemini didn't". Don't say "local is better than cloud". It is a one-cell difference, both passes are on P06, and gpt-oss is not repeatable here: the same floor cell gave three different outcomes in three attempts. In repeat 1, P06 was 0/3.
- **The pre-written re-run rule:** fix integration problems (server errors, replies lost before the parser); never patch model behaviour; re-run only the cells a fix touches; if the floor still fails, accept "nothing passes". I wrote it down *before* re-running anything.

## The main finding: tool-protocol confusion

- **39 of 40** incorrect runs contain a call the toolkit rejects before any GIS runs. Excluding NameErrors, it is 36 of 40.
- **Typical calls:**
  - `geoprocess` with `op=load_vector` (39 events) or `op=list_files` (28), although these are separate tools;
  - argument names from one tool passed to another (`path`, `var_name`);
  - calls to `commentary` and `container`, which are channel names from gpt-oss's Harmony format, not tools;
  - `reproject` on a layer it never loaded.
- **Consequence:** wasted rounds. 12 runs hit the 16-round limit, and 26 incorrect runs never wrote `answer.json`.
- **The pack was used.** All 12 pack parameter questions called `domain_param`, and the 8 pack controls made 0 calls, as expected. Retrieving a value didn't mean applying it (P01/pack).
- **Honest caveat:** repeat 1 logged parsed actions, not raw model text. The earlier session's raw-reply check ("13 of 13" unknown-op failures were the model's own native `geoprocess` calls) was made on early runs of the stopped second repeat. I cite it as recorded, as mechanism evidence only.

## Why only one repeat (the honest answer)

"I planned two repeats to measure run-to-run agreement with Cohen's kappa, and the code for it exists. The second repeat was running on a GPU PC I then lost access to. It stopped at 35 of 52 runs. A partial repeat would bias any agreement number toward the questions that happened to run first, so I decided not to use it at all. I report one repeat and treat the arm comparisons as descriptive. The failure modes don't depend on the repeat count: 39 of 40 failures show the same pattern."

## Likely interviewer questions

1. **Your water threshold was chosen after looking at the data. Isn't that cheating?**
   It's post-hoc, and I say so everywhere. Otsu (−11.65 dB) and Kittler–Illingworth (−12.55 dB) were pulled toward the land peak, because water is only about 15 % of pixels and flooded vegetation forms a tail. I took the histogram valley (−14.0 dB) and report ±1 dB sensitivity: P06 gold moves from 51.22 to 64.29 km². Crucially, the threshold sets the *gold*, and every arm is scored against the same gold, so it can't favour one arm.

2. **52 runs, one per cell. Can you claim anything?**
   Not about arm differences. The sign tests have p = 1.0, and the model is not deterministic. I can claim the failure profile: 39 of 40 failures show tool-protocol errors. That pattern is too consistent to be noise.

3. **Your pre-registered expectation was A2 ≥ A3. Did it hold?**
   Not in repeat 1, but only by one cell. On parameter questions the pack was right twice where inline was wrong, and inline once where the pack was wrong. That's a single cell, so I don't call it evidence either way.

4. **How did you validate the gold?**
   - It comes from a separate script that never imports the agent and uses plain GeoPandas, Rasterio and NumPy.
   - It was recomputed twice independently, with sanity statements (for example, Alappuzha's OSM area of 1,417.76 km²).
   - There is a hand-check map for P01, and a review document.
   - Then it was frozen by hash.
   - What I couldn't do: compare against official damage records. The NASA flood-map cross-check URL returned 404.

5. **Why not just use a bigger model?**
   - Budget: the study ran on one consumer GPU (repeat 1 peaked at 7,237 MiB of VRAM), and the cloud model was on a free tier.
   - The question was specifically about *small* models.
   - The finding suggests a bigger model wouldn't be my first move. Fixing the tool interface (strict schemas) would likely help more per unit of compute.

6. **What would you do with more compute?**
   - 3–5 repeats per cell, with kappa.
   - A larger local model and an approved cloud matrix.
   - Re-running after exposing the tools as native schemas, to see whether parameters matter once execution is reliable.

7. **What is `correct_given_own_params` and why do you need it?**
   In the no-parameter arm, the model may pick a defensible but different value, for example a 500 m buffer. I recompute the gold with its values; if it matches, the GIS was right and only the choice differed. Without this, "chose differently" and "can't do GIS" look the same.

8. **Why give every arm the parameter names?**
   So A1 isn't failing just because it doesn't know *which* decisions matter. It isolates whether the model can pick good *values*.

9. **Why UTM and not lat/lon?**
   Areas and distances need metres. A square degree has no fixed area. The AnswerChecker flags areas that look like they were computed in degrees.

10. **Representative point vs centroid?**
    A centroid can fall outside an L-shaped building; a representative point is guaranteed to be inside. For P01 both give 93, while whole-polygon `intersects` gives 96.

11. **Tell me about a bug you found.**
    F8: gpt-oss scored 0/6 with empty replies. I saved the raw API response and found the answer was in `tool_calls`, which the engine ignored. A placeholder was then parsed as a tool called `Args`. After the fix it passed the floor. Lesson: check what the model actually returned before blaming it. (Or use F1/F2 for an upstream bug.)

12. **How do you know the agent can't cheat by reading the answers?**
    It only sees `dataset/` (the layers). Gold, pack values, the manifest and the benchmark folder are outside its sandbox, and a leak test checks this. API keys are stripped from its environment.

13. **What's the AnswerChecker and how is it different from GISclaw's check?**
    GISclaw's output guard catches blank images and empty CSVs. My AnswerChecker checks the answer itself: schema, unit, plausible range, areas that look like degrees. It lets the agent retry. In repeat 1, 3 noparam and 3 pack runs were right on the first attempt; the final counts were 5 and 6.

14. **The Copernicus DEM is a DSM. Does that matter?**
    Yes, for the "low-lying" questions and the slope mask: buildings and trees raise the surface. It's a stated limitation. A DTM variant would be a bench v2 item.

15. **Why did P06 pass the floor but fail in the matrix?**
    Run-to-run variation. On the floor, P06/inline gave three different outcomes in three attempts. In repeat 1, all three P06 runs ran out of rounds or ended without an answer. That's exactly why I don't read anything into a single run.

16. **What does "frozen and hashed" buy you?**
    Nobody, including me, can quietly tweak a gold value or tolerance after seeing results. The test fails if a single byte changes. (Moving the repo through a zip changed line endings, which is why the frozen files get `-text` in `.gitattributes`.)

17. **Why a pack *tool* instead of putting everything in the prompt?**
    Real analysts look parameters up, with provenance. The study tests whether a tool lookup helps as much as inline values. Here all 12 pack parameter runs did call the tool, but retrieving a value didn't guarantee using it.

18. **What would you change first in the system?**
    Expose `load_vector`, `list_files` and the rest as strict native tool schemas, so `geoprocess op=load_vector` can't happen. Then re-measure.
