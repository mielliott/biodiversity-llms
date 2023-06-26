import geopandas as gpd
import pandas as pd
import os, sys

MAPS_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))

shp_file = os.path.join(MAPS_DIR, "mex_admbnda_govmex_20210618_shp/mex_admbnda_govmex_20210618_SHP/mex_admbnda_adm2_govmex_20210618.shp")
df = gpd.read_file(shp_file)[["ADM1_ES", "ADM2_ES", "geometry"]].sort_values(["ADM1_ES", "ADM2_ES"])

print("state\tmunicipality\tlat\tlon")
print(*[f"{state}\t{muni}\t{geo.centroid.y:.4f}\t{geo.centroid.x:.4f}" for state, muni, geo in df[["ADM1_ES", "ADM2_ES", "geometry"]].values], sep="\n")
