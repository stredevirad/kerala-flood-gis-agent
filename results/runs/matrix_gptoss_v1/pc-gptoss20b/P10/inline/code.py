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


import geopandas as gpd, rasterio, numpy as np, json, os
# load data
dem_path='dataset/dem_cop30.tif'
taluks_path='dataset/taluks.gpkg'
flood_path='dataset/flood_extent_20180821.gpkg'

# read rasters and vectors
with rasterio.open(dem_path) as src:
    dem = src.read(1)
    dem_meta = src.meta
    transform = src.transform
    crs = src.crs

# taluks
taluks = gpd.read_file(taluks_path)
# ensure same CRS
if taluks.crs != crs:
    taluks = taluks.to_crs(crs)
# assign integer id
taluks = taluks.reset_index(drop=True)
taluks['tid'] = taluks.index

# flood extent
flood = gpd.read_file(flood_path)
if flood.crs != crs:
    flood = flood.to_crs(crs)

# rasterize taluks
from rasterio.features import rasterize
shape_taluks = [(geom, val) for geom, val in zip(taluks.geometry, taluks.tid)]
# create empty array
taluk_raster = rasterize(shape_taluks, out_shape=dem.shape, transform=transform, fill=0, dtype='int32')

# low-lying mask
low_mask = (dem <= 10) & (~np.isnan(dem))

# compute low-lying pixel count per taluk
low_ids = taluk_raster[low_mask]
# exclude 0 (outside taluks)
low_ids = low_ids[low_ids>0]
low_counts = np.bincount(low_ids, minlength=taluks.shape[0]+1)[1:]  # skip 0

# rasterize flood extent
shape_flood = [(geom, 1) for geom in flood.geometry]
flood_raster = rasterize(shape_flood, out_shape=dem.shape, transform=transform, fill=0, dtype='uint8')

# overlap mask
overlap_mask = low_mask & (flood_raster==1)
# compute overlap pixel count per taluk
overlap_ids = taluk_raster[overlap_mask]
overlap_ids = overlap_ids[overlap_ids>0]
overlap_counts = np.bincount(overlap_ids, minlength=taluks.shape[0]+1)[1:]

# compute areas
pixel_area = 900  # m2
low_area = low_counts * pixel_area
overlap_area = overlap_counts * pixel_area

# filter taluks with low_area >=10 km2
min_area = 10_000_000
valid = low_area >= min_area
if not np.any(valid):
    answer = {
        "question_id": "P10",
        "status": "cannot_answer",
        "value": None,
        "unit": None,
        "parameters_used": {"low_lying_max_elevation_m":10,"raster_area_rule":"pixel_count*900 m2"},
        "assumptions": "No taluk has at least 10 km2 of low-lying land.",
        "method": "Computed low-lying area per taluk from DEM and filtered by 10 km2 threshold."
    }
else:
    shares = np.where(valid, overlap_area/low_area*100, 0)
    idx = np.argmax(shares)
    taluk_name = taluks.loc[idx, 'name']
    answer = {
        "question_id": "P10",
        "status": "ok",
        "value": float(shares[idx]),
        "unit": "percent",
        "parameters_used": {"low_lying_max_elevation_m":10,"raster_area_rule":"pixel_count*900 m2"},
        "assumptions": "Low-lying defined as DEM <=10 m; flood extent polygon used as given.",
        "method": "Rasterized taluks and flood extent, counted low-lying pixels per taluk, computed share of overlap."
    }

# write answer
os.makedirs('pred_results', exist_ok=True)
with open('pred_results/answer.json', 'w', encoding='utf-8') as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print('Answer written')


import json, os
# Load the answer that was already written
with open('pred_results/answer.json', 'r', encoding='utf-8') as f:
    answer = json.load(f)
# Update unit to match expected validator value
answer['unit'] = 'percent'
# Write back
os.makedirs('pred_results', exist_ok=True)
with open('pred_results/answer.json', 'w', encoding='utf-8') as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print('Updated answer.json with unit percent')

import json, os
# Load the existing answer
with open('pred_results/answer.json', 'r', encoding='utf-8') as f:
    answer = json.load(f)
# Replace value with taluk name and set unit to 'name'
# The original answer stored the percent in answer['value'] and the taluk name in answer['name']? It did not.
# We need to extract the taluk name from the original calculation.
# Recompute the taluk name from the data to be safe.
import geopandas as gpd
import rasterio
import numpy as np
from rasterio.features import rasterize

dem_path='dataset/dem_cop30.tif'
taluks_path='dataset/taluks.gpkg'
flood_path='dataset/flood_extent_20180821.gpkg'

with rasterio.open(dem_path) as src:
    dem=src.read(1)
    transform=src.transform
    crs=src.crs

# taluks
taluks=gpd.read_file(taluks_path).to_crs(crs).reset_index(drop=True)
taluks['tid']=taluks.index

# flood
flood=gpd.read_file(flood_path).to_crs(crs)

# rasterize taluks
shape_taluks=[(geom,val) for geom,val in zip(taluks.geometry,taluks.tid)]
taluk_raster=rasterize(shape_taluks,out_shape=dem.shape,transform=transform,fill=0,dtype='int32')

# low-lying mask
low_mask=(dem<=10)&(~np.isnan(dem))
low_ids=taluk_raster[low_mask]
low_ids=low_ids[low_ids>0]
low_counts=np.bincount(low_ids,minlength=taluks.shape[0]+1)[1:]

# flood raster
shape_flood=[(geom,1) for geom in flood.geometry]
flood_raster=rasterize(shape_flood,out_shape=dem.shape,transform=transform,fill=0,dtype='uint8')

# overlap
overlap_mask=low_mask&(flood_raster==1)
overlap_ids=taluk_raster[overlap_mask]
overlap_ids=overlap_ids[overlap_ids>0]
overlap_counts=np.bincount(overlap_ids,minlength=taluks.shape[0]+1)[1:]

pixel_area=900
low_area=low_counts*pixel_area
overlap_area=overlap_counts*pixel_area

min_area=10_000_000
valid=low_area>=min_area
if not np.any(valid):
    taluk_name=None
else:
    shares=np.where(valid,overlap_area/low_area*100,0)
    idx=np.argmax(shares)
    taluk_name=taluks.loc[idx,'name']

# Update answer
answer['value']=taluk_name
answer['unit']='name'
# Remove any numeric value field
answer.pop('value',None)
# Write back
os.makedirs('pred_results',exist_ok=True)
with open('pred_results/answer.json','w',encoding='utf-8') as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print('Answer updated to taluk name')

import json, os
import geopandas as gpd
import rasterio
import numpy as np
from rasterio.features import rasterize

# Paths
DEM='dataset/dem_cop30.tif'
TALUKS='dataset/taluks.gpkg'
FLOOD='dataset/flood_extent_20180821.gpkg'

# Load data
with rasterio.open(DEM) as src:
    dem=src.read(1)
    tr=src.transform
    crs=src.crs

# Taluks
lt=gpd.read_file(TALUKS).to_crs(crs).reset_index(drop=True)
lt['tid']=lt.index

# Flood extent
lf=gpd.read_file(FLOOD).to_crs(crs)

# Rasterize taluks
shape_t=[(geom,val) for geom,val in zip(lt.geometry,lt.tid)]
rt=rasterize(shape_t,out_shape=dem.shape,transform=tr,fill=0,dtype='int32')

# Low‑lying mask
low=(dem<=10)&(~np.isnan(dem))
low_ids=rt[low]
low_ids=low_ids[low_ids>0]
low_counts=np.bincount(low_ids,minlength=lt.shape[0]+1)[1:]

# Flood raster
shape_f=[(geom,1) for geom in lf.geometry]
fr=rasterize(shape_f,out_shape=dem.shape,transform=tr,fill=0,dtype='uint8')

# Overlap
ov=(low)&(fr==1)
ov_ids=rt[ov]
ov_ids=ov_ids[ov_ids>0]
ov_counts=np.bincount(ov_ids,minlength=lt.shape[0]+1)[1:]

pixel_area=900
low_area=low_counts*pixel_area
ov_area=ov_counts*pixel_area

min_area=10_000_000
valid=low_area>=min_area
if not np.any(valid):
    taluk_name=None
else:
    shares=np.where(valid,ov_area/low_area*100,0)
    idx=np.argmax(shares)
    taluk_name=lt.loc[idx,'name']

answer={
    "question_id": "P10",
    "status": "ok" if taluk_name else "cannot_answer",
    "value": taluk_name,
    "unit": "name",
    "parameters_used": {"low_lying_max_elevation_m":10,"raster_area_rule":"pixel_count*900 m2"},
    "assumptions": "Low‑lying defined as DEM <=10 m; flood extent polygon used as given.",
    "method": "Rasterized taluks and flood extent, counted low‑lying pixels per taluk, computed share of overlap and selected taluk with highest share."
}

os.makedirs('pred_results',exist_ok=True)
with open('pred_results/answer.json','w',encoding='utf-8') as f:
    json.dump(answer,f,ensure_ascii=False,indent=2)
print('Answer written')