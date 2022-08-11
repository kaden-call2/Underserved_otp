import geopandas as gpd

# Code to download the geometric files for the state lines and zip code lines

zip_codes = gpd.read_file('https://www2.census.gov/geo/tiger/TIGER2019/ZCTA5/tl_2019_us_zcta510.zip')
zip_codes.to_file('data/zip_shapes/zip_geo_data.shp')

states = gpd.read_file('https://www2.census.gov/geo/tiger/TIGER2019/STATE/tl_2019_us_state.zip')
states.to_file('data/state_shapes/states_geo_data.shp')