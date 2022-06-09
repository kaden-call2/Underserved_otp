import pandas as pd
import geopandas as gpd
from matplotlib import pyplot as plt



def clean_provider_zip(zips):
    new_zips = [z[:5] for z in zips]
    return new_zips


def format_rates_zip_codes(zips):
    new_zips = []
    for zip in zips:
        zip = str(zip).split('.')[0]
        while len(zip) < 5:
            zip = '0' + zip
        if len(zip) > 5:
            print(zip)
            raise Exception
        new_zips.append(zip)
    return new_zips

zip_map = {'Samoa': ['96799'], 
            'Mariana': [str(x) for x in list(range(96950, 96953))], 
            'Guam': [str(x) for x in list(range(96910, 96933))], 
            'Virgin_isles': ['00' + x for x in [str(y) for y in list(range(801, 852))]],
            'Alaska': [str(x) for x in list(range(99501, 99951))],
            'Hawaii': [str(x) for x in list(range(96701, 96899))],
            'Puerto Rico': ['00' + x for x in [str(y) for y in list(range(601, 989))]]}

#Read in the zip codes
all_zips = gpd.read_file('https://www2.census.gov/geo/tiger/TIGER2019/ZCTA5/tl_2019_us_zcta510.zip')
# all_zips = gpd.read_file('data/zip_codes.shp')
all_zips = all_zips.rename(columns={'ZCTA5CE10':'ZIP'})


provider_data = pd.read_csv('data/provider_data.csv')
provider_data['ZIP'] = clean_provider_zip(provider_data['ZIP'])

rates_data = pd.read_csv('data/prescribing_rates.csv')
rates_data = rates_data[rates_data['Prscrbr_Geo_Lvl'] == 'ZIP']

def plot_rates():
    rates_year = []  # rates_year contains each individual year 2013-2019. 2013:index0, 2019:index6
    for year in range(2013, 2020):
        rates_year.append(rates_data[rates_data['Year'] == year])
    rates_2019 = rates_year[-1]
    # print(rates_2019['Prscrbr_Geo_Cd'])
    rates_2019['ZIP'] = format_rates_zip_codes(rates_2019['Prscrbr_Geo_Cd'])
    # print(rates_2019['ZIP'])





    #Plot the state outline of the continental US
    states = gpd.read_file('https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_500k.zip')
    #Filter out territories
    invalid_FIPS = ['60', '66', '69', '72', '78', '02', '15']
    Alaska = states.loc[states['STATEFP'] == '02']
    Hawaii = states.loc[states['STATEFP'] == '15']
    states = states[[s not in invalid_FIPS for s in states['STATEFP']]]
    state_boundary_map = states.boundary.plot(figsize=(12,9), color='Black', linewidth=.25)


    pd.set_option('display.max_columns', None)

    #Choose the ones that we don't want to include
    invalid = zip_map['Mariana'] + zip_map['Guam'] + zip_map['Alaska'] + zip_map['Samoa'] + zip_map['Hawaii'] + zip_map['Virgin_isles'] + zip_map['Puerto Rico']
    mask = [z not in invalid for z in all_zips['ZIP']]
    cont_US_zips = all_zips[mask]

    mask = [z not in invalid for z in rates_2019['ZIP']]
    filtered_2019_rates = rates_2019[mask]
    joined = cont_US_zips.join(filtered_2019_rates.set_index(['ZIP'], verify_integrity=True), on=['ZIP'], how='left')
    # print(joined)
    # print(rates_2019['Prscrbr_Geo_Cd'])
    # print(cont_US_zips)
    joined.plot(ax=state_boundary_map, column='Opioid_Prscrbng_Rate', legend=True, cmap='Blues')
    plt.show()



def plot_providers():
    states = gpd.read_file('https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_500k.zip')
    #Filter out territories
    invalid_FIPS = ['60', '66', '69', '72', '78', '02', '15']
    Alaska = states.loc[states['STATEFP'] == '02']
    Hawaii = states.loc[states['STATEFP'] == '15']
    states = states[[s not in invalid_FIPS for s in states['STATEFP']]]
    state_boundary_map = states.boundary.plot(figsize=(12,9), color='Black', linewidth=.25)


    #show zips with a provider
    provider_zips = list(provider_data['ZIP'])
    cont_US_filter = zip_map['Alaska'] + zip_map['Hawaii']
    plot_provider = all_zips[[x in provider_zips and x not in cont_US_filter for x in all_zips['ZIP']]]
    plot_provider.plot(ax=state_boundary_map)
    plt.title('Zip codes that contain an opiod prescriber enrolled in Medicare under the OTP')
    plt.show()

plot_rates()