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
schools = gpd.read_file('dataset/schools.geojson')
districts = gpd.read_file('dataset/districts.gpkg')
flood = gpd.read_file('dataset/flood_extent_20180821.gpkg')
print('loaded', schools.shape, districts.shape, flood.shape)



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
