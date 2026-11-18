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


import geopandas as gpd
import rasterio
import numpy as np
import json
import os

# Load vector layers
districts = gpd.read_file("dataset/districts.gpkg")
flood = gpd.read_file("dataset/flood_extent_20180821.gpkg")
dem = rasterio.open("dataset/dem_cop30.tif")

# Ensure same CRS
if districts.crs != dem.crs:
    districts = districts.to_crs(dem.crs)
if flood.crs != dem.crs:
    flood = flood.to_crs(dem.crs)

# Select Alappuzha district
alappuzha = districts[districts['name'] == 'Alappuzha'].iloc[0]
alappuzha_geom = alappuzha.geometry

# Clip flood extent to Alappuzha
flood_in_alappuzha = flood.intersection(alappuzha_geom)

# Rasterize the clipped flood geometry
from rasterio.features import rasterize
mask = rasterize(
    [(flood_in_alappuzha, 1)],
    out_shape=dem.shape,
    transform=dem.transform,
    fill=0,
    dtype='uint8'
)

# Low-lying mask from DEM
low_lying = dem.read(1) <= 10  # low_lying_max_elevation_m = 10
low_lying = low_lying.astype('uint8')

# Combine masks: flood AND low-lying
combined = (mask == 1) & (low_lying == 1)

# Get pixel area from raster_area_rule (assume 30m x 30m = 900 m^2)
pixel_area_m2 = 30 * 30
area_km2 = combined.sum() * pixel_area_m2 / 1e6

# Prepare answer dict
answer = {
    "question_id": "P08",
    "status": "ok",
    "value": round(area_km2, 3),
    "unit": "km2",
    "parameters_used": {"low_lying_max_elevation_m": 10, "raster_area_rule": "30m x 30m"},
    "assumptions": "DEM elevation threshold of 10 m defines low‑lying land.",
    "method": "Rasterized flood extent intersected with low‑lying DEM pixels; pixel area 900 m²."
}

# Write answer
os.makedirs("pred_results", exist_ok=True)
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)

print("Area km2:", area_km2)


import geopandas as gpd
import rasterio
import numpy as np
import json, os
from rasterio.features import rasterize

districts = gpd.read_file("dataset/districts.gpkg")
flood = gpd.read_file("dataset/flood_extent_20180821.gpkg")
dem = rasterio.open("dataset/dem_cop30.tif")

if districts.crs != dem.crs:
    districts = districts.to_crs(dem.crs)
if flood.crs != dem.crs:
    flood = flood.to_crs(dem.crs)

alappuzha = districts[districts['name'] == 'Alappuzha'].iloc[0]
alapp_geom = alappuzha.geometry

flood_in_alapp = flood.intersection(alapp_geom)

# get geometry
geom = flood_in_alapp.geometry[0]
mask = rasterize([(geom,1)], out_shape=dem.shape, transform=dem.transform, fill=0, dtype='uint8')

low_lying = dem.read(1) <= 10
low_lying = low_lying.astype('uint8')
combined = (mask==1) & (low_lying==1)
pixel_area_m2 = 30*30
area_km2 = combined.sum()*pixel_area_m2/1e6
print(area_km2)


import os
print(os.listdir('pred_results'))

import geopandas as gpd
import rasterio
import numpy as np
import json, os
from rasterio.features import rasterize

# Load data
districts = gpd.read_file("dataset/districts.gpkg")
flood = gpd.read_file("dataset/flood_extent_20180821.gpkg")
dem = rasterio.open("dataset/dem_cop30.tif")

# Ensure same CRS (DEM is EPSG:32643)
if districts.crs != dem.crs:
    districts = districts.to_crs(dem.crs)
if flood.crs != dem.crs:
    flood = flood.to_crs(dem.crs)

# Select Alappuzha district
alapp = districts[districts['name'] == 'Alappuzha'].iloc[0]
alapp_geom = alapp.geometry

# Clip flood extent to Alappuzha
flood_in_alapp = flood.intersection(alapp_geom)
# The result may be a MultiPolygon; get geometry list
geoms = flood_in_alapp.geometry.values

# Rasterize the clipped flood geometry
mask = rasterize(
    [(geom, 1) for geom in geoms],
    out_shape=dem.shape,
    transform=dem.transform,
    fill=0,
    dtype='uint8'
)

# Low‑lying mask from DEM (≤10 m)
low_lying = dem.read(1) <= 10
low_lying = low_lying.astype('uint8')

# Combine masks: flood AND low‑lying
combined = (mask == 1) & (low_lying == 1)

# Compute area in km²
pixel_area_m2 = 30 * 30
area_km2 = combined.sum() * pixel_area_m2 / 1e6

# Prepare answer dict
answer = {
    "question_id": "P08",
    "status": "ok",
    "value": round(float(area_km2), 3),
    "unit": "km2",
    "parameters_used": {"low_lying_max_elevation_m": 10, "raster_area_rule": "30m x 30m"},
    "assumptions": "DEM elevation threshold of 10 m defines low‑lying land.",
    "method": "Rasterized flood extent intersected with low‑lying DEM pixels; pixel area 900 m²."
}

# Write answer
os.makedirs("pred_results", exist_ok=True)
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)

print("Area km2:", area_km2)


import os
os.makedirs('pred_results', exist_ok=True)
_saved = []
# current matplotlib figure
try:
    import matplotlib.pyplot as plt
    if plt.get_fignums():
        plt.savefig('pred_results/emergency_plot.png', dpi=150, bbox_inches='tight')
        _saved.append('emergency_plot.png')
except: pass
# largest GeoDataFrame
try:
    import geopandas as _gpd
    _gdf_candidates = []
    for _n, _v in list(globals().items()):
        if isinstance(_v, _gpd.GeoDataFrame) and len(_v) > 0 and not _n.startswith('_'):
            _gdf_candidates.append((_n, _v))
    if _gdf_candidates:
        _name, _gdf = max(_gdf_candidates, key=lambda x: len(x[1]))
        _gdf.to_file('pred_results/emergency_output.geojson', driver='GeoJSON')
        _saved.append(f'{_name}.geojson')
except: pass
# largest DataFrame
try:
    import pandas as _pd
    _df_candidates = []
    for _n, _v in list(globals().items()):
        if isinstance(_v, _pd.DataFrame) and not isinstance(_v, _gpd.GeoDataFrame) and len(_v) > 0 and not _n.startswith('_'):
            _df_candidates.append((_n, _v))
    if _df_candidates:
        _name, _df = max(_df_candidates, key=lambda x: len(x[1]))
        _df.to_csv('pred_results/emergency_output.csv', index=False)
        _saved.append(f'{_name}.csv')
except: pass
print(f'Emergency save: {_saved}')
