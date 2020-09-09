"""
Convert BSEE GoM offshore pipelines shapefile data into geojson.

References:
https://worldmap.harvard.edu/data/geonode:gulf_of_mexico_pipelines_cpu
http://worldmap.harvard.edu/geoserver/geonode/geonode:gulf_of_mexico_pipelines_cpu/wms?tiled=true&service=WMS&request=GetCapabilities

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


# https://data-ogauthority.opendata.arcgis.com/datasets/oga-offshore-zipped-shapefiles-wgs84
zip_fname = None
#shp_stem_name = "ppl_arcs"   # specify the root name of the shape file, no extension
shp_fname = "BSEE_pipelines/ppl_arcs.shp"
# "urn:ogc:def:crs:EPSG::4267"  NAD27

geojson_fname = "GoM_ppl_arcs.geojson"  # output file name

# clean-up extracted/temporary files
cleanup = False
# minify geojson file (requires https://github.com/TNOCS/minify-geojson)
minify_geojson = True
# End inputs --------

if zip_fname:
    extracted_files = []
    with ZipFile(zip_fname, 'r') as zf:
        zfiles = zf.namelist()
        for _fname in zfiles:
            if not _fname.startswith(shp_stem_name):
                continue
            op = zf.extract(_fname)
            if op.lower().endswith(".shp"):
                shp_fname = op
            extracted_files.append(op)


pl_df = geopandas.read_file(shp_fname) 


# clean up...
if cleanup:
    for _fname in extracted_files:
        os.remove(_fname)
        print(f"INFO: deleted shape file {os.path.basename(_fname)}")


pl_df.to_file(geojson_fname, driver='GeoJSON')
with open(geojson_fname, 'r') as fh:
    pl_jdata = json.load(fh)



for _f in pl_jdata['features']:
    _meta = {k:v for k,v in _f['properties'].items() if v is not None}

    new_meta = {}
    if 'NAME' in _meta and _meta['NAME']:
        new_meta["name"] = _meta['NAME']

    if 'CO_NAME' in _meta and _meta['CO_NAME']:
        new_meta["CO_NAME"] = _meta['CO_NAME']

    if 'SDE_COMPAN' in _meta and _meta['SDE_COMPAN']:
        new_meta["SDE_COMPAN"] = _meta['SDE_COMPAN']

    if 'STATUS_COD' in _meta and _meta['STATUS_COD']:
        new_meta["STATUS_COD"] = _meta['STATUS_COD']

    if 'PPL_SIZE_C' in _meta and _meta['PPL_SIZE_C']:
        new_meta["PPL_SIZE_C"] = _meta['PPL_SIZE_C']

    if 'PROD_CODE' in _meta and _meta['PROD_CODE']:
        new_meta["PROD_CODE"] = _meta['PROD_CODE']

    #if 'APRV_CODE' in _meta and _meta['APRV_CODE']:
    #    new_meta["APRV_CODE"] = _meta['APRV_CODE']

    _f['properties'] = new_meta.copy()


# add some top-level metadata into the "crs" object
crs = pl_jdata.setdefault("crs", {})
props = crs.setdefault("properties", {})
props["ts"] = datetime.utcnow().isoformat()
props["url"] = "qwilka.com"


with open(geojson_fname, 'w') as fh:
    json.dump(pl_jdata, fh)

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

