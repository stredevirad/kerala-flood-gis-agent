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


_src = rasterio.open('dataset/s1_vv_20180821_db.tif')
if _src.count > 1:
    s1_vv = _src.read().astype(float)
else:
    s1_vv = _src.read(1).astype(float)
s1_vv_meta = dict(
    crs=_src.crs,
    transform=_src.transform,
    width=_src.width,
    height=_src.height,
    nodata=_src.nodata,
    dtype=_src.dtypes[0],
    count=_src.count,
    bounds=_src.bounds,
)
print(f"Size: {_src.width}x{_src.height}")
print(f"Bands: {_src.count}")
print(f"CRS: {_src.crs}")
print(f"Dtype: {_src.dtypes[0]}")
if _src.count > 1:
    print(f"Shape: {s1_vv.shape} (bands, height, width)")
    for _b in range(_src.count):
        _band = s1_vv[_b]
        print(f"  Band {_b+1}: min={_band[~__import__('numpy').isnan(_band)].min():.4g}, max={_band[~__import__('numpy').isnan(_band)].max():.4g}" if not __import__('numpy').all(__import__('numpy').isnan(_band)) else f"  Band {_b+1}: all NaN")
    print(f"\nHint: s1_vv has {_src.count} bands. Access bands by index: s1_vv[0]=Band1, s1_vv[1]=Band2, etc.")
else:
    print(f"Value range: min={s1_vv.min():.4g}, max={s1_vv.max():.4g}")
print(f"Bounds: {_src.bounds}")
if _src.nodata is not None:
    print(f"NoData: {_src.nodata}")
    import numpy as _np
    s1_vv[s1_vv == _src.nodata] = _np.nan
    if _src.count == 1:
        print(f"NoData replaced with NaN, valid range: min={s1_vv[~_np.isnan(s1_vv)].min():.4g}, max={s1_vv[~_np.isnan(s1_vv)].max():.4g}")
    else:
        print(f"NoData replaced with NaN across all bands")
print(f"Transform: {_src.transform}")
if _src.count == 1:
    print(f"\\nHint: s1_vv is ndarray(float) shape (H, W), s1_vv_meta is dict(crs/transform/nodata etc.)")
    print(f"To write GeoTIFF: rasterio.open(path, 'w', driver='GTiff', height=s1_vv.shape[0], width=s1_vv.shape[1], count=1, dtype='float32', crs=s1_vv_meta['crs'], transform=s1_vv_meta['transform'])")
_src.close()


import os
os.makedirs('pred_results', exist_ok=True)


import os, json, rasterio, numpy as np
print(os.listdir('pred_results'))


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
