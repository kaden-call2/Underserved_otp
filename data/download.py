import geopandas as gpd
import svi_data

# Code to download the geometric files for the state lines and zip code lines as well as the SVI data.

zip_codes = gpd.read_file('https://www2.census.gov/geo/tiger/TIGER2019/ZCTA5/tl_2019_us_zcta510.zip')
zip_codes.to_file('data/zip_shapes/zip_geo_data.shp')

states = gpd.read_file('https://www2.census.gov/geo/tiger/TIGER2019/STATE/tl_2019_us_state.zip')
states.to_file('data/state_shapes/states_geo_data.shp')


# Need to sign up for your own key
with open('data/api_key.txt', 'r') as infile:
    key = infile.read()
# Download the data from census API
svi_zips = svi_data.get_svi(key,'zip',2019)
open('data/ZipData.csv', 'wb').write(svi_zips)