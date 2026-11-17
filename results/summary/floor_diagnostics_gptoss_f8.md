# Floor-check diagnostics

| Model | QID / arm | exit_reason | format_ok | correct_final | correct_given_own_params | value vs gold | parameters_used | first error |
|---|---|---|---:|---:|---:|---|---|---|
| pc-gptoss20b | P01 / inline | finished | yes | no | no | 0 vs 93 | {"facility_point_rule": "representative_point", "facility_flood_buffer_m": 250} | r2 `geoprocess`: ❌ Tool 'geoprocess' argument error: GISToolkit.geoprocess() got an unexpected keyword argument 'path' |
| pc-gptoss20b | P01 / noparam | finished | no | no | no | — vs 93 | — | r2 `geoprocess`: ❌ Unknown geoprocess op 'list_files'. Available: add_field, aspect, attribute_join, bounding_box, buffer, cent |
| pc-gptoss20b | P01 / pack | finished | yes | no | no | 86 vs 93 | {"facility_flood_buffer_m": 250, "facility_point_rule": "representative_point"} | r7 `geoprocess`: ❌ Tool 'geoprocess' argument error: GISToolkit.geoprocess() got an unexpected keyword argument 'path' |
| pc-gptoss20b | P06 / inline | finished | yes | yes | no | 57.254 vs 57.6 | {"water_threshold_vv_db": -14.0, "permanent_water_rule": "jrc_seasonality >= 10", "max_flood_slope_deg": 5, "raster_area_rule": "pixel_count * 900 m2"} | r1 `execute`: ❌ Execution failed |
| pc-gptoss20b | P06 / noparam | finished | no | no | no | — vs 57.6 | — | r4 `geoprocess`: ❌ geoprocess 'clip' is missing a required input/param: 'overlay'. Expected: inputs.overlay = mask layer |
| pc-gptoss20b | P06 / pack | finished | yes | yes | no | 57.221 vs 57.6 | {"water_threshold_vv_db": -14.0, "permanent_water_rule": "jrc_seasonality >= 10", "max_flood_slope_deg": 5, "raster_area_rule": "pixel_count * 900 m2, pixel centre inside zone"} | r3 `commentary`: ❌ Unknown tool 'commentary'. Available tools: list_files, load_vector, load_raster, geoprocess, execute, inspe |
