import requests
import geopandas as gpd

# provider_URL = 'https://data.cms.gov/provider-characteristics/medicare-provider-supplier-enrollment/opioid-treatment-program-providers/data'
# prescribing_rates = 'https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-opioid-prescribing-rates/medicare-part-d-opioid-prescribing-rates-by-geography/data'
prescribing_rates = 'https://data.cms.gov/data-api/v1/dataset/96a69fe9-d559-4356-bce8-516a46367e1c/data'
provider_URL = 'https://data.cms.gov/data-api/v1/dataset/22e251b7-1e91-46e7-b925-1ef4ce1c419e/data'


response = requests.get(provider_URL)
open('data/provider_data1.json', 'wb').write(response.content)

response = requests.get(prescribing_rates)
open('data/prescribing_rates1.json', 'wb').write(response.content)


zip_codes = gpd.read_file('https://www2.census.gov/geo/tiger/TIGER2019/ZCTA5/tl_2019_us_zcta510.zip')
# print(zip_codes)
zip_codes.to_file('data/zip_geo_data.shp')

states = gpd.read_file('https://www2.census.gov/geo/tiger/TIGER2019/STATE/tl_2019_us_state.zip')
states.to_file('data/states_geo_data.shp')
