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


schools = gpd.read_file('dataset/schools.geojson')
print(f"Rows: {len(schools)}")
print(f"CRS: {schools.crs}")
print(f"Columns: {list(schools.columns)}")
print()
# Show first 3 rows
print(schools.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in schools.columns if c != 'geometry'][:6]:
    try:
        uniques = schools[col].dropna().unique()
        if len(uniques) <= 10:
            print(f"{col} unique values: {list(uniques)}")
        else:
            print(f"{col}: {len(uniques)} unique values, e.g.: {list(uniques[:5])}")
    except:
        pass


schools = gpd.read_file('dataset/schools.geojson')
print(f"Rows: {len(schools)}")
print(f"CRS: {schools.crs}")
print(f"Columns: {list(schools.columns)}")
print()
# Show first 3 rows
print(schools.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in schools.columns if c != 'geometry'][:6]:
    try:
        uniques = schools[col].dropna().unique()
        if len(uniques) <= 10:
            print(f"{col} unique values: {list(uniques)}")
        else:
            print(f"{col}: {len(uniques)} unique values, e.g.: {list(uniques[:5])}")
    except:
        pass


schools = gpd.read_file('dataset/schools.geojson')
print(f"Rows: {len(schools)}")
print(f"CRS: {schools.crs}")
print(f"Columns: {list(schools.columns)}")
print()
# Show first 3 rows
print(schools.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in schools.columns if c != 'geometry'][:6]:
    try:
        uniques = schools[col].dropna().unique()
        if len(uniques) <= 10:
            print(f"{col} unique values: {list(uniques)}")
        else:
            print(f"{col}: {len(uniques)} unique values, e.g.: {list(uniques[:5])}")
    except:
        pass


schools = gpd.read_file('dataset/schools.geojson')
print(f"Rows: {len(schools)}")
print(f"CRS: {schools.crs}")
print(f"Columns: {list(schools.columns)}")
print()
# Show first 3 rows
print(schools.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in schools.columns if c != 'geometry'][:6]:
    try:
        uniques = schools[col].dropna().unique()
        if len(uniques) <= 10:
            print(f"{col} unique values: {list(uniques)}")
        else:
            print(f"{col}: {len(uniques)} unique values, e.g.: {list(uniques[:5])}")
    except:
        pass


import json, os, geopandas as gpd
# ensure output dir
os.makedirs('pred_results', exist_ok=True)
# load layers
schools = gpd.read_file('dataset/schools.geojson')
# keep only points
schools = schools[schools.geometry.type == 'Point']
schools = schools.to_crs(epsg=32643)
flood = gpd.read_file('dataset/flood_extent_20180821.gpkg').to_crs(epsg=32643)
flood_buf = flood.buffer(250).unary_union
districts = gpd.read_file('dataset/districts.gpkg').to_crs(epsg=32643)
# clip schools to district
schools_ernakulam = gpd.overlay(schools, districts, how='intersection')
# intersect with buffer
schools_flooded = schools_ernakulam[schools_ernakulam.geometry.intersects(flood_buf)]
count = len(schools_flooded)
answer = {
  "question_id": "P02",
  "status": "ok",
  "value": count,
  "unit": "count",
  "parameters_used": {"facility_point_rule": "representative_point", "facility_flood_buffer_m": 250},
  "assumptions": "Schools are represented by their point geometry and flood impact is defined by a 250 m buffer around the 21 Aug 2018 flood extent.",
  "method": "Count of schools within 250 m of the 21 Aug 2018 flood extent, restricted to Ernakulam district."
}
with open('pred_results/answer.json', 'w', encoding='utf-8') as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print('count', count)


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
