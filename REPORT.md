# KeralaFloodBench report notes

Phase 6 report drafting has not started. Preserve the following implementation note for the final report.

## Upstream issue F6: dataset path mismatch

GISclaw's `app.runner.DATA_BLOCK` describes the layer listing as complete for `data/`, and `app.data_profile` lists bare layer names. The GIS ReAct agent exposes the same layers in its work directory under `dataset/<name>`. This mismatch led the model to request paths such as `districts.gpkg` instead of `dataset/districts.gpkg`.

Kerala's local mitigation prefixes every layer path in the data profile with `dataset/` and places shared path instructions in the answer contract for all three arms. The contract directs inputs to `dataset/`, outputs to `pred_results/`, and shows a three-line `execute` example that writes `pred_results/answer.json` using `json.dump`. This remains a documented upstream product issue (F6); no upstream `app/` or `src/` code was changed.

The exact P01/noparam system prompt and task used for the approved rerun are preserved at `results/_profile/example_prompt_P01_noparam.txt`. It was rendered before the model batch and confirmed to contain the `dataset/` paths.
