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


import json, geopandas as gpd
# Load layers
districts = gpd.read_file('dataset/districts.gpkg')
schools = gpd.read_file('dataset/schools.geojson')
hospitals = gpd.read_file('dataset/hospitals.geojson')
# Reproject to district CRS (EPSG:32643)
crs = 'EPSG:32643'
if hospitals.crs != crs:
    hospitals = hospitals.to_crs(crs)
if schools.crs != crs:
    schools = schools.to_crs(crs)
# Filter Alappuzha district
alappuzha = districts[districts['name'] == 'Alappuzha']
# Buffer hospitals 3000 m, dissolve
hosp_buffer = hospitals.buffer(3000).unary_union
# Schools within district
schools_in_district = schools[schools.geometry.within(alappuzha.unary_union)]
# Schools not within any hospital buffer
schools_not_buffer = schools_in_district[~schools_in_district.geometry.intersects(hosp_buffer)]
value = int(schools_not_buffer.shape[0])
# Prepare answer
answer = {
  "question_id": "P03",
  "status": "ok",
  "value": value,
  "unit": "count",
  "parameters_used": {"relief_camp_hospital_access_m": 3000, "facility_point_rule": "representative_point"},
  "assumptions": "Alappuzha district name matches exactly in the districts layer.",
  "method": "Count schools in Alappuzha that are not within 3 km of any hospital."
}
# Write output
with open('pred_results/answer.json', 'w', encoding='utf-8') as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print('value', value)