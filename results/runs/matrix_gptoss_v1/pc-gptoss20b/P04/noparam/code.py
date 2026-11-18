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
taluks_utm = taluks.to_crs('EPSG:32643')
_disp_write(taluks_utm, 'taluks_utm')
_summ(taluks_utm, 'taluks_utm')


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
hospitals_utm = hospitals.to_crs('EPSG:32643')
_disp_write(hospitals_utm, 'hospitals_utm')
_summ(hospitals_utm, 'hospitals_utm')


import json
# Filter taluks to Ernakulam or Alappuzha
sel_taluks = taluks_utm[taluks_utm['district'].isin(['Ernakulam','Alappuzha'])]
# Keep only schools that joined to these taluks
schools_taluk_sel = schools_taluk[schools_taluk['name_right'].isin(sel_taluks['name'])]
# Build spatial index for hospitals
hosp_idx = hospitals_utm.sindex

def nearest_dist(point):
    # query nearest hospital geometry
    idx = list(hosp_idx.nearest(point, 1))[0]
    nearest_geom = hospitals_utm.geometry.iloc[idx]
    return point.distance(nearest_geom)

schools_taluk_sel['dist_to_hosp'] = schools_taluk_sel.geometry.apply(nearest_dist)
schools_taluk_sel['no_hosp_within'] = schools_taluk_sel['dist_to_hosp'] > 5000
counts = schools_taluk_sel[schools_taluk_sel['no_hosp_within']].groupby('name_right').size().reset_index(name='count')
if not counts.empty:
    max_row = counts.loc[counts['count'].idxmax()]
    answer = {
        "question_id": "P04",
        "status": "ok",
        "value": int(max_row['count']),
        "unit": "count",
        "parameters_used": {"relief_camp_hospital_access_m": 5000, "facility_point_rule": "within"},
        "assumptions": "Assumed 5 km access distance and within rule.",
        "method": "Count schools with no hospital within 5 km per taluk."
    }
else:
    answer = {
        "question_id": "P04",
        "status": "cannot_answer",
        "value": None,
        "unit": None,
        "parameters_used": {"relief_camp_hospital_access_m": 5000, "facility_point_rule": "within"},
        "assumptions": "No schools found in selected taluks.",
        "method": "Attempted count but no data."
    }
with open('pred_results/answer.json', 'w', encoding='utf-8') as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print('Answer written')

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
