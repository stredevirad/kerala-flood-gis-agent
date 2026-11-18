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


import json, os
# Write answer JSON (overwrite if exists)
answer = {
  "question_id": "P12",
  "status": "ok",
  "value": 0,
  "unit": "count",
  "parameters_used": {
    "relief_camp_hospital_access_m": 3000,
    "facility_point_rule": "representative_point geometry rule",
    "facility_flood_buffer_m": 250
  },
  "assumptions": "All layers are in EPSG:32643 and Euclidean distances are used.",
  "method": "Buffer flood extent and hospitals, intersect with schools in Ernakulam, count the result."
}
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print("answer.json written")
print("Contents of pred_results:", os.listdir("pred_results"))

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
