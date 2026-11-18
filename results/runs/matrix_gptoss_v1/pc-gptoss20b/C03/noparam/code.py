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


flood = gpd.read_file('dataset/flood_extent_20180821.gpkg')
print(f"Rows: {len(flood)}")
print(f"CRS: {flood.crs}")
print(f"Columns: {list(flood.columns)}")
print()
# Show first 3 rows
print(flood.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in flood.columns if c != 'geometry'][:6]:
    try:
        uniques = flood[col].dropna().unique()
        if len(uniques) <= 10:
            print(f"{col} unique values: {list(uniques)}")
        else:
            print(f"{col}: {len(uniques)} unique values, e.g.: {list(uniques[:5])}")
    except:
        pass


taluks = gpd.read_file('dataset/taluks.gpkg')
print(f"Rows: {len(taluks)}")
print(f"CRS: {taluks.crs}")
print(f"Columns: {list(taluks.columns)}")
print()
# Show first 3 rows
print(taluks.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in taluks.columns if c != 'geometry'][:6]:
    try:
        uniques = taluks[col].dropna().unique()
        if len(uniques) <= 10:
            print(f"{col} unique values: {list(uniques)}")
        else:
            print(f"{col}: {len(uniques)} unique values, e.g.: {list(uniques[:5])}")
    except:
        pass



import os as _os, numpy as _np, geopandas as _gpd, pandas as _pd
_os.makedirs('pred_results', exist_ok=True)
def _disp_write(_g, _name):
    # Write a WGS84 GeoJSON snapshot for auto-render on the map.
    try:
        _d = _g
        if getattr(_d, 'crs', None) is not None:
            _d = _d.to_crs(4326)
        _d.to_file('pred_results/' + _name + '.geojson', driver='GeoJSON')
    except Exception:
        pass
def _summ(_g, _label):
    try:
        _crs = _g.crs.to_epsg() if getattr(_g, 'crs', None) is not None else None
        print(f"OK {_label}: {len(_g)} features, EPSG:{_crs}")
    except Exception:
        print(f"OK {_label}")
_b = taluks.to_crs(flood.crs) if (flood.crs is not None and taluks.crs is not None and flood.crs != taluks.crs) else taluks
flood_taluk = _gpd.overlay(flood, _b, how='intersection')
_disp_write(flood_taluk, 'flood_taluk')
_summ(flood_taluk, 'flood_taluk')
try:
    flood_taluk.to_file('pred_results/flood_taluk.geojson', driver='GeoJSON' if 'pred_results/flood_taluk.geojson'.endswith('.geojson') else None)
    print('saved -> ' + 'pred_results/flood_taluk.geojson')
except Exception as _e:
    print('save failed:', _e)


import geopandas as gpd
# compute area in km2
flood_taluk['area_m2'] = flood_taluk.geometry.area
flood_taluk['area_km2'] = flood_taluk.area_m2/1e6
# aggregate by taluk name
agg = flood_taluk.groupby('name')['area_km2'].sum().reset_index()
max_row = agg.loc[agg.area_km2.idxmax()]
max_row


import json
answer = {
  "question_id": "C03",
  "status": "ok",
  "value": 171.796349,
  "unit": "km2",
  "parameters_used": {},
  "assumptions": "All flood polygons are in the same CRS as taluk polygons, so area calculations are accurate.",
  "method": "Intersected flood extent with taluk polygons, summed area per taluk, and selected the maximum."
}
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print("answer written")

import os
os.makedirs('pred_results', exist_ok=True)
print('Directory created')

import os
print(os.listdir('pred_results'))

import json
answer = {
  "question_id": "C03",
  "status": "ok",
  "value": "Kuttanad",
  "unit": "name",
  "parameters_used": {},
  "assumptions": "All flood polygons are in the same CRS as taluk polygons, so area calculations are accurate.",
  "method": "Intersected flood extent with taluk polygons, summed area per taluk, and selected the maximum."
}
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print("answer updated")

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
