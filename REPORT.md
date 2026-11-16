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
