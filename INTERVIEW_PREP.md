# Interview prep: KeralaFloodBench

Plain-language explanations you should be able to give without notes. Numbers are from this repo's own results (`results/summary/`, `PROGRESS.md`).

## The 30-second pitch

"I built an AI agent that answers questions about the 2018 Kerala floods by writing and running real GIS code on satellite radar, elevation and OpenStreetMap data, and checking its own answers. Around it I built a frozen 20-question benchmark with independently computed gold answers, to test one question: when a small model fails at GIS, is it missing expert parameters (like the radar water threshold), or is it failing to execute the GIS? I compared three ways of giving it the parameters. Along the way I found and fixed eight real integration and correctness bugs, including two in the open-source agent I built on."

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

## The P01 story (practise this one)

- **P01:** "How many mapped hospitals in Alappuzha district were flood-affected (within the facility flood buffer of the flood extent)?" Gold = **93**, using each hospital's representative point and a 250 m buffer.
- In the floor check, **no model ever produced 93.** Two different models (Gemini and Qwen 3.5) returned **exactly 96** three times, and Qwen once returned exactly **161**.
- I recomputed the independent gold under other rules: whole-polygon `intersects` at 250 m = **96**, and `intersects` at 500 m = **161**. So those "wrong" answers were exactly right for a *different rule*: the models tested whole hospital polygons and ignored the representative-point rule, **even when the rule was written into the question** (inline) or returned by the tool (pack).
- That turns a vague "the model got it wrong" into a precise diagnosis: **parameter ignored**, not "can't do GIS". In the matrix analysis I label such runs `PARAM_IGNORED` (rule given, A2/A3) or `PARAM_CHOICE` (A1 chose it), counted by arm in `REPORT.md`.
- Why it matters: it shows the benchmark can tell *method* errors from *execution* errors, which is the whole research question.

## The local-beats-cloud floor result

- Before running the full matrix, every model had to pass a **floor check**: P01 + P06 in all three arms, at least 2 of 6 correct. The questions were fixed in advance and never changed afterwards.
- Results: **gpt-oss:20b (local, on an 8 GB laptop GPU) 2/6**, **Gemini 3.5 Flash-Lite (cloud) 1/6**, Qwen 3.5 9B 0/6, Qwen2.5-Coder 7B 0/6.
- So a free local model edged out a free cloud model on this task, but only **after** the F8 integration fix. Before the fix, gpt-oss scored 0/6 for reasons unrelated to GIS.
- Be honest about how thin this is: 2/6 vs 1/6 is one question's difference. gpt-oss is not repeatable here (the same cell gave three different outcomes across three runs), and the pass relied on a re-run that I had pre-specified in writing before seeing the result. Say "it cleared the bar and Gemini didn't", not "local is better than cloud".
- The pre-written re-run rule: fix *integration* problems (server errors, replies lost before the parser), never patch *model* behaviour; re-run only the cells a fix touches; if it still fails, accept "nothing passes".
