[Part A: Shared context](../MASTERPROMPT.md#part-a-shared-context-applies-to-every-session)

## Phase 2: Data preparation (`kerala\prepare_data.py`, resumable; run it in the background)

Sub-steps (each one caches its output and is skipped if already done):

1. **Area of interest.** Geocode the two districts with `osmnx.geocode_to_gdf` using "Ernakulam district, Kerala, India" and "Alappuzha district, Kerala, India". If that fails, fall back to `boundary=administrative`, `admin_level=5`.
2. **Taluks.**
   - Take `admin_level=6` features. Keep Polygon and MultiPolygon only.
   - Keep a taluk only if its representative point lies inside the area of interest.
   - Fields:
     - `name`: OSM `name:en` if present, otherwise `name`;
     - `name_local`;
     - `district`.
   - **VERIFY:**
     - there are about 13 taluks (7 in Ernakulam, 6 in Alappuzha);
     - one of them is named like "Kuttanad";
     - names are ASCII.

   If not, stop under **Needs Kirito**. Do not invent boundaries.
3. **Target grid.** EPSG:32643, 30 m pixels, covering the area-of-interest bounding box snapped to 30 m. Pixels outside the area of interest are nodata.
4. **Write the layers** to `data\kerala\layers\`, using exactly these names:

| File | CRS | Fields and notes |
|---|---|---|
| `districts.gpkg` | EPSG:32643 | `name` |
| `taluks.gpkg` | EPSG:32643 | `name`, `name_local`, `district` |
| `hospitals.geojson` | **EPSG:4326** | `osm_id`, `name`, `geom_kind`. Keep the OSM mix of Points and Polygons, and keep features that intersect the area of interest. |
| `schools.geojson` | **EPSG:4326** | Same as hospitals. |
| `roads_major.gpkg` | EPSG:32643 | `highway`, `name`. LineStrings only. |
| `s1_vv_20180821_db.tif` | EPSG:32643 | float32, NaN nodata. Mosaic the two slices, average-resample in linear units, then convert to dB. |
| `jrc_seasonality.tif` | EPSG:32643 | uint8, nodata 255, nearest-neighbour resampling. |
| `dem_cop30.tif` | EPSG:32643 | float32 metres, bilinear resampling. |
| `flood_extent_20180821.gpkg` | EPSG:32643 | The reference flood, built in sub-step 5. |

   The CRS mix is deliberate: CRS handling is part of what we test.
5. **Reference flood.**
   1. Compute `T_raw` = the Otsu threshold of VV dB over valid pixels inside the area of interest. Use numpy only, with 256 bins over [−30, 5].
   2. Set **T = round(T_raw, 1)** and use the rounded value everywhere from here on.
   3. **VERIFY** that −22 ≤ T ≤ −13. If not, stop.
   4. Water = `VV_dB ≤ T`.
   5. Permanent water = `seasonality ≥ 10`.
   6. Steep = slope > 5°, computed from `dem_cop30.tif` with `np.gradient` at 30 m spacing.
   7. Flood = water AND NOT permanent AND NOT steep, inside the area of interest.
   8. Polygonize the flood mask with `rasterio.features.shapes`, dissolve the result, and write it with the field `source="S1A 2018-08-21 VV Otsu T=<T>"`.
   9. Do not simplify the polygons.
6. **Meta outputs** go in `data\kerala\meta\`:
   - `data_manifest.json`, containing:
     - STAC item IDs, unsigned asset hrefs and acquisition times;
     - the RTC units you found;
     - `T_raw` and `T`;
     - pixel counts and km² for water, permanent water, steep ground and flood, per district;
     - feature counts per layer;
     - the OSM retrieval time;
     - library versions;
     - the SHA-256 of every layer file.
   - `cache\flood_mask_20180821.tif`.
   - `cache\quicklook.png`: VV dB with flood in blue and permanent water in dark blue over the outlines.
7. **Optional cross-check** (time-boxed to 20 minutes).
   - Export a PNG over the same bounding box from the NASA Disasters MapServer: `https://maps.disasters.nasa.gov/ags03/rest/services/Kerala_India_Flood/Sentinel1_20180821_water_extent/MapServer/export`
   - Save it as `meta\cache\nasa_compare.png`, placed next to the quicklook.
   - Skip this step if it fails.
8. **Lock the layers.** Run `attrib +R` on every file in `layers\`.

**Acceptance:** `.\.venv\Scripts\python.exe -m kerala.prepare_data --check` exits 0. It checks:
- the files exist;
- each layer has the right CRS;
- every raster is under 25 million pixels;
- T is within range;
- flood km² is greater than 0 and less than the area of interest;
- the manifest hashes match.

**Report in `PROGRESS.md`:** T, flood km² per district, and the taluk list.
