## P01 method analysis (single repeat)

Batch: `matrix_gptoss_v1` only. Run-to-run agreement is not computed (one repeat).

### P01 gold under alternative facility rules

| Rule | Buffer m | P01 count |
|---|---:|---:|
| centroid | 100 | 35 |
| centroid | 250 | 93 |
| intersects | 100 | 43 |
| intersects | 250 | 96 |
| representative_point (gold) | 250 | 93 |

### P01 failed runs matching another facility rule, by arm

| Arm | Failed P01 runs | PARAM_IGNORED | PARAM_CHOICE | No rule match |
|---|---:|---:|---:|---:|
| noparam | 1 | 0 | 0 | 1 |
| inline | 1 | 0 | 0 | 1 |
| pack | 1 | 0 | 0 | 1 |

### P01 failed runs (detail)

| Repeat | Arm | Value | Matches | Label |
|---|---|---:|---|---|
| matrix_gptoss_v1 | inline | 2 | — | — |
| matrix_gptoss_v1 | noparam | 82 | — | — |
| matrix_gptoss_v1 | pack | 174 | — | — |
