"""
Convert BOEM GoM offshore pipelines shapefile data into geojson.

References:
https://worldmap.harvard.edu/data/geonode:gulf_of_mexico_pipelines_cpu
http://worldmap.harvard.edu/geoserver/geonode/geonode:gulf_of_mexico_pipelines_cpu/wms?tiled=true&service=WMS&request=GetCapabilities
https://www.data.bsee.gov/Pipeline/PipelinePermits/FieldDefinitions.aspx
https://www.data.bsee.gov/Main/Pipeline.aspx
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
zip_fname = "Harvard_Worldmap_data/gulf_of_mexico_pipelines_cpu.zip"
shp_stem_name = "gulf_of_mexico_pipelines_cpu"   # specify the root name of the shape file, no extension
# "urn:ogc:def:crs:EPSG::4267"  NAD27

geojson_fname = "BSEE_GoM_pipelines.geojson"  # output file name

# clean-up extracted/temporary files
cleanup = True
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

# https://www.data.bsee.gov/Pipeline/PipelinePermits/FieldDefinitions.aspx
PROD_CODE_map = {
"ACID": "ACID",
"AIR": "PNEUMATIC",
"BLGH": "BULK GAS WITH TRACE LEVELS OF HYDROGEN SULFIDE",
"BLKG": "BULK GAS - FULL WELL STREAM PRODUCTION FROM GAS WELL(S) PRIO",
"BLKO": "BULK OIL - FULL WELL STREAM PRODUCTION FROM OIL WELL(S) PRIO",
"BLOH": "BULK OIL WITH TRACE LEVELS OF HYDROGEN SULFIDE",
"CBLC": "A NON-UMBILICAL CABLE SUCH AS FIBER OPTIC/COMMUNICATIONS",
"CBLP": "POWER CABLE",
"CBLR": "RENEWABLE ENERGY POWER CABLE",
"CHEM": "CORROSION INHIBITOR or OTHER CHEMICALS",
"CO2": "CARBON DIOXIDE (SUPPORT ACTIVITY LEASE)",
"COND": "CONDENSATE or DISTILLATE TRANSPORTED DOWNSTREAM OF FIRST PRO",
"CSNG": "PIPELINE USED AS A PROTECTIVE CASING (CSNG) FOR ANOTHER PIPELINE.",
"FLG": "FLARE GAS",
"G/C": "GAS AND CONDENSATE SERVICE AFTER FIRST PROCESSING",
"G/CH": "GAS AND CONDENSATE (H2S)",
"G/O": "GAS AND OIL SERVICE AFTER FIRST PROCESSING",
"G/OH": "GAS AND OIL (H2S)",
"GAS": "GAS TRANSPORTED AFTER FIRST PROCESSING",
"GASH": "PROCESSED GAS WITH TRACE LEVELS OF HYDROGEN SULFIDE",
"H2O": "WATER",
"INJ": "GAS INJECTION",
"LGER": "LIQUID GAS ENHANCED RECOVERY",
"LIFT": "GAS LIFT",
"LPRO": "LIQUID PROPANE",
"METH": "METHANOL / GLYCOL",
"NGER": "NATURAL GAS ENHANCED RECOVERY",
"NGL": "Natural Gas Liquids",
"O/W": "OIL AND WATER TRANSPORTED AFTER FIRST PROCESSING",
"OIL": "OIL TRANSPORTED AFTER FIRST PROCESSING",
"OILH": "PROCESSED OIL WITH TRACE LEVELS OF HYDROGEN SULFIDE",
"PWTR": "PRESSURIZED WATER (RENEWABLE ENERGY)",
"SERV": "SERVICE or UTILITY LINE USED FOR PIGGING AND PIPELINE MAINTE",
"SPLY": "SUPPLY GAS",
"SPRE": "SPARE",
"SULF": "LIQUIFIED SULPHUR or SLURRIED SULPHER",
"TEST": "TEST",
"TOW": "TOW ROUTE ONLY - NOT A PIPELINE",
"UBEH": "ELECTRO /HYDRAULIC UMBILICAL",
"UMB": "UMBILICAL LINE. USUALLY INCLUDES PNEUMATIC or HYDRAULIC CONT",
"UMBC": "CHEMICAL UMBILICAL",
"UMBE": "ELECTRICAL UMBILICAL",
"UMBH": "HYDRAULIC UMBILICAL",    
}

PPL_SIZE_C_map = {
"0.5": "1/2\" pipe",
"0.75": "3/4\" pipe",
"01": "1\"",
"01-02": "1\" to 2 7/8\"",
"01-03": "1\" to 3 1/2\"",
"02": "2 1/2\" or 2 7/8\"",
"02-01": "(2 1/2\" or 2 7/8\") to 1\"",
"02-03": "(2 1/2\" or 2 7/8\") to 3\"",
"02-04": "(2 1/2\" or 2 7/8\") to 4\"",
"02-06": "2\" to 6\"",
"03": "3 1/2\"",
"03-01": "3 1/2\" to 1\"",
"03-02": "3 1/2\" to (2 1/2\" or 2 7/8\")",
"03-04": "3 1/2\" to 4\"",
"03-06": "3 1/2\" to 6 5/8\"",
"04": "4\"",
"04-02": "4\" to (2 1/2\" or 2 7/8\")",
"04-03": "4\" to 3 1/2\"",
"04-06": "4\" to 6 5/8\"",
"05": "5\"",
"06": "6 5/8\"",
"06-03": "6 5/8\" to 3 1/2\"",
"06-04": "6 5/8\" to 4\"",
"06-08": "6 5/8\" to 8 5/8\"",
"07": "special 7\" pipe",
"08": "8 5/8\"",
"08-06": "8 5/8\" to 6 5/8\"",
"08-10": "8 5/8\" to 10 3/4\"",
"08-12": "8 5/8\" to 12 3/4\"",
"10": "10 3/4\"",
"10-08": "10 3/4\" to 8 5/8\"",
"10-12": "10 3/4\" to 12 3/4\"",
"12": "12\"",
"12-10": "12 3/4\" to 10 3/4\"",
"12-14": "12 3/4\" to 14\"",
"14": "14\"",
"14-10": "14\" to 10 3/4\"",
"14-12": "14\" to 12 3/4\"",
"14-16": "14\" to 16\"",
"16": "16\"",
"16-14": "16\" to 14\"",
"16-18": "16\" to 18\"",
"18": "18\"",
"18-16": "18\" to 16\"",
"18-20": "18\" to 20\"",
"20": "20\"",
"20-18": "20\" to 18\"",
"20-24": "20\" to 24\"",
"22": "22\"",
"24": "24\"",
"24-20": "24\" to 20\"",
"24-26": "24\" to 26\"",
"24-30": "24\" to 30\"",
"26": "26\"",
"26-24": "26\" to 24\"",
"26-30": "26\" to 30\"",
"28": "28\"",
"30": "30\"",
"30-24": "30\" to 24\"",
"30-26": "30\" to 26\"",
"36": "36\"",
"42": "42\"",
"48": "48\"",
"54": "54\"",
"OTHER": "Other",    
}

STATUS_COD_map = {
"A/C": "ABANDONED AND COMBINED",
"ABN": "ABANDONED",
"ACT": "ACTIVE",
"CNCL": "CANCELLED",
"COMB": "COMBINED",
"O/C": "OUT AND COMBINED",
"OUT": "OUT OF SERVICE",
"PABN": "PROPOSE ABANDONMENT",
"PREM": "PROPOSE REMOVAL",
"PROP": "PROPOSED",
"R/A": "RELINQUISHED AND ABANDONED",
"R/C": "RELINQUISHED AND COMBINED",
"R/R": "RELINQUISHED AND REMOVED",
"RELQ": "RELINQUISHED",
"REM": "REMOVED",
}


for _f in pl_jdata['features']:
    _meta = {k:v for k,v in _f['properties'].items() if v is not None}

    new_meta = {}
    if 'NAME' in _meta and _meta['NAME']:
        new_meta["name"] = _meta['NAME']

    if 'CO_NAME' in _meta and _meta['CO_NAME']:
        new_meta["CO_NAME"] = _meta['CO_NAME']

    # if 'MMS_PIPELI' in _meta and _meta['MMS_PIPELI']:
    #     new_meta["MMS_PIPELI"] = _meta['MMS_PIPELI']

    if 'STATUS_COD' in _meta and _meta['STATUS_COD']:
        # if _meta['STATUS_COD'] == "A/C":
        #     new_meta["status"] = "ABANDONED AND COMBINED"
        # elif _meta['STATUS_COD'] == "ABN":
        #     new_meta["status"] = "ABANDONED"
        # elif _meta['STATUS_COD'] == "ACTIVE":
        #     new_meta["status"] = "ACTIVE"
        # elif _meta['STATUS_COD'] == "CNCL":
        #     new_meta["status"] = "CANCELLED"
        # elif _meta['STATUS_COD'] == "COMB":
        #     new_meta["status"] = "COMBINED"
        # elif _meta['STATUS_COD'] == "O/C":
        #     new_meta["status"] = "OUT AND COMBINED"
        # elif _meta['STATUS_COD'] == "OUT":
        #     new_meta["status"] = "OUT OF SERVICE"
        # elif _meta['STATUS_COD'] == "PABN":
        #     new_meta["status"] = "PROPOSE ABANDONMENT"
        # elif _meta['STATUS_COD'] == "PREM":
        #     new_meta["status"] = "PROPOSE REMOVAL"
        # elif _meta['STATUS_COD'] == "PROP":
        #     new_meta["status"] = "PROPOSED"
        # elif _meta['STATUS_COD'] == "R/A":
        #     new_meta["status"] = "RELINQUISHED AND ABANDONED"
        # elif _meta['STATUS_COD'] == "R/C":
        #     new_meta["status"] = "RELINQUISHED AND COMBINED"
        # elif _meta['STATUS_COD'] == "R/R":
        #     new_meta["status"] = "RELINQUISHED AND REMOVED"
        # elif _meta['STATUS_COD'] == "RELQ":
        #     new_meta["status"] = "RELINQUISHED"
        # elif _meta['STATUS_COD'] == "RELQ":
        #     new_meta["status"] = "RELINQUISHED"
        # elif _meta['STATUS_COD'] == "REM":
        #     new_meta["status"] = "REMOVED"
        if _meta['STATUS_COD'] in STATUS_COD_map:
            new_meta["status"] = STATUS_COD_map[_meta['STATUS_COD']]
        else:
            new_meta["STATUS_CODE"] = _meta['STATUS_COD']


    if 'PPL_SIZE_C' in _meta and _meta['PPL_SIZE_C']:
        if _meta['PPL_SIZE_C'] in PPL_SIZE_C_map:
            new_meta["size"] = PPL_SIZE_C_map[_meta['PPL_SIZE_C']]
        else:
            new_meta["PPL_SIZE_C"] = _meta['PPL_SIZE_C']
        #new_meta["PPL_SIZE_CODE"] = _meta['PPL_SIZE_C']

    if 'PROD_CODE' in _meta and _meta['PROD_CODE']:
        if _meta['PROD_CODE'] in PROD_CODE_map:
            new_meta["product"] = PROD_CODE_map[_meta['PROD_CODE']]
        else:
            new_meta["PROD_CODE"] = _meta['PROD_CODE']

    if 'MAOP_PRSS' in _meta and _meta['MAOP_PRSS']:
        try:
            _press = int(_meta['MAOP_PRSS'])
            if _press:
                new_meta["MAOP_PRSS"] = _press
        except Exception:
            pass


    if 'SEGMENT_NU' in _meta and _meta['SEGMENT_NU']:
        try:
            new_meta["SEGMENT_NUM"] = int(_meta['SEGMENT_NU'])
        except Exception:
            pass

    if "SEGMENT_NUM" not in new_meta:
        if 'MMS_PIPELI' in _meta and _meta['MMS_PIPELI']:
            new_meta["MMS_PIPELI"] = _meta['MMS_PIPELI']
        elif 'MMS_PIPE_1' in _meta and _meta['MMS_PIPE_1']:
            new_meta["MMS_PIPE_1"] = _meta['MMS_PIPE_1']

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

