# KeralaFloodBench gold review

This review is generated from `gold.py` and the accepted Phase 2 layers. It is not frozen until Kirito replies `gold approved`.

## Calculation basis

- Default water threshold: -14.0 dB, resolved from the accepted manifest through the pack.
- Flood-rule defaults: seasonality < 10, slope <= 5 degrees.
- Other defaults: low land <= 10 m; hospital access <= 3 km; facility rule = `representative_point`.
- Raster masks use pixel centres (`all_touched=False`) on the 30 m grid. P06 and P07 recompute the VV/JRC/DEM rule from the agent-visible rasters rather than reuse a Phase 2 cache output.

## Full gold table

| ID | Gold value | Status | Tied names |
|---|---:|---|---|
| P01 | 2 count | ok | — |
| P02 | 2 count | ok | — |
| P03 | 8 count | ok | — |
| P04 | Kothamangalam name | ok | Kothamangalam |
| P05 | 402.589800 km2 | ok | — |
| P06 | 57.600000 km2 | ok | — |
| P07 | 56.236341 percent | ok | — |
| P08 | 278.805600 km2 | ok | — |
| P09 | 407 count | ok | — |
| P10 | Kuttanad name | ok | Kuttanad |
| P11 | 3 count | ok | — |
| P12 | 2 count | ok | — |
| C01 | 1417.757234 km2 | ok | — |
| C02 | 2058.921864 km | ok | — |
| C03 | Kuttanad name | ok | Kuttanad |
| C04 | 543 count | ok | — |
| C05 | 1.546613 m | ok | — |
| C06 | 57.604372 km2 | ok | — |
| C07 | cannot_answer (value and unit are null) | cannot_answer | — |
| C08 | cannot_answer (value and unit are null) | cannot_answer | — |
| D01 | 860 count | ok | — |
| D02 | 2919.994700 km2 | ok | — |
| D03 | 278.861230 km2 | ok | — |

## P01

- Gold value: `2 count`; status `ok`; tied names: `none`.
- Steps: Select Alappuzha hospitals using the facility rule, then count those inside the flood polygon.
- Computing code: gold.py:L404-L406, gold.py:L249-L250, gold.py:L241-L246.
- Sanity: PASS — P01 is no greater than the 317 hospitals assigned to Alappuzha.

## P02

- Gold value: `2 count`; status `ok`; tied names: `none`.
- Steps: Select Ernakulam schools using the facility rule, then count those inside the flood polygon.
- Computing code: gold.py:L410-L412, gold.py:L249-L250, gold.py:L241-L246.
- Sanity: PASS — P02 is no greater than the mapped school count.

## P03

- Gold value: `8 count`; status `ok`; tied names: `none`.
- Steps: Select Alappuzha schools and count those farther than the access distance from every hospital.
- Computing code: gold.py:L416-L421, gold.py:L249-L250, gold.py:L299-L329.
- Sanity: PASS — P03 is no greater than the 916 schools assigned to Alappuzha.

## P04

- Gold value: `Kothamangalam name`; status `ok`; tied names: `Kothamangalam`.
- Steps: Repeat the no-nearby-hospital count in every taluk and select the largest count, retaining 1% ties.
- Computing code: gold.py:L425-L433, gold.py:L249-L250, gold.py:L299-L329.
- Sanity: PASS — P04 names a taluk present in taluks.gpkg.

## P05

- Gold value: `402.589800 km2`; status `ok`; tied names: `none`.
- Steps: Mask Alappuzha by pixel centre, count finite VV pixels at or below T, and multiply by 900 m².
- Computing code: gold.py:L437-L440, gold.py:L181-L189.
- Sanity: PASS — P05 is between zero and Alappuzha's planar area.

## P06

- Gold value: `57.600000 km2`; status `ok`; tied names: `none`.
- Steps: Recompute VV water, remove seasonality-permanent water and cells above the slope limit, then count Ernakulam pixels.
- Computing code: gold.py:L444-L449, gold.py:L201-L221, gold.py:L181-L189.
- Sanity: PASS — P06 is between zero and Ernakulam's planar area.

## P07

- Gold value: `56.236341 percent`; status `ok`; tied names: `none`.
- Steps: Use the same raster flood rule in Kuttanad and divide flooded pixels by valid VV pixels in the taluk.
- Computing code: gold.py:L453-L461, gold.py:L201-L221, gold.py:L181-L189.
- Sanity: PASS — P07 is a percentage between zero and 100.

## P08

- Gold value: `278.805600 km2`; status `ok`; tied names: `none`.
- Steps: Count Alappuzha pixel centres that are both inside the flood polygon and at or below the low-land elevation.
- Computing code: gold.py:L465-L469, gold.py:L181-L189.
- Sanity: PASS — P08 is between zero and Alappuzha's planar area.

## P09

- Gold value: `407 count`; status `ok`; tied names: `none`.
- Steps: Apply the facility rule to hospitals and count those at or below the low-land elevation.
- Computing code: gold.py:L473-L477, gold.py:L281-L295.
- Sanity: PASS — P09 is no greater than the mapped hospital count.

## P10

- Gold value: `Kuttanad name`; status `ok`; tied names: `Kuttanad`.
- Steps: For each taluk with at least 10 km² of low land, compare its flooded-low-land share and retain 1% ties.
- Computing code: gold.py:L481-L490, gold.py:L181-L189.
- Sanity: PASS — P10 names a taluk present in taluks.gpkg.

## P11

- Gold value: `3 count`; status `ok`; tied names: `none`.
- Steps: Count hospitals that satisfy Ernakulam membership, flood membership, and low-land membership together.
- Computing code: gold.py:L494-L499, gold.py:L241-L246, gold.py:L281-L295.
- Sanity: PASS — P11 is no greater than the 543 hospitals assigned to Ernakulam.

## P12

- Gold value: `2 count`; status `ok`; tied names: `none`.
- Steps: Select flooded Ernakulam schools and count those with a hospital within the access distance.
- Computing code: gold.py:L503-L508, gold.py:L249-L250, gold.py:L241-L246, gold.py:L299-L329.
- Sanity: PASS — P12 is no greater than P02's flooded Ernakulam-school count.

## C01

- Gold value: `1417.757234 km2`; status `ok`; tied names: `none`.
- Steps: Read the Alappuzha polygon in EPSG:32643 and convert its planar area to km².
- Computing code: gold.py:L512-L513.
- Sanity: PASS — C01 is a positive projected polygon area.

## C02

- Gold value: `2058.921864 km`; status `ok`; tied names: `none`.
- Steps: Clip each major-road line to Ernakulam and sum the clipped metre lengths as km.
- Computing code: gold.py:L517-L520.
- Sanity: PASS — C02 is a positive clipped-road length.

## C03

- Gold value: `Kuttanad name`; status `ok`; tied names: `Kuttanad`.
- Steps: Intersect the flood polygon with every taluk and select the largest planar area, retaining 1% ties.
- Computing code: gold.py:L524-L529.
- Sanity: PASS — C03 names a taluk present in taluks.gpkg.

## C04

- Gold value: `543 count`; status `ok`; tied names: `none`.
- Steps: Reduce hospitals to representative points and count those covered by Ernakulam.
- Computing code: gold.py:L533-L534, gold.py:L241-L246.
- Sanity: PASS — C04 is no greater than the mapped hospital count.

## C05

- Gold value: `1.546613 m`; status `ok`; tied names: `none`.
- Steps: Use a pixel-centre Kuttanad mask and take the mean of finite DEM heights.
- Computing code: gold.py:L538-L543, gold.py:L181-L189.
- Sanity: PASS — C05 lies within the finite DEM range.

## C06

- Gold value: `57.604372 km2`; status `ok`; tied names: `none`.
- Steps: Intersect the flood polygon with Ernakulam and convert its planar area to km².
- Computing code: gold.py:L547-L549.
- Sanity: PASS — C06 is between zero and Ernakulam's planar area.

## C07

- Gold value: `cannot_answer (value and unit are null)`; status `cannot_answer`; tied names: `none`.
- Steps: Return cannot_answer because the available layers contain no hospital-damage record.
- Computing code: gold.py:L553-L554.
- Sanity: PASS — C07 is unavailable from the supplied layers.

## C08

- Gold value: `cannot_answer (value and unit are null)`; status `cannot_answer`; tied names: `none`.
- Steps: Return cannot_answer because the available layers contain no evacuation record.
- Computing code: gold.py:L558-L559.
- Sanity: PASS — C08 is unavailable from the supplied layers.

## D01

- Gold value: `860 count`; status `ok`; tied names: `none`.
- Steps: Count rows in hospitals.geojson.
- Computing code: gold.py:L563-L564.
- Sanity: PASS — D01 equals the hospitals.geojson row count.

## D02

- Gold value: `2919.994700 km2`; status `ok`; tied names: `none`.
- Steps: Read the Ernakulam polygon in EPSG:32643 and convert its planar area to km².
- Computing code: gold.py:L568-L569.
- Sanity: PASS — D02 is a positive projected polygon area.

## D03

- Gold value: `278.861230 km2`; status `ok`; tied names: `none`.
- Steps: Intersect the flood polygon with Alappuzha and convert its planar area to km².
- Computing code: gold.py:L573-L575.
- Sanity: PASS — D03 is between zero and Alappuzha's planar area.
