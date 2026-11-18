# KeralaFloodBench results

## Accuracy

| QID | Arm | n | Accuracy |
|---|---|---:|---:|
| C01 | noparam | 1 | 1.000 |
| C01 | pack | 1 | 1.000 |
| C02 | noparam | 1 | 0.000 |
| C02 | pack | 1 | 0.000 |
| C03 | noparam | 1 | 1.000 |
| C03 | pack | 1 | 1.000 |
| C04 | noparam | 1 | 0.000 |
| C04 | pack | 1 | 1.000 |
| C05 | noparam | 1 | 0.000 |
| C05 | pack | 1 | 0.000 |
| C06 | noparam | 1 | 0.000 |
| C06 | pack | 1 | 0.000 |
| C07 | noparam | 1 | 0.000 |
| C07 | pack | 1 | 0.000 |
| C08 | noparam | 1 | 1.000 |
| C08 | pack | 1 | 1.000 |
| P01 | inline | 1 | 0.000 |
| P01 | noparam | 1 | 0.000 |
| P01 | pack | 1 | 0.000 |
| P02 | inline | 1 | 0.000 |
| P02 | noparam | 1 | 0.000 |
| P02 | pack | 1 | 0.000 |
| P03 | inline | 1 | 0.000 |
| P03 | noparam | 1 | 0.000 |
| P03 | pack | 1 | 0.000 |
| P04 | inline | 1 | 0.000 |
| P04 | noparam | 1 | 0.000 |
| P04 | pack | 1 | 0.000 |
| P05 | inline | 1 | 0.000 |
| P05 | noparam | 1 | 0.000 |
| P05 | pack | 1 | 0.000 |
| P06 | inline | 1 | 0.000 |
| P06 | noparam | 1 | 0.000 |
| P06 | pack | 1 | 0.000 |
| P07 | inline | 1 | 1.000 |
| P07 | noparam | 1 | 0.000 |
| P07 | pack | 1 | 0.000 |
| P08 | inline | 1 | 0.000 |
| P08 | noparam | 1 | 1.000 |
| P08 | pack | 1 | 1.000 |
| P09 | inline | 1 | 0.000 |
| P09 | noparam | 1 | 0.000 |
| P09 | pack | 1 | 0.000 |
| P10 | inline | 1 | 0.000 |
| P10 | noparam | 1 | 1.000 |
| P10 | pack | 1 | 1.000 |
| P11 | inline | 1 | 0.000 |
| P11 | noparam | 1 | 0.000 |
| P11 | pack | 1 | 0.000 |
| P12 | inline | 1 | 0.000 |
| P12 | noparam | 1 | 0.000 |
| P12 | pack | 1 | 0.000 |

## Paired comparisons

| Comparison | Both right | Only left | Only right | Both wrong | Descriptive sign-test p |
|---|---:|---:|---:|---:|---:|
| A3 vs A2 | 0 | 2 | 1 | 9 | 1.00000 |
| A2 vs A1 | 0 | 1 | 2 | 9 | 1.00000 |
| A3 vs A1 controls | 3 | 1 | 0 | 4 | 1.00000 |

## Cost per correct answer

| Model | Arm | Runs | Correct | Minutes | Tokens | Minutes per correct | Tokens per correct |
|---|---|---:|---:|---:|---:|---:|---:|
| pc-gptoss20b | inline | 12 | 1 | 45.07 | 1024083 | 45.07 | 1024083 |
| pc-gptoss20b | noparam | 20 | 5 | 69.72 | 1546506 | 13.94 | 309301 |
| pc-gptoss20b | pack | 20 | 6 | 67.73 | 1426057 | 11.29 | 237676 |

## First attempt vs final (AnswerChecker effect), by arm

| Arm | Runs | Correct first attempt | Correct final | Format OK | A3 runs with zero pack calls |
|---|---:|---:|---:|---:|---:|
| inline | 12 | 0 | 1 | 8 | n/a |
| noparam | 20 | 3 | 5 | 9 | n/a |
| pack | 20 | 3 | 6 | 9 | 8 |

## Failure taxonomy (automatic), by arm

| Label | inline | noparam | pack |
|---|---:|---:|---:|
| FORMAT | 4 | 11 | 11 |
| LOGIC | 1 | 0 | 1 |
| TOOL_BUG | 6 | 4 | 1 |
| UNANSWERABLE_ANSWERED | 0 | 0 | 1 |

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
