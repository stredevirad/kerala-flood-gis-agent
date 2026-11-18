# Data licences

The **AGPL-3.0-or-later licence of this repository (see `LICENSE`) covers the code only.** It does not cover the data files listed below. Each data file stays under the licence of its source, and you must follow that licence (including its attribution terms) when you reuse it.

## Kerala project data (`data/kerala/`)

Every raster is single-band, 30 m, EPSG:32643, and clipped to Ernakulam + Alappuzha. The layers were built by `kerala/prepare_data.py`; sources are recorded in `data/kerala/meta/data_manifest.json`.

| File | Source | Licence |
|---|---|---|
| `data/kerala/layers/s1_vv_20180821_db.tif` | Copernicus Sentinel-1 RTC VV backscatter, 21 Aug 2018 (S1A, two slices), accessed via Microsoft Planetary Computer; mosaicked, reprojected, converted to dB | Copernicus free and open data licence. Attribution: "Contains modified Copernicus Sentinel data 2018" |
| `data/kerala/layers/dem_cop30.tif` | Copernicus DEM GLO-30; reprojected and clipped | Copernicus free and open data licence (Copernicus DEM licence). Attribution: "© DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA; all rights reserved" |
| `data/kerala/layers/jrc_seasonality.tif` | JRC Global Surface Water, seasonality layer (Pekel et al. 2016, *Nature* 540, 418–422); reprojected and clipped | CC BY 4.0. Attribution: "Source: EC JRC/Google" with the Pekel et al. 2016 citation |
| `data/kerala/layers/flood_extent_20180821.gpkg` | Derived: VV ≤ −14.0 dB, minus JRC permanent water and slopes > 5° (from the three rasters above) | Derived from Copernicus Sentinel-1, Copernicus DEM GLO-30 and JRC GSW. Carries the attribution terms of all three (Copernicus licence + CC BY 4.0) |
| `data/kerala/meta/cache/flood_mask_20180821.tif` | Derived flood mask (same rule as above) | As above: Copernicus licence + CC BY 4.0, with attribution |
| `data/kerala/layers/districts.gpkg` | OpenStreetMap district boundaries | © OpenStreetMap contributors, **ODbL 1.0** |
| `data/kerala/layers/taluks.gpkg` | OpenStreetMap taluk boundaries | © OpenStreetMap contributors, **ODbL 1.0** |
| `data/kerala/layers/hospitals.geojson` | OpenStreetMap hospitals | © OpenStreetMap contributors, **ODbL 1.0** |
| `data/kerala/layers/schools.geojson` | OpenStreetMap schools | © OpenStreetMap contributors, **ODbL 1.0** |
| `data/kerala/layers/roads_major.gpkg` | OpenStreetMap major roads | © OpenStreetMap contributors, **ODbL 1.0** |

**OSM-derived files.** These are derived databases under the Open Database License 1.0. If you redistribute them or a modified version, keep the attribution "© OpenStreetMap contributors" and the ODbL terms, including share-alike for derived databases. See <https://www.openstreetmap.org/copyright>.

## Data that comes with upstream GISclaw (unchanged)

| File | Source | Licence |
|---|---|---|
| `examples/urban-heat-madison/Temperature.geojson`, `block.geojson` | GeoAnalystBench task 1 (Zhang et al. 2025) | Apache License 2.0. See `examples/urban-heat-madison/README.md` and `LICENSE-Apache-2.0.txt` |
| `app/web/vendor/naturalearth/*.geojson` | Natural Earth 1:110m | Public domain. See `THIRD_PARTY_NOTICES.md` |

## Other files

The run outputs under `results/` (traces, answers, tables, figures) are outputs of this project's code. Where they contain values derived from the data above, the attributions above apply as well.
