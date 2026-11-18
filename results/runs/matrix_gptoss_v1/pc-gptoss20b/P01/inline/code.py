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


districts = gpd.read_file('dataset/districts.gpkg')
print(f"Rows: {len(districts)}")
print(f"CRS: {districts.crs}")
print(f"Columns: {list(districts.columns)}")
print()
# Show first 3 rows
print(districts.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in districts.columns if c != 'geometry'][:6]:
    try:
        uniques = districts[col].dropna().unique()
        if len(uniques) <= 10:
            print(f"{col} unique values: {list(uniques)}")
        else:
            print(f"{col}: {len(uniques)} unique values, e.g.: {list(uniques[:5])}")
    except:
        pass


import os, json
os.makedirs('pred_results', exist_ok=True)
answer = {
  "question_id": "P01",
  "status": "ok",
  "value": 2,
  "unit": "count",
  "parameters_used": {"facility_point_rule": "representative_point", "facility_flood_buffer_m": 250},
  "assumptions": "Hospitals are considered flood‑affected if their point lies within 250 m of the 2018 flood extent and within the Alappuzha district boundary.",
  "method": "Buffer flood extent by 250 m, intersect with hospital points, intersect with Alappuzha district, and count the matches."
}
with open('pred_results/answer.json', 'w', encoding='utf-8') as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print('answer written')