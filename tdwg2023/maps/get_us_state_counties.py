import geopandas as gpd
import pandas as pd
import os, sys

MAPS_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))

state_shp_file = os.path.join(MAPS_DIR, "tl_2022_us_state/tl_2022_us_state.shp")
county_shp_file = os.path.join(MAPS_DIR, "tl_2022_us_county/tl_2022_us_county.shp")

def get_continental_statefp_name_map(path_to_states_shp):
    states_df = gpd.read_file(path_to_states_shp)
    non_continental = ['HI','VI','MP','GU','AK','AS','PR']
    us48 = states_df.loc[~states_df["STUSPS"].isin(non_continental)]
    return {fp: name for fp, name in us48[["STATEFP", "NAME"]].values}

continental_fp_names = get_continental_statefp_name_map(state_shp_file)

def get_continental_counties(statefps, path_to_counties_shp):
    df = gpd.read_file(path_to_counties_shp)
    return df.loc[df["STATEFP"].isin(statefps)]

raw_df = get_continental_counties(continental_fp_names.keys(), county_shp_file)

df = pd.DataFrame({
    "state": raw_df["STATEFP"].apply(lambda x: continental_fp_names[x]),
    "county": raw_df["NAMELSAD"],
    "lat": pd.to_numeric(raw_df["INTPTLAT"]),
    "lon": pd.to_numeric(raw_df["INTPTLON"])
}).sort_values(["state", "county"])

print("state\tcounty\tlat\tlon")
print(*[f"{state}\t{county}\t{lat:.4f}\t{lon:.4f}" for state, county, lat, lon in df.values], sep="\n")
