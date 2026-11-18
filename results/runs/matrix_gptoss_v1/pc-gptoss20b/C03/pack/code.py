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


flood_extent = gpd.read_file('dataset/flood_extent_20180821.gpkg')
print(f"Rows: {len(flood_extent)}")
print(f"CRS: {flood_extent.crs}")
print(f"Columns: {list(flood_extent.columns)}")
print()
# Show first 3 rows
print(flood_extent.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in flood_extent.columns if c != 'geometry'][:6]:
    try:
        uniques = flood_extent[col].dropna().unique()
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
_b = taluks.to_crs(flood_extent.crs) if (flood_extent.crs is not None and taluks.crs is not None and flood_extent.crs != taluks.crs) else taluks
flood_taluk_intersect = _gpd.overlay(flood_extent, _b, how='intersection')
_disp_write(flood_taluk_intersect, 'flood_taluk_intersect')
_summ(flood_taluk_intersect, 'flood_taluk_intersect')
try:
    flood_taluk_intersect.to_file('pred_results/flood_taluk_intersect.geojson', driver='GeoJSON' if 'pred_results/flood_taluk_intersect.geojson'.endswith('.geojson') else None)
    print('saved -> ' + 'pred_results/flood_taluk_intersect.geojson')
except Exception as _e:
    print('save failed:', _e)



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
flood_taluk_intersect_area = flood_taluk_intersect.copy()
flood_taluk_intersect_area['area_sqm'] = flood_taluk_intersect_area.eval('geometry.area')
_disp_write(flood_taluk_intersect_area, 'flood_taluk_intersect_area')
_summ(flood_taluk_intersect_area, 'flood_taluk_intersect_area')
try:
    flood_taluk_intersect_area.to_file('pred_results/flood_taluk_intersect_area.geojson', driver='GeoJSON' if 'pred_results/flood_taluk_intersect_area.geojson'.endswith('.geojson') else None)
    print('saved -> ' + 'pred_results/flood_taluk_intersect_area.geojson')
except Exception as _e:
    print('save failed:', _e)


import pandas as pd, json
# aggregate area by taluk
area_by_taluk = flood_taluk_intersect_area.groupby('name')['area_sqm'].sum().reset_index()
# find max
max_row = area_by_taluk.loc[area_by_taluk['area_sqm'].idxmax()]
# prepare answer dict
answer = {
    "question_id": "C03",
    "status": "ok",
    "value": round(max_row['area_sqm']/1e6, 3),
    "unit": "km2",
    "parameters_used": {},
    "assumptions": "All flooded polygons are in the same CRS as taluks, so area is accurate.",
    "method": "Intersect flood extent with taluks, compute area, aggregate, and select maximum."
}
# write JSON
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print("Done", max_row['name'], max_row['area_sqm']/1e6, "km2")

import json
answer = {
    "question_id": "C03",
    "status": "ok",
    "value": max_row['name'],
    "unit": "name",
    "parameters_used": {},
    "assumptions": "All flooded polygons are in the same CRS as taluks, so area is accurate.",
    "method": "Intersect flood extent with taluks, compute area, aggregate by taluk name, and select the maximum."
}
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print("Answer written to pred_results/answer.json")

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
