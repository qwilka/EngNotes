"""
Convert UK OGA offshore pipelines shapefile data into geojson.

References:
https://data-ogauthority.opendata.arcgis.com/datasets/oga-offshore-zipped-shapefiles-wgs84  OGA_OFF_WGS84.zip
https://ndr.ogauthority.co.uk   DealPipelinesKis.csv
https://github.com/qwilka/qwilka.github.io/blob/master/gis/assets/OGA_pipelines.geojson

"""
from datetime import datetime
import json
import os
import subprocess
from zipfile import ZipFile

from dateutil import parser as duparser
import geopandas
import numpy as np
import pandas as pd


# Inputs ----------
# https://ndr.ogauthority.co.uk
# More>Infrastructure>Pipelines
# click "Export->" button and "Export all data" to CSV file
NDR_platforms_fname = "DealSurfaceKis.csv"

# https://data-ogauthority.opendata.arcgis.com/datasets/oga-offshore-zipped-shapefiles-wgs84
OGA_zip_fname = "OGA_data/OGA_OFF_WGS84_2020-09-03.zip"
shp_stem_name = "OGA_InfrastructureSurface_WGS84"   # specify the root name of the shape file, no extension

geojson_fname = "OGA_platforms.geojson"  # output file name

# clean-up extracted/temporary files
cleanup = False
# use geopandas to create geojson (direct_method=True), or use alternative method (False)
direct_method = True 
# minify geojson file (requires https://github.com/TNOCS/minify-geojson)
minify_geojson = False
# End inputs --------


DealPlatforms_df = pd.read_csv(NDR_platforms_fname, encoding="ISO-8859-1")

# extract shape files from OGA_OFF_WGS84.zip
extracted_files = []
with ZipFile(OGA_zip_fname, 'r') as zf:
    zfiles = zf.namelist()
    for _fname in zfiles:
        if not _fname.startswith(shp_stem_name):
            continue
        op = zf.extract(_fname)
        if op.lower().endswith(".shp"):
            shp_fname = op
        extracted_files.append(op)

OGA_pl_df = geopandas.read_file(shp_fname) 

# filter FPSO type
OGA_pl_df["TYPE"].unique()
fpso = OGA_pl_df["TYPE"]=="FPSO"
OGA_pl_df[["NAME", "TYPE", "STATUS", "INS_DATE"]][fpso] 
# "NAME", "TYPE", "STATUS", "INS_DATE"

# clean up...
if cleanup:
    for _fname in extracted_files:
        os.remove(_fname)
        print(f"INFO: deleted shape file {os.path.basename(_fname)}")


OGA_pl_df.to_file(geojson_fname, driver='GeoJSON')
with open(geojson_fname, 'r') as fh:
    OGA_pl_data = json.load(fh)

# filter the properties object in each geojson feature to retain only relevant metadata
for _f in OGA_pl_data['features']:
    _meta = {k:v for k,v in _f['properties'].items() if v is not None}

    new_meta = {}
    if 'NAME' in _meta and _meta['NAME']:
        new_meta["name"] = _meta['NAME']

    if 'OPERATOR' in _meta and _meta['OPERATOR']:
        new_meta["operator"] = _meta['OPERATOR']

    if 'TYPE' in _meta and _meta['TYPE']:
        new_meta["type"] = _meta['TYPE']

    if 'STATUS' in _meta and _meta['STATUS']:
        new_meta["status"] = _meta['STATUS']


    if 'INS_DATE' in _meta and _meta['INS_DATE']:
        try:
            dt=duparser.parse(_meta['INS_DATE'])
            new_meta["installed"] =  dt.date().isoformat()
        except Exception:
            pass

    if 'DESC_' in _meta and _meta['DESC_']:
        new_meta["desc"] = _meta['DESC_']

    if 'DATASOURCE' in _meta and _meta['DATASOURCE']:
        new_meta["data src"] = _meta['DATASOURCE']
    
    _f['properties'] = new_meta.copy()


# add some top-level metadata into the "crs" object
crs = OGA_pl_data.setdefault("crs", {})
props = crs.setdefault("properties", {})
props["ts"] = datetime.utcnow().isoformat()
props["url"] = "qwilka.com"


with open(geojson_fname, 'w') as fh:
    json.dump(OGA_pl_data, fh)

# https://github.com/TNOCS/minify-geojson
# this seems to strip out the "crs" object...
if minify_geojson:
    commandList = [
        'minify-geojson',
        "--verbose",
        "--coordinates", "5",
        geojson_fname
    ]
    try:
        op = subprocess.run(commandList, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as err:
        print(f"WARNING: cannot minify geojson file {geojson_fname}: {err} {op.stderr.decode('UTF-8')}.")
    else:
        print(f"INFO: minify-geojson: {op.stdout.decode('UTF-8')}")
        if op.stderr:
            print(f"WARNING: minify-geojson: {op.stderr.decode('UTF-8')}")
