# Floor-check diagnostics

| Model | QID / arm | exit_reason | format_ok | correct_final | correct_given_own_params | value vs gold | parameters_used | first error |
|---|---|---|---:|---:|---:|---|---|---|
| cloud-flashlite | P01 / inline | finished | yes | no | no | 96 vs 93 | {"facility_point_rule": "representative_point geometry rule", "facility_flood_buffer_m": 250} | r6 `execute`: ❌ Execution failed |
| cloud-flashlite | P01 / noparam | finished | yes | no | no | 2 vs 93 | {"facility_point_rule": "intersect", "facility_flood_buffer_m": 0.0} | r5 `execute`: ❌ Tool 'execute' argument error: GISToolkit.execute_code() missing 1 required positional argument: 'code' |
| cloud-flashlite | P01 / pack | finished | yes | no | no | 96 vs 93 | {"facility_point_rule": "representative_point", "facility_flood_buffer_m": 250} | r7 `execute`: ❌ Execution failed |
| cloud-flashlite | P06 / inline | finished | yes | yes | no | 57.25 vs 57.6 | {"water_threshold_vv_db": -14.0, "permanent_water_rule": "jrc_seasonality >= 10", "max_flood_slope_deg": 5.0, "raster_area_rule": "pixel_count * 900 m2, pixel centre inside zone area rule"} | r6 `geoprocess`: ❌ Tool 'geoprocess' argument error: GISToolkit.geoprocess() missing 1 required positional argument: 'op' |
| cloud-flashlite | P06 / noparam | finished | yes | no | no | 28.52 vs 57.6 | {"water_threshold_vv_db": -14.0, "permanent_water_rule": "jrc_seasonality > 0", "max_flood_slope_deg": 10, "raster_area_rule": "pixel_count * 900 m2"} | r8 `execute`: ❌ Execution failed |
| cloud-flashlite | P06 / pack | max_rounds | no | no | no | — vs 57.6 | — | r5 `execute`: ❌ Execution failed |
| pc-qwen35-9b | P01 / inline | finished | yes | no | no | 96 vs 93 | {"facility_point_rule": "representative_point", "facility_flood_buffer_m": 250} | r12 `execute`: ❌ Execution failed |
| pc-qwen35-9b | P01 / noparam | finished | yes | no | no | 161 vs 93 | {"facility_point_rule": "buffer", "facility_flood_buffer_m": 500} | r8 `execute`: ❌ Execution failed |
| pc-qwen35-9b | P01 / pack | finished | yes | no | no | 0 vs 93 | {"facility_point_rule": "representative_point", "facility_flood_buffer_m": 250} | r7 `execute`: ❌ Execution failed |
| pc-qwen35-9b | P06 / inline | finished | no | no | no | — vs 57.6 | — | r6 `geoprocess`: ❌ geoprocess 'select' is missing a required input/param: 'layer'. Expected: expression |
| pc-qwen35-9b | P06 / noparam | max_rounds | no | no | no | — vs 57.6 | — | r10 `execute`: ❌ Execution failed |
| pc-qwen35-9b | P06 / pack | finished | no | no | no | — vs 57.6 | — | r12 `execute`: ❌ Execution failed |
| pc-gptoss20b | P01 / inline | finished | no | no | no | — vs 93 | — | r2 `Args`: ❌ Unknown tool 'Args'. Available tools: list_files, load_vector, load_raster, geoprocess, execute, inspect, fi |
| pc-gptoss20b | P01 / noparam | finished | no | no | no | — vs 93 | — | r2 `Args`: ❌ Unknown tool 'Args'. Available tools: list_files, load_vector, load_raster, geoprocess, execute, inspect, fi |
| pc-gptoss20b | P01 / pack | finished | no | no | no | — vs 93 | — | r1 `Args`: ❌ Unknown tool 'Args'. Available tools: list_files, load_vector, load_raster, geoprocess, execute, inspect, fi |
| pc-gptoss20b | P06 / inline | finished | no | no | no | — vs 57.6 | — | r1 `Args`: ❌ Unknown tool 'Args'. Available tools: list_files, load_vector, load_raster, geoprocess, execute, inspect, fi |
| pc-gptoss20b | P06 / noparam | finished | no | no | no | — vs 57.6 | — | r1 `Args`: ❌ Unknown tool 'Args'. Available tools: list_files, load_vector, load_raster, geoprocess, execute, inspect, fi |
| pc-gptoss20b | P06 / pack | finished | no | no | no | — vs 57.6 | — | r1 `Args`: ❌ Unknown tool 'Args'. Available tools: list_files, load_vector, load_raster, geoprocess, execute, inspect, fi |

## P01 gold under alternative facility rules (independent gold function)

| facility_point_rule | buffer m | P01 count |
|---|---:|---:|
| representative_point | 250 | 93 |
| representative_point | 500 | 158 |
| centroid | 250 | 93 |
| centroid | 500 | 158 |
| intersects | 250 | 96 |
| intersects | 500 | 161 |
