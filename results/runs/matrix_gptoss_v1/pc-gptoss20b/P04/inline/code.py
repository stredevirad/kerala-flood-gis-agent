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


hospitals = gpd.read_file('dataset/hospitals.geojson')
print(f"Rows: {len(hospitals)}")
print(f"CRS: {hospitals.crs}")
print(f"Columns: {list(hospitals.columns)}")
print()
# Show first 3 rows
print(hospitals.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in hospitals.columns if c != 'geometry'][:6]:
    try:
        uniques = hospitals[col].dropna().unique()
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
_src = hospitals_utm
_geo = (_src.crs is None) or _src.crs.is_geographic
_work = _src.to_crs(_src.estimate_utm_crs()) if _geo else _src
hospitals_buf = _work.copy()
hospitals_buf['geometry'] = _work.geometry.buffer(3000)
hospitals_buf = hospitals_buf.to_crs(_src.crs) if _geo and _src.crs is not None else hospitals_buf
_disp_write(hospitals_buf, 'hospitals_buf')
_summ(hospitals_buf, 'hospitals_buf')



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
schools_utm = schools.to_crs('EPSG:32643')
_disp_write(schools_utm, 'schools_utm')
_summ(schools_utm, 'schools_utm')



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
_b = hospitals_buf.to_crs(schools_utm.crs) if (schools_utm.crs is not None and hospitals_buf.crs is not None and schools_utm.crs != hospitals_buf.crs) else hospitals_buf
schools_join = _gpd.sjoin(schools_utm, _b, predicate='within', how='left')
_disp_write(schools_join, 'schools_join')
_summ(schools_join, 'schools_join')



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
schools_outside = schools_join.query('index_right.isna()').reset_index(drop=True)
_disp_write(schools_outside, 'schools_outside')
_summ(schools_outside, 'schools_outside')


import geopandas as gpd
schools_outside = gpd.read_file("pred_results/schools_outside.geojson") if False else None


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
schools_outside = schools_join.query('index_right.isna()').reset_index(drop=True)
_disp_write(schools_outside, 'schools_outside')
_summ(schools_outside, 'schools_outside')


import geopandas as gpd
schools_outside_clean = schools_outside.drop(columns=['index_right'])
schools_taluk = gpd.sjoin(schools_outside_clean, taluks, how='left', predicate='within')
filtered = schools_taluk[schools_taluk['district'].isin(['Ernakulam', 'Alappuzha'])]
counts = filtered.groupby(['name', 'district']).size().reset_index(name='school_count')
max_row = counts.loc[counts['school_count'].idxmax()]
answer = {
    "question_id": "P04",
    "status": "ok",
    "value": int(max_row['school_count']),
    "unit": "count",
    "parameters_used": {"relief_camp_hospital_access_m": 3000, "facility_point_rule": "representative_point geometry rule"},
    "assumptions": "All schools and hospitals are projected to EPSG:32643 and buffers are Euclidean 3000 m.",
    "method": "Buffer hospitals, select schools outside buffers, spatially join to taluks, count per taluk, take maximum."
}
import json, os
os.makedirs('pred_results', exist_ok=True)
with open('pred_results/answer.json', 'w', encoding='utf-8') as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
answer


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
