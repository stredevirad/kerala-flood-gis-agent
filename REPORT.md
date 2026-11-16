# KeralaFloodBench report notes

Phase 6 report drafting has not started. Preserve the following implementation note for the final report.

## Upstream issue F6: dataset path mismatch

GISclaw's `app.runner.DATA_BLOCK` describes the layer listing as complete for `data/`, and `app.data_profile` lists bare layer names. The GIS ReAct agent exposes the same layers in its work directory under `dataset/<name>`. This mismatch led the model to request paths such as `districts.gpkg` instead of `dataset/districts.gpkg`.

Kerala's local mitigation prefixes every layer path in the data profile with `dataset/` and places shared path instructions in the answer contract for all three arms. The contract directs inputs to `dataset/`, outputs to `pred_results/`, and shows a three-line `execute` example that writes `pred_results/answer.json` using `json.dump`. This remains a documented upstream product issue (F6); no upstream `app/` or `src/` code was changed.

The exact P01/noparam system prompt and task used for the approved rerun are preserved at `results/_profile/example_prompt_P01_noparam.txt`. It was rendered before the model batch and confirmed to contain the `dataset/` paths.

## Model selection

### Qwen2.5-Coder:7B — below the floor

After the Kerala-only prompt correction, the approved local development batch (D01–D03, pack) and unchanged floor batch (P01/P06, all arms) completed on the original `qwen2.5-coder:7b` model. D01 and D02 were correct; D03 failed output format. The six floor cells produced 0/6 `correct_final` and 0/6 `correct_given_own_params`, below the unchanged 2/6 floor, so the matrix was not run. Across the nine runs, first failures included a 300 s `buffer` timeout, `clip` calls missing `overlay`, `attribute_join` calls missing `layer`, an unsupported `threshold` operation, and a `cannot_answer` refusal on answerable P01/inline.

The detailed nine-run table follows.

| QID / arm | exit_reason | format_ok | correct_final | correct_given_own_params | rounds | minutes | First trace error, if failed |
|---|---|---:|---:|---:|---:|---:|---|
| D01 / pack | finished | yes | yes | n/a | 5 | 4.84 | — |
| D02 / pack | finished | yes | yes | n/a | 9 | 5.17 | — |
| D03 / pack | finished | no | no | n/a | 11 | 5.28 | `clip`: missing required `overlay` input |
| P01 / noparam | finished | no | no | no | 12 | 24.60 | `buffer`: exceeded the 300 s limit and was stopped |
| P01 / inline | finished | yes | no | no | 12 | 14.37 | `clip`: missing required `overlay` input |
| P01 / pack | finished | no | no | no | 11 | 10.01 | `clip`: missing required `overlay` input |
| P06 / noparam | finished | no | no | no | 10 | 6.85 | `attribute_join`: missing required `layer` input |
| P06 / inline | max_rounds | no | no | no | 12 | 13.55 | `attribute_join`: missing required `layer` input |
| P06 / pack | finished | no | no | no | 12 | 8.30 | unknown `threshold` operation |

The largest per-call prompt was 8,270 tokens, under the 14,500-token limit. If another pilot is later authorized, a simpler raster-only P05/P08 pair is a candidate for replacing P01/P06; this is a recommendation only, with no gold or rubric changes.

### PC model-selection pilots — both below the floor

The user-authorized selection used the unchanged P01/P06 × three-arm floor and the same 2/6 rule. `pc-gptoss20b` ran first; at 0/6 the script proceeded to `pc-qwen35-9b`, which also scored 0/6. No candidate was selected and no matrix was started. The exact tags, `gpt-oss:20b` and `qwen3.5:9b`, were verified on [Ollama's gpt-oss tag page](https://ollama.com/library/gpt-oss/tags) and [qwen3.5 tag page](https://ollama.com/library/qwen3.5/tags).

The pilot commands were:

```powershell
.\.venv\Scripts\python.exe -m kerala.bench.run_bench --model pc-gptoss20b --batch selection_pc_gptoss20b --questions P01,P06 --arms noparam,inline,pack --resume
.\.venv\Scripts\python.exe -m kerala.bench.run_bench --model pc-qwen35-9b --batch selection_pc_qwen35_9b --questions P01,P06 --arms noparam,inline,pack --resume
```

| Model | QID / arm | exit_reason | format_ok | correct_final | correct_given_own_params | rounds | minutes | tokens/s | Peak RAM (GB) | Peak VRAM (MiB) | First error in trace |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pc-gptoss20b | P01 / noparam | finished | no | no | no | 9 | 10.68 | 15.41 | 18.67 | 6707 | empty response; parsed as unknown tool `Args` |
| pc-gptoss20b | P01 / inline | finished | no | no | no | 6 | 3.95 | 21.85 | 18.46 | 6707 | empty response; parsed as unknown tool `Args` |
| pc-gptoss20b | P01 / pack | finished | no | no | no | 5 | 7.24 | 20.96 | 18.76 | 6707 | empty response; parsed as unknown tool `Args` |
| pc-gptoss20b | P06 / noparam | finished | no | no | no | 6 | 13.14 | 21.25 | 19.28 | 6708 | empty response; parsed as unknown tool `Args` |
| pc-gptoss20b | P06 / inline | finished | no | no | no | 6 | 12.00 | 22.06 | 18.88 | 6708 | empty response; parsed as unknown tool `Args` |
| pc-gptoss20b | P06 / pack | paused_quota* | no | no | no | 5 | 6.70 | 21.91 | 19.10 | 6708 | empty response; parsed as unknown tool `Args` |
| pc-qwen35-9b | P01 / noparam | finished | yes | no | no | 16 | 5.32 | 13.83 | 19.22 | 7004 | first `geopandas.sjoin` execution failed; trace truncates the exception |
| pc-qwen35-9b | P01 / inline | finished | yes | no | no | 16 | 3.32 | 20.71 | 13.46 | 7004 | execution failed after flood/hospital bounds; traceback truncated |
| pc-qwen35-9b | P01 / pack | finished | yes | no | no | 16 | 5.89 | 22.28 | 16.54 | 7004 | failed selecting a joined column; traceback truncates the `KeyError` |
| pc-qwen35-9b | P06 / noparam | max_rounds | no | no | no | 16 | 3.36 | 23.13 | 16.34 | 7005 | `AttributeError`: tuple has no `.minx` |
| pc-qwen35-9b | P06 / inline | finished | no | no | no | 16 | 3.30 | 23.05 | 15.50 | 7004 | `select` missing required `layer` input |
| pc-qwen35-9b | P06 / pack | paused_quota* | no | no | no | 16 | 2.28 | 22.48 | 15.43 | 7005 | malformed `execute` payload; `SyntaxError` |

`pc-gptoss20b` produced no format-valid final answer in any cell. Its trace contains `(empty response from model)` followed by an `Args` action, which the ReAct parser rejects as an unknown tool. The 0/6 result is an adapter/content-format failure on this setup and is not evidence about the model's GIS execution ability.

`pc-qwen35-9b` produced format-valid P01 JSON in all three arms, but each final answer was incorrect. The P01 runs also had GIS execution failures while joining or selecting output columns. All P06 cells were format-invalid: the inline arm passed a `select` operation without the required `layer`, the noparam arm used a tuple as if it had `.minx`, and the pack arm emitted malformed Python.

\* The `paused_quota` labels on P06/pack are false positives from the existing substring check for `429` across serialized trace text. Both runs recorded `error: null` and zero backoff; their local Ollama completion requests returned HTTP 200. The numeric `gen_time_ms` fields contained the substring `429`, which triggered the label. Keep these `exit_reason` values in the table but do not interpret them as external rate limits.

Peak resource use was 19.28 GB system RAM / 6,708 MiB VRAM for `pc-gptoss20b`, and 19.22 GB / 7,005 MiB for `pc-qwen35-9b`. The mean pilot rates were 20.57 and 20.91 output tokens/s, respectively. A simple 52 × mean-run-time extrapolation is 7.76 hours for gpt-oss and 3.39 hours for Qwen 3.5. These are timing-only projections for below-floor candidates, not a selected model or approval to run the matrix.

On the PC, `OLLAMA_CONTEXT_LENGTH=16384` was set as a user environment variable. The server log confirmed CUDA on the RTX 4060; while loaded, `ollama ps` showed 59% CPU / 41% GPU for gpt-oss and 16% CPU / 84% GPU for Qwen 3.5, both at context 16,384. AC sleep is set to Never with `powercfg /change standby-timeout-ac 0`; the original setting was already Never, so that same command restores it.

No matrix command is active because no model passed the floor. Next review: fix and verify the local reasoning/tool-call response path before repeating the same floor, or authorize the previously proposed raster-only P05/P08 floor. Keep gold values and tolerances unchanged.
