import pulp
from matplotlib import pyplot as plt
import pandas as pd
import geopandas as gpd
import numpy as np
from src import func1 as f1
from shapely.geometry import Point
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 


pd.set_option('display.max_columns', 30)
pd.set_option('display.max_rows', 100000000)

# pd.reset_option('display.max_columns')




use_state = 'Utah'
dist_thresh = 30


# Prepare the Provider Data
# Load the Data
provider_data = f1.load_provider_data()
zip_geo_data = f1.load_zip_geo_data()
zip_geo_data = zip_geo_data.drop(columns=['GEOID20', 'MTFCC20', 'FUNCSTAT20', 'ALAND20', 'AWATER20', 'INTPTLAT20', 'INTPTLON20', 'CLASSFP20'])

#Prepare the provider data
provider_data = f1.filter_out_states(provider_data, use_state, True)
provider_data = provider_data.drop(columns=['NPI', 'MEDICARE ID EFFECTIVE DATE', 'PHONE'])
provider_data['PROVIDER CAPACITY'] = 225
provider_data.rename(columns={'ZIP':'PROVIDER ZIP', 'ADDRESS LINE 1':'PROVIDER ADDRESS LINE 1', 
                    'ADDRESS LINE 2':'PROVIDER ADDRESS LINE 2', 'CITY':'PROVIDER CITY', 'STATE':'PROVIDER STATE'}, inplace=True)

# Combine provider with geo
provider_data = provider_data.join(zip_geo_data.set_index('ZIP'), on='PROVIDER ZIP', how='left')
provider_data = provider_data.rename(columns={'geometry':'provider geometry'})
provider_data = provider_data.set_geometry('provider geometry').set_crs('EPSG:4269') 
provider_data['PROVIDER CENTERS'] = provider_data.to_crs('ESRI:102008').centroid.values
provider_data['NUM PROVIDERS'] = 1


unique_zips = provider_data['PROVIDER ZIP']

for val in unique_zips:
    mask = provider_data['PROVIDER ZIP'] == val
    zip_provider = provider_data[mask]
    if len(zip_provider) > 1:
        zip_capacity = zip_provider['PROVIDER CAPACITY'].sum()

        for i, entry in enumerate(zip_provider.iterrows()):
            entry_index = entry[0]
            entry = entry[1]
            if i == 0:
                provider_data.loc[entry_index, 'PROVIDER CAPACITY'] = zip_capacity
                provider_data.loc[entry_index, 'NUM PROVIDERS'] = len(zip_provider)
                keep_index = entry_index
            
            else:
                provider_data.drop(index=entry_index, inplace=True)
                provider_data.loc[keep_index, 'PROVIDER ADDRESS LINE 1'] = provider_data.loc[keep_index, 'PROVIDER ADDRESS LINE 1'] + '/' + entry['PROVIDER ADDRESS LINE 1']
                provider_data.loc[keep_index, 'PROVIDER ADDRESS LINE 2'] = provider_data.loc[keep_index, 'PROVIDER ADDRESS LINE 2'] + '/' + entry['PROVIDER ADDRESS LINE 2']
                provider_data.loc[keep_index, 'PROVIDER NAME'] = provider_data.loc[keep_index, 'PROVIDER NAME'] + '/' + entry['PROVIDER NAME']

#Add dummy provider
dummy_provider = provider_data.iloc[[0]].copy()
dummy_provider['PROVIDER ZIP'] = '-1'
dummy_provider['PROVIDER ADDRESS LINE 1'] = 'DUMMY'
dummy_provider['PROVIDER ADDRESS LINE 2'] = 'DUMMY'
dummy_provider['PROVIDER STATE'] = 'DUMMY'
dummy_provider['PROVIDER CITY'] = 'DUMMY'
dummy_provider['PROVIDER NAME'] = 'DUMMY'
dummy_provider['PROVIDER CAPACITY'] = 99999999
dummy_provider['provider geometry'] = 'Dummy'
dummy_provider['PROVIDER CENTERS'] = Point(0,0)
dummy_provider['NUM PROVIDERS'] = 1

provider_data = pd.concat([provider_data, dummy_provider])


# provider_data = provider_data.join(zip_geo_data.set_index('ZIP'), on='PROVIDER ZIP', how='left')
# provider_data = provider_data.rename(columns={'geometry':'provider geometry'})
# provider_data = provider_data.set_geometry('provider geometry').set_crs('EPSG:4269') 
# provider_data['PROVIDER CENTERS'] = provider_data.to_crs('ESRI:102008').centroid.values[0]

# Prepare the Rates Data
# state_geo_data = f1.load_states_geo_data()
rates_data = f1.load_rates_data()
rates_data = f1.filter_out_states(rates_data, use_state, True)
rates_data = rates_data[['ZIP', 'Tot_Opioid_Prscrbrs', 'Tot_Opioid_Clms', 'MedPop']]
rates_data = rates_data.rename(columns={'ZIP':'RATES ZIP'})
rates_data['Estimate_Need_Care'] = rates_data['MedPop'] * .08
rates_data = rates_data.dropna(axis=0, subset=['MedPop'])
rates_data['Estimate_Need_Care'] = rates_data['Estimate_Need_Care'].astype(int)
rates_data = rates_data.join(zip_geo_data.set_index('ZIP'), on='RATES ZIP', how='left')
rates_data = rates_data.rename(columns={'geometry':'rates geometry'})
rates_data = rates_data.set_geometry('rates geometry').set_crs('EPSG:4269')
rates_data['RATES CENTERS'] = rates_data.to_crs('ESRI:102008').centroid.values



# Need to get the distance for all of these
rates_data['const'] = 1
provider_data['const'] = 1
merged = pd.merge(rates_data, provider_data, on='const')

merged.set_index(['RATES ZIP', 'PROVIDER ZIP'], inplace=True) 

distances = gpd.GeoSeries(merged['RATES CENTERS']).distance(gpd.GeoSeries(merged['PROVIDER CENTERS']), align=False)
merged['dist'] = distances * 0.000621

merged.loc[merged.xs('-1', level='PROVIDER ZIP', drop_level=False).index, 'dist'] = 0

merged = merged[merged['dist'] <= dist_thresh].copy()

# Put a condition to deal with when they have multiple providers in one zip. this could be done be adding capacity to the other and deleting one


merged.loc[merged.xs('-1', level='PROVIDER ZIP', drop_level=False).index, 'dist'] = 99999
rates_zip = rates_data['RATES ZIP']
providers_zip = provider_data['PROVIDER ZIP']

D = pulp.LpVariable.dicts('DA', merged.index.tolist(), lowBound=0, upBound=int(provider_data['PROVIDER CAPACITY'].max()), cat=pulp.LpInteger)
P = pulp.LpProblem('minDist', pulp.LpMinimize)
# print('1')
# print(D[merged.index[0]])
# print('2')
# print(merged.loc[merged.index[0],'dist'])
# print(type(merged.loc[merged.index[0],'dist']))
# print(merged.loc[merged.index[0],'dist'].values[0])


# print('3')
# print(D[merged.index[0]] * merged.loc[merged.index[0], 'dist'].values[0])
# P += pulp.lpSum(D[i]*merged.loc[i, 'dist'].values[0] for i in merged.index)
P += pulp.lpSum(D[i]*merged.loc[i, 'dist'] for i in merged.index)


# print(P)
for p in rates_data['RATES ZIP']:
    provl = merged.xs(p, 0, drop_level=False)
    ptot = provl['Estimate_Need_Care'].iloc[0]
    P += pulp.lpSum(D[i] for i in provl.index) == ptot, f"pers_{p}"
# print(P)

for h in provider_data['PROVIDER ZIP']:
    peopl = merged.xs(h, level=1, drop_level=False)
    pid = peopl.index
    cap = peopl['PROVIDER CAPACITY'].iloc[0]
    # print('peopl')
    # print(peopl)
    # print('cap')
    # print(cap)
    # print('pid')
    # print(pid)
    P += pulp.lpSum(D[i] for i in pid) <= cap, f"prov_{h}"
    # print('P')
    # print(P)
    # raise Exception


# 84770
print('solved')
print()
print()

# Solve the model
P.solve(pulp.PULP_CBC_CMD()) 
# CPLEX or CBC only ones I know of that return shadow
print(pulp.value(P.objective)) #print objective 20024.33502494309


# Get the person distances
res_pick = []
for ph in merged.index:
    res_pick.append(D[ph].varValue)

merged['picked'] = res_pick
# print(merged[merged['picked'] > 0.99][['picked', 'Estimate_Need_Care', 'MedPop', 'dist']])
# print(merged[['picked', 'Estimate_Need_Care', 'MedPop', 'dist']])
print(merged[merged['picked'] > 0.99])
print(merged)
