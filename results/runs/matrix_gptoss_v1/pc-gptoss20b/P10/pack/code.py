import os
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.warp import reproject, calculate_default_transform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon, MultiPolygon, box
from shapely.ops import unary_union
import warnings
warnings.filterwarnings('ignore')
os.makedirs('pred_results', exist_ok=True)


import json, numpy as np, geopandas as gpd, rasterio
from rasterio.features import rasterize
from rasterstats import zonal_stats

# Load DEM
with rasterio.open('dataset/dem_cop30.tif') as dem_src:
    dem_arr = dem_src.read(1)
    dem_crs = dem_src.crs
    dem_aff = dem_src.transform

# Load taluks and flood extent
taluk_gdf = gpd.read_file('dataset/taluks.gpkg')
flood_gdf = gpd.read_file('dataset/flood_extent_20180821.gpkg')

# Reproject to DEM CRS if needed
if taluk_gdf.crs != dem_crs:
    taluk_gdf = taluk_gdf.to_crs(dem_crs)
if flood_gdf.crs != dem_crs:
    flood_gdf = flood_gdf.to_crs(dem_crs)

# Low‑lying mask (≤10 m)
low_mask = (dem_arr <= 10).astype(np.uint8)

# Rasterize flood extent onto DEM grid
flood_mask = rasterize(
    [(geom, 1) for geom in flood_gdf.geometry],
    out_shape=dem_arr.shape,
    transform=dem_aff,
    fill=0,
    dtype=np.uint8
)

# Mask of low‑lying pixels that are also flooded
low_flood_mask = low_mask & flood_mask

# Zonal statistics for low‑lying pixels per taluk
low_stats = zonal_stats(taluk_gdf, low_mask, affine=dem_aff, stats=['count'], nodata=0)
low_flood_stats = zonal_stats(taluk_gdf, low_flood_mask, affine=dem_aff, stats=['count'], nodata=0)

# Attach counts to taluk GeoDataFrame
taluk_gdf['low_cnt'] = [s['count'] for s in low_stats]
taluk_gdf['low_flood_cnt'] = [s['count'] for s in low_flood_stats]

# Convert pixel counts to area (900 m² per pixel)
px_area = 900
taluk_gdf['low_area_km2'] = taluk_gdf['low_cnt'] * px_area / 1e6
taluk_gdf['low_flood_area_km2'] = taluk_gdf['low_flood_cnt'] * px_area / 1e6

# Filter taluks with ≥10 km² low‑lying land
eligible = taluk_gdf[taluk_gdf['low_area_km2'] >= 10]

if eligible.empty:
    answer = {
        'question_id': 'P10',
        'status': 'cannot_answer',
        'value': None,
        'unit': None,
        'parameters_used': {
            'low_lying_max_elevation_m': 10,
            'raster_area_rule': 'pixel_count * 900 m2, pixel centre inside zone'
        },
        'assumptions': 'No taluk has ≥10 km² of low‑lying land.',
        'method': 'Zonal statistics on DEM and flood extent.'
    }
else:
    eligible['share_pct'] = eligible['low_flood_area_km2'] / eligible['low_area_km2'] * 100
    max_row = eligible.loc[eligible['share_pct'].idxmax()]
    answer = {
        'question_id': 'P10',
        'status': 'ok',
        'value': round(max_row['share_pct'], 2),
        'unit': 'percent',
        'parameters_used': {
            'low_lying_max_elevation_m': 10,
            'raster_area_rule': 'pixel_count * 900 m2, pixel centre inside zone'
        },
        'assumptions': 'DEM and flood extent share the same CRS and pixel grid.',
        'method': 'Zonal statistics and percentage calculation.'
    }

# Write the answer JSON
with open('pred_results/answer.json', 'w', encoding='utf-8') as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)


import json, numpy as np, geopandas as gpd, rasterio
from rasterio.features import rasterize
from rasterstats import zonal_stats

# Load DEM
with rasterio.open('dataset/dem_cop30.tif') as dem_src:
    dem_arr = dem_src.read(1)
    dem_crs = dem_src.crs
    dem_aff = dem_src.transform

# Load taluks and flood extent
taluk_gdf = gpd.read_file('dataset/taluks.gpkg')
flood_gdf = gpd.read_file('dataset/flood_extent_20180821.gpkg')

# Reproject to DEM CRS if needed
if taluk_gdf.crs != dem_crs:
    taluk_gdf = taluk_gdf.to_crs(dem_crs)
if flood_gdf.crs != dem_crs:
    flood_gdf = flood_gdf.to_crs(dem_crs)

# Low‑lying mask (≤10 m)
low_mask = (dem_arr <= 10).astype(np.uint8)

# Rasterize flood extent onto DEM grid
flood_mask = rasterize(
    [(geom, 1) for geom in flood_gdf.geometry],
    out_shape=dem_arr.shape,
    transform=dem_aff,
    fill=0,
    dtype=np.uint8
)

# Mask of low‑lying pixels that are also flooded
low_flood_mask = low_mask & flood_mask

# Zonal statistics for low‑lying pixels per taluk
low_stats = zonal_stats(taluk_gdf, low_mask, affine=dem_aff, stats=['count'], nodata=0)
low_flood_stats = zonal_stats(taluk_gdf, low_flood_mask, affine=dem_aff, stats=['count'], nodata=0)

# Attach counts to taluk GeoDataFrame
taluk_gdf['low_cnt'] = [s['count'] for s in low_stats]
taluk_gdf['low_flood_cnt'] = [s['count'] for s in low_flood_stats]

# Convert pixel counts to area (900 m² per pixel)
px_area = 900
taluk_gdf['low_area_km2'] = taluk_gdf['low_cnt'] * px_area / 1e6
taluk_gdf['low_flood_area_km2'] = taluk_gdf['low_flood_cnt'] * px_area / 1e6

# Filter taluks with ≥10 km² low‑lying land
eligible = taluk_gdf[taluk_gdf['low_area_km2'] >= 10]

if eligible.empty:
    answer = {
        'question_id': 'P10',
        'status': 'cannot_answer',
        'value': None,
        'unit': None,
        'parameters_used': {
            'low_lying_max_elevation_m': 10,
            'raster_area_rule': 'pixel_count * 900 m2, pixel centre inside zone'
        },
        'assumptions': 'No taluk has ≥10 km² of low‑lying land.',
        'method': 'Zonal statistics on DEM and flood extent.'
    }
else:
    eligible['share_pct'] = eligible['low_flood_area_km2'] / eligible['low_area_km2'] * 100
    max_row = eligible.loc[eligible['share_pct'].idxmax()]
    answer = {
        'question_id': 'P10',
        'status': 'ok',
        'value': max_row['name'],
        'unit': 'name',
        'parameters_used': {
            'low_lying_max_elevation_m': 10,
            'raster_area_rule': 'pixel_count * 900 m2, pixel centre inside zone'
        },
        'assumptions': 'DEM and flood extent share the same CRS and pixel grid.',
        'method': 'Zonal statistics and percentage calculation.'
    }

# Write the answer JSON
with open('pred_results/answer.json', 'w', encoding='utf-8') as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)


import pandas as pd
eligible.to_csv('pred_results/results.csv', index=False)
print('Saved results.csv')