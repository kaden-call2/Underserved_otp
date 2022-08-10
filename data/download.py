import requests
import geopandas as gpd
import svi_data

# Code to download the geometric files for the state lines and zip code lines as well as the SVI data.

# zip_codes = gpd.read_file('https://www2.census.gov/geo/tiger/TIGER2019/ZCTA5/tl_2019_us_zcta510.zip')
# zip_codes.to_file('data/zip_geo_data.shp')

# states = gpd.read_file('https://www2.census.gov/geo/tiger/TIGER2019/STATE/tl_2019_us_state.zip')
# states.to_file('data/states_geo_data.shp')


# Need to sign up for your own key
# with open('data/api_key.txt', 'r') as infile:
#     key = infile.read()
key = '329b4aabf603a3aaa2dcd28c248c1c4544d11f58'
# Download the data from census API
svi_zips = svi_data.get_svi(key,'zip',2019)
svi_zips['ZIP'] = svi_zips['GEO_ID'].str[-5:]
open('data/SVI_data.csv', 'wb').write(svi_zips)