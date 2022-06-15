import pandas as pd
import geopandas as gpd
from matplotlib import pyplot as plt
pd.options.mode.chained_assignment = None


# Map of every state/territory to its range of zip codes
zip_map = {
            'Samoa': ['96799'], 
            'Mariana': [str(x) for x in list(range(96950, 96953))], 
            'Guam': [str(x) for x in list(range(96910, 96933))], 
            'Virgin Islands': ['00' + x for x in [str(y) for y in list(range(801, 852))]],
            'Alaska': [str(x) for x in list(range(99501, 99951))],
            'Hawaii': [str(x) for x in list(range(96701, 96899))],
            'Puerto Rico': ['00' + x for x in [str(y) for y in list(range(601, 989))]],
            'Alabama': [str(x) for x in list(range(35004, 36926))],
            'Arizona': [str(x) for x in list(range(85001, 86557))],
            'Arkansas': [str(x) for x in list(range(71601, 72960))],
            'California': [str(x) for x in list(range(90001, 96162))],
            'Colorado': [str(x) for x in list(range(80001, 81659))],
            'Connecticut': ['0' + x for x in [str(y) for y in list(range(6001, 6929))]],
            'Delaware': [str(x) for x in list(range(19701, 19981))],
            'Florida': [str(x) for x in list(range(32003, 34998))],
            'Georgia': [str(x) for x in list(range(30002, 32000))] + [str(x) for x in list(range(39813, 39902))],
            'Idaho': [str(x) for x in list(range(83201, 83878))],
            'Illinois': [str(x) for x in list(range(60001, 63000))],
            'Indiana': [str(x) for x in list(range(46001, 47998))],
            'Iowa': [str(x) for x in list(range(50001, 52810))],
            'Kansas': [str(x) for x in list(range(66002, 67955))],
            'Kentucky': [str(x) for x in list(range(40003, 42789))],
            'Louisiana': [str(x) for x in list(range(70001, 71498))],
            'Maine': ['0' + x for x in [str(y) for y in list(range(3901, 4993))]],
            'Maryland': [str(x) for x in list(range(20588, 21931))],
            'Massachusetts': ['0' + x for x in [str(y) for y in list(range(1001, 2792))]] + ['5501', '5544'],
            'Michigan': [str(x) for x in list(range(48001, 49972))],
            'Minnesota': [str(x) for x in list(range(55001, 56763))],
            'Mississippi': [str(x) for x in list(range(38601, 39777))],
            'Missouri': [str(x) for x in list(range(63001, 65900))],
            'Montana': [str(x) for x in list(range(59001, 59938))],
            'Nebraska': [str(x) for x in list(range(68001, 69368))],
            'Nevada': [str(x) for x in list(range(88901, 89884))],
            'New Hampshire': ['0' + x for x in [str(y) for y in list(range(3031, 3898))]],
            'New Jersey': ['0' + x for x in [str(y) for y in list(range(7001, 8990))]],
            'New Mexico': [str(x) for x in list(range(87001, 88440))],
            'New York': [str(x) for x in list(range(10001, 14926))] + ['00501', '00544', '06390'],
            'North Carolina': [str(x) for x in list(range(27006, 28910))],
            'North Dakota': [str(x) for x in list(range(58001, 58857))],
            'Ohio': [str(x) for x in list(range(43001, 46000))],
            'Oklahoma': [str(x) for x in list(range(73001, 74967))],
            'Oregon': [str(x) for x in list(range(97001, 97921))],
            'Pennsylvania': [str(x) for x in list(range(15001, 19641))],
            'Rhode Island': ['0' + x for x in [str(y) for y in list(range(2801, 2941))]],
            'South Carolina': [str(x) for x in list(range(29001, 29946))],
            'South Dakota': [str(x) for x in list(range(57001, 57800))],
            'Tennessee': [str(x) for x in list(range(37010, 38590))],
            'Texas': [str(x) for x in list(range(75001, 80000))] + [str(x) for x in list(range(88510, 88595))] + ['73301', '73344', '73960'],
            'Utah': [str(x) for x in list(range(84001, 84792))],
            'Vermont': ['0' + x for x in [str(y) for y in list(range(5001, 5908))]],
            'Virginia': [str(x) for x in list(range(20101, 20599))] + [str(x) for x in list(range(22003, 24659))],
            'Washington': [str(x) for x in list(range(98001, 99404))],
            'West Virginia': [str(x) for x in list(range(24701, 26887))],
            'Wisconsin': [str(x) for x in list(range(53001, 54991))],
            'Wyoming': [str(x) for x in list(range(82001, 83129))] + ['83414'],
            'DC': [str(x) for x in list(range(20001, 20600))] + [str(x) for x in list(range(56901, 57000))]
            }


fips_map = {
    'Washington': '53', 'Delaware': '10', 'DC': '11', 'Wisconsin': '55', 'West Virginia': '54', 'Hawaii': '15',
    'Florida': '12', 'Wyoming': '56', 'New Jersey': '34', 'New Mexico': '35', 'Texas': '48',
    'Louisiana': '22', 'North Carolina': '37', 'North Dakota': '38', 'Nebraska': '31', 'Tennessee': '47', 'New York': '36',
    'Pennsylvania': '42', 'Alaska': '02', 'Nevada': '32', 'New Hampshire': '33', 'Virginia': '51', 'Colorado': '08',
    'California': '06', 'Alabama': '01', 'Arkansas': '05', 'Vermont': '50', 'Illinois': '17', 'Georgia': '13',
    'Indiana': '18', 'Iowa': '19', 'Massachusetts': '25', 'Arizona': '04', 'Idaho': '16', 'Connecticut': '09',
    'Maine': '23', 'Maryland': '24', 'Oklahoma': '40', 'Ohio': '39', 'Utah': '49', 'Missouri': '29',
    'Minnesota': '27', 'Michigan': '26', 'Rhode Island': '44', 'Kansas': '20', 'Montana': '30', 'Mississippi': '28',
    'South Carolina': '45', 'Kentucky': '21', 'Oregon': '41', 'South Dakota': '46', 'Puerto Rico': '72', 
    'Samoa': '60', 'Virgin Islands': '78', 'Guam': '66', 'Mariana': '69'
}
territory_names = ['Puerto Rico', 'Samoa', 'Virgin Islands', 'Guam', 'Mariana']

all_states = [
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware',
    'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky',
    'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri',
    'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
    'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island',
    'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia',
    'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'
]

# all_states = [
#     'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia',
#     'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'
# ]



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


def filter_out_territories(data_orig, using_zips):
    data = data_orig.copy()
    filter = []
    mask = None
    if using_zips:
        for territory in territory_names:
            filter += zip_map[territory]
        mask = [z not in filter for z in data['ZIP']]

    else: 
        for territory in territory_names:
            filter.append(fips_map[territory])
        mask = [s not in filter for s in data['STATEFP']]
    return data[mask]


def filter_out_states(data_orig, states, using_zips):
    if type(states) == str:
        states = [states]
    data = data_orig.copy()
    if states[0] == 'None':
        return
    mask = None
    filter = []
    if using_zips:
        if states[0] == 'Continental':
            filter = [zip_map['Alaska'], zip_map['Hawaii']]
            mask = [s not in filter for s in data['ZIP']]

        else:
            for state in states:
                filter += zip_map[state]
            mask = [s in filter for s in data['ZIP']]

    else:
        if states[0] == 'Continental':
            filter = [fips_map['Alaska'], fips_map['Hawaii']]
            mask = [s not in filter for s in data['STATEFP']]

        else:
            for state in states:
                filter.append(fips_map[state])
            mask = [s in filter for s in data['STATEFP']]

    return data[mask]


def get_dist_from_provider(zip):
    provider_with_geo = provider_data.join(zip_geo_data.set_index(['ZIP'], verify_integrity=True), on=['ZIP'], how='left')
    provider_with_geo = provider_with_geo.set_geometry(provider_with_geo['geometry'])
    provider_with_geo = provider_with_geo.to_crs('ESRI:102008')
    provider_with_geo = filter_out_states(provider_with_geo, 'Utah', True)
    center = provider_with_geo['geometry'].centroid
    test_p = provider_with_geo.plot()
    center.plot(ax=test_p, color='orange')
    plt.show()



# Read in the zip codes
zip_geo_data = gpd.read_file('https://www2.census.gov/geo/tiger/TIGER2019/ZCTA5/tl_2019_us_zcta510.zip')
zip_geo_data = zip_geo_data.rename(columns={'ZCTA5CE10':'ZIP'})
# zip_geo_data = zip_geo_data.to_crs('ESRI:102008')

provider_data = pd.read_csv('data/provider_data.csv')
provider_data['ZIP'] = clean_provider_zip(provider_data['ZIP'])

rates_data = pd.read_csv('data/prescribing_rates.csv')
rates_data = rates_data[rates_data['Prscrbr_Geo_Lvl'] == 'ZIP']


# rates_year contains each individual year 2013-2019. 2013:index0, 2019:index6
rates_year = []
for year in range(2013, 2020):
    year_data = rates_data[rates_data['Year'] == year]
    year_data['ZIP'] = format_rates_zip_codes(year_data['Prscrbr_Geo_Cd'])
    rates_year.append(year_data)
rates_2019 = filter_out_territories(rates_year[-1], True)

states_geo_data = gpd.read_file('https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_500k.zip')
states_geo_data = filter_out_territories(states_geo_data, False)
# states_geo_data = states_geo_data.to_crs('ESRI:102008')



def plot_rates(plot_states='None'):
    # year_rates_data = rates_year[-1]
    year_rates_data = rates_2019

    #Filter out territories and states out of the state outlines
    filter_states_geo_data = filter_out_territories(states_geo_data, False)
    filter_states_geo_data = filter_out_states(filter_states_geo_data, plot_states, False)
    state_boundary_map = filter_states_geo_data.boundary.plot(figsize=(12,9), color='Black', linewidth=.25)
    

    #Filter out territories and states out of the zip outlines and zip data
    filter_zip_geo_data = filter_out_territories(zip_geo_data, True)
    filter_zip_geo_data = filter_out_states(filter_zip_geo_data, plot_states, True)

    filter_year_rates_data = filter_out_territories(year_rates_data, True)
    filter_year_rates_data = filter_out_states(filter_year_rates_data, plot_states, True)

    #Join zip outlines and data
    joined = filter_zip_geo_data.join(filter_year_rates_data.set_index(['ZIP'], verify_integrity=True), on=['ZIP'], how='left')
    
    joined['Tot_Opioid_Clms'] = joined['Tot_Opioid_Clms'].fillna('-1')
    new_col = []
    for entry in joined['Tot_Opioid_Clms']:
        new_col.append(entry.replace(',', ''))
    joined['Tot_Opioid_Clms'] = new_col
    joined['Tot_Opioid_Clms'] = joined['Tot_Opioid_Clms'].astype('int')

    joined_nan = joined[[x == -1 for x in joined['Tot_Opioid_Clms']]]
    joined_not_nan = joined[[x != -1 for x in joined['Tot_Opioid_Clms']]]
    joined_nan.plot(ax=state_boundary_map, color='w')
    
    joined_not_nan.plot(ax=state_boundary_map, column='Tot_Opioid_Clms', legend=True)
    plt.title('Opiod prescriptions')
    plt.show()


def plot_providers(plot_states='None'):
    #Filter out territories
    filter_states_geo_data = filter_out_states(states_geo_data, plot_states, False)
    state_boundary_map = filter_states_geo_data.boundary.plot(figsize=(12,9), color='Black', linewidth=.25)

    # Plot the ZIP lines
    plot_zip_boundaries = filter_out_states(zip_geo_data, plot_states, True)
    plot_zip_boundaries.boundary.plot(ax=state_boundary_map, color='Black', linewidth=.25, alpha=.3)
    # filter_states_geo_data.apply(lambda x: state_boundary_map.annotate(text=x['ZIP'], xy=x.geometry.centroid.coords[0], ha='center'), axis=1)
    
    # Plot the ZIP's that have a provider
    filter_providers = filter_out_states(provider_data, plot_states, True)
    filter_provider_zips = list(filter_providers['ZIP'])
    if len(filter_provider_zips) != 0:
        plot_providers = zip_geo_data[[x in filter_provider_zips for x in zip_geo_data['ZIP']]]
    plot_providers.plot(ax=state_boundary_map)


    plt.title('Zip codes that contain an OTP enrolled in Medicare')
    plt.show()


# all_s = 'Utah'
# plot_providers(all_s)
# for st in all_states:
#     plot_rates(st)
get_dist_from_provider('Utah')
# plot_providers('Continental')