import pulp
from matplotlib import pyplot as plt
import pandas as pd
import geopandas as gpd
import numpy as np
from zmq import USE_FD
# import func1 as f1
from src import func1 as f1
from shapely.geometry import Point
import warnings
import time
warnings.filterwarnings("ignore", category=DeprecationWarning) 

PERCENT_MEDICAREPOP_NEED_TREATMENT = .05
DUMMY_PROVIDER_DISTANCE = 99999
USE_CMAP = f1.USE_CMAP

pd.set_option('display.max_columns', 30)
pd.set_option('display.max_rows', 100000000)

# pd.reset_option('display.max_columns')


def combine_zips(provider_data):
    unique_zips = provider_data['PROVIDER ZIP']

    for val in unique_zips:
        mask = provider_data['PROVIDER ZIP'] == val
        zip_provider = provider_data[mask]

        # If there are multiple zips then combine them to one entry combining there capacities together and increasing "NUM PROVIDERS".
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
                    # Drop repeated instances of the zip and combine the names so they are still visible.
                    provider_data.drop(index=entry_index, inplace=True)
                    # provider_data.loc[keep_index, 'PROVIDER ADDRESS LINE 1'] = provider_data.loc[keep_index, 'PROVIDER ADDRESS LINE 1'] + '/' + entry['PROVIDER ADDRESS LINE 1']
                    # provider_data.loc[keep_index, 'PROVIDER ADDRESS LINE 2'] = provider_data.loc[keep_index, 'PROVIDER ADDRESS LINE 2'] + '/' + entry['PROVIDER ADDRESS LINE 2']
                    # provider_data.loc[keep_index, 'PROVIDER NAME'] = provider_data.loc[keep_index, 'PROVIDER NAME'] + '/' + entry['PROVIDER NAME']

    return provider_data


def add_dummy_provider(provider_data):
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

    return pd.concat([provider_data, dummy_provider])
    

def prep_provider_data(provider_data, zip_geo_data, state, new_provider_data=None):
    # print(provider_data)
    provider_data = provider_data.copy()
    zip_geo_data = zip_geo_data.copy()

    # TODO: Handle when there is no providers
    
    if len(provider_data) == 0 and new_provider_data is None:
        print('The provider data frame is empty')
        return None

    # Drop columns that are not needed
    zip_geo_data = zip_geo_data.drop(columns=['GEOID20', 'MTFCC20', 'FUNCSTAT20', 'ALAND20', 'AWATER20', 'INTPTLAT20', 'INTPTLON20', 'CLASSFP20'])

    # Filter state
    provider_data = f1.filter_out_states(provider_data, state, True)
    provider_data = provider_data.drop(columns=['NPI', 'MEDICARE ID EFFECTIVE DATE', 'PHONE'])

    # Add a default capacity of 225 (Average of all providers capacity) if it doesn't exist
    if 'PROVIDER CAPACITY' not in provider_data.columns:
        provider_data['PROVIDER CAPACITY'] = 225

    # Rename columns for clarification
    provider_data.rename(columns={'ZIP':'PROVIDER ZIP', 'ADDRESS LINE 1':'PROVIDER ADDRESS LINE 1', 
                        'ADDRESS LINE 2':'PROVIDER ADDRESS LINE 2', 'CITY':'PROVIDER CITY', 'STATE':'PROVIDER STATE'}, inplace=True)

    # Combine provider with geo data and get the zip centers
    provider_data = provider_data.join(zip_geo_data.set_index('ZIP'), on='PROVIDER ZIP', how='left')
    provider_data = provider_data.rename(columns={'geometry':'provider geometry'})
    provider_data = provider_data.set_geometry('provider geometry').set_crs('EPSG:4269') 
    provider_data['PROVIDER CENTERS'] = provider_data.to_crs('ESRI:102008').centroid.values
    provider_data['NUM PROVIDERS'] = 1

    if new_provider_data is not None:
        provider_data = add_new_provider(provider_data, new_provider_data)
    provider_data = combine_zips(provider_data)

    provider_data = add_dummy_provider(provider_data)

    return provider_data


def prep_rates_data(rates_data, zip_geo_data, state):
    # Add in the avg claim per person
    claim_dist = pd.read_csv('data/claim_dist.csv')
    claim_dist['tot_claims'] = claim_dist['TotClaims'] * claim_dist['TotN']
    sums = claim_dist.sum(axis=0)
    average_claim_per_person = sums['tot_claims'] / sums['TotN']

    # rates_data = f1.load_rates_data()
    rates_data = f1.filter_out_states(rates_data, state, True)
    rates_data = rates_data[['ZIP', 'Tot_Opioid_Prscrbrs', 'Tot_Opioid_Clms', 'MedPop']]
    rates_data = rates_data.rename(columns={'ZIP':'RATES ZIP'})
    rates_data['Estimate_Need_Care'] = (rates_data['Tot_Opioid_Clms'] / average_claim_per_person) * PERCENT_MEDICAREPOP_NEED_TREATMENT

    # rates_data['Estimate_Need_Care'] = rates_data['MedPop'] * PERCENT_MEDICAREPOP_NEED_TREATMENT
    # rates_data = rates_data.dropna(axis=0, subset=['MedPop'])
    rates_data = rates_data.dropna(axis=0, subset=['Estimate_Need_Care'])

    rates_data['Estimate_Need_Care'] = rates_data['Estimate_Need_Care'].astype(int)
    rates_data = rates_data.join(zip_geo_data.set_index('ZIP'), on='RATES ZIP', how='left')
    rates_data = rates_data.rename(columns={'geometry':'rates geometry'})

    rates_data = rates_data.set_geometry('rates geometry').set_crs('EPSG:4269')
    rates_data['RATES CENTERS'] = rates_data.to_crs('ESRI:102008').centroid.values

    return rates_data


def merge_and_get_distances(rates_data, provider_data, dist_thresh):
    rates_data['const'] = 1
    provider_data['const'] = 1
    merged = pd.merge(rates_data, provider_data, on='const')
    merged.set_index(['RATES ZIP', 'PROVIDER ZIP'], inplace=True) 

    # Get the distance away in miles
    distances = gpd.GeoSeries(merged['RATES CENTERS']).distance(gpd.GeoSeries(merged['PROVIDER CENTERS']), align=False)
    merged['dist'] = distances * 0.000621

    merged.loc[merged.xs('-1', level='PROVIDER ZIP', drop_level=False).index, 'dist'] = 0

    # Get rid of pairs that are not "dist_thresh" close
    merged = merged[merged['dist'] <= dist_thresh].copy()

    # Set the distance to the dummy provider very far away
    merged.loc[merged.xs('-1', level='PROVIDER ZIP', drop_level=False).index, 'dist'] = DUMMY_PROVIDER_DISTANCE

    return merged


def run_model(provider_data, zip_geo_data, rates_data, state, dist_thresh, plot_unassigned=False, ):

    provider_data = prep_provider_data(provider_data, zip_geo_data, state)
    if provider_data is None:
        return None
    rates_data = prep_rates_data(rates_data, zip_geo_data, state)

    # Need to get the distance for all of these
    merged = merge_and_get_distances(rates_data, provider_data, dist_thresh)

    # rates_zip = ['RATES ZIP']
    # providers_zip = provider_data['PROVIDER ZIP']

    # Create the pulp minimization problem
    D = pulp.LpVariable.dicts('DA', merged.index.tolist(), lowBound=0, upBound=int(provider_data['PROVIDER CAPACITY'].max()), cat=pulp.LpInteger)
    P = pulp.LpProblem('minDist', pulp.LpMinimize)
    P += pulp.lpSum(D[i]*merged.loc[i, 'dist'] for i in merged.index)

    # Add equality constraints. (All people need to go somewhere)
    for p in rates_data['RATES ZIP']:
        provl = merged.xs(p, 0, drop_level=False)
        ptot = provl['Estimate_Need_Care'].iloc[0]
        P += pulp.lpSum(D[i] for i in provl.index) == ptot, f"pers_{p}"

    # Add inequality constraints. (Providers have a max capacity)
    for h in provider_data['PROVIDER ZIP']:
        peopl = merged.xs(h, level=1, drop_level=False)
        pid = peopl.index
        cap = peopl['PROVIDER CAPACITY'].iloc[0]
        P += pulp.lpSum(D[i] for i in pid) <= cap, f"prov_{h}"

    # Solve the model
    P.solve(pulp.PULP_CBC_CMD()) 
    stat = pulp.LpStatus[P.status]
    if stat != 'Optimal':
        print(f"    status is {stat}")
        try:
            objective = pulp.value(P.opjective)
            print(f'    Objective value {objective}, is not optimal')
        except:
            print('Failed to get objective')

    # print(pulp.value(P.objective))


    # Get the person distances
    res_pick = []
    for ph in merged.index:
        res_pick.append(D[ph].varValue)

    merged['picked'] = res_pick
    # print(merged[merged['picked'] > 0.99][['picked', 'Estimate_Need_Care', 'MedPop', 'dist']])

    unassigned = merged[merged['picked'] > 0.99].xs('-1', level=1)
    unassigned = unassigned.set_geometry('rates geometry')

    if plot_unassigned:
        filter_states_geo_data = f1.filter_out_states(f1.load_states_geo_data('data/state_shapes/states_geo_data.shp'), state, False)
        state_boundary_map = filter_states_geo_data.boundary.plot(figsize=(12,9), color='Black', linewidth=.25)
        unassigned.plot(ax=state_boundary_map, column='picked', legend=True, cmap=USE_CMAP)
        plt.title('unassgined: ' + state)
        plt.show()

    return pulp.value(P.objective), merged, unassigned


def add_new_provider(provider_data, new_provider_data):
    if len(provider_data == 0):
        new_provider = provider_data.iloc[[0]].copy()
        new_provider['PROVIDER ZIP'] = new_provider_data['ZIP']
        new_provider['PROVIDER ADDRESS LINE 1'] = 'NEW'
        new_provider['PROVIDER ADDRESS LINE 2'] = 'NEW'
        new_provider['PROVIDER STATE'] = 'NEW'
        new_provider['PROVIDER CITY'] = 'NEW'
        new_provider['PROVIDER NAME'] = 'NEW'
        new_provider['PROVIDER CAPACITY'] = 225
        new_provider['provider geometry'] = new_provider_data['geometry']
        new_provider = new_provider.set_geometry('provider geometry').set_crs('EPSG:4269')
        new_provider['PROVIDER CENTERS'] = new_provider.to_crs('ESRI:102008').centroid.values
        new_provider['NUM PROVIDERS'] = 1
        
        return pd.concat([provider_data, new_provider])
    
    else:

        new_columns = ['PROVIDER NAME', 'PROVIDER ADDRESS LINE 1', 'POVIDER ADDRESS LINE 2','PROVIDER CITY', 
                    'PROVIDER STATE', 'PROVIDER ZIP', 'PROVIDER CAPACITY', 'provider geometry', 'NUM PROVIDERS']
        # new_columns = ['NAME', 'ADDRESS LINE 1', 'ADDRESS LINE 2','CITY', 
        #         'STATE', 'ZIP', 'CAPACITY', 'geometry', 'NUM PROVIDERS']

        
        values = np.array([['NEW', 'NEW', 'NEW', 'NEW', 'NEW', new_provider_data['ZIP'], 225, new_provider_data['geometry'], 1]])

        provider_data = pd.DataFrame(data=values, columns=new_columns)
        provider_data = provider_data.set_geometry('provider geometry').set_crs('EPSG:4269')
        provider_data['PROVIDER CENTERS'] = provider_data.to_crs('ESRI:102008').centroid.values
        
        return provider_data


def find_best_new_provider(provider_data, zip_geo_data, rates_data, state, dist_thresh):
    original_run = run_model(provider_data, zip_geo_data, rates_data, state, dist_thresh, False)
    if original_run is not None:
        original_score, original_df, original_unassigned = original_run
    lowest_score = np.inf
    zip_geo_data = f1.filter_out_states(zip_geo_data, state, True)
    best_zip = None
    keep_merged = None
    keep_unassigned = None
    count= 0
    for zip in zip_geo_data.iterrows():
        update_provider_data = prep_provider_data(provider_data, zip_geo_data, state, zip[1])
        update_rates_data = prep_rates_data(rates_data, zip_geo_data, state)
        merged = merge_and_get_distances(update_rates_data, update_provider_data, dist_thresh)

        # Create the pulp minimization problem
        D = pulp.LpVariable.dicts('DA', merged.index.tolist(), lowBound=0, upBound=int(update_provider_data['PROVIDER CAPACITY'].max()), cat=pulp.LpInteger)
        P = pulp.LpProblem('minDist', pulp.LpMinimize)
        P += pulp.lpSum(D[i]*merged.loc[i, 'dist'] for i in merged.index)

        # Add equality constraints. (All people need to go somewhere)
        for p in update_rates_data['RATES ZIP']:
            provl = merged.xs(p, 0, drop_level=False)
            ptot = provl['Estimate_Need_Care'].iloc[0]
            P += pulp.lpSum(D[i] for i in provl.index) == ptot, f"pers_{p}"

        # Add inequality constraints. (Providers have a max capacity)
        for h in update_provider_data['PROVIDER ZIP']:
            try:
                peopl = merged.xs(h, level=1, drop_level=False)
                pid = peopl.index
                cap = peopl['PROVIDER CAPACITY'].iloc[0]
                P += pulp.lpSum(D[i] for i in pid) <= cap, f"prov_{h}"
            except:
                continue

        # Solve the model
        P.solve(pulp.PULP_CBC_CMD()) 
        stat = pulp.LpStatus[P.status]
        if stat != 'Optimal':
            print(f"    status is {stat}")
            try:
                objective = pulp.value(P.opjective)
                print(f'    Objective value {objective}, is not optimal')
            except:
                print('Failed to get objective')

        # print(pulp.value(P.objective))

        score = pulp.value(P.objective)

        res_pick = []
        for ph in merged.index:
            res_pick.append(D[ph].varValue)

        merged['picked'] = res_pick
        keep_merged = merged.copy()
        unassigned = merged[merged['picked'] > 0.99].xs('-1', level=1)
        unassigned = unassigned.set_geometry('rates geometry')


        score = pulp.value(P.objective)
        if score < lowest_score:
            lowest_score = score
            best_zip = zip
            keep_merged = merged.copy()
            keep_unassigned = unassigned.copy()


    if original_run is not None:
        return best_zip, lowest_score, keep_merged, keep_unassigned, original_score, original_df, original_unassigned

    else:
        return best_zip, lowest_score, keep_merged, keep_unassigned, None, None, None



# state = 'Utah'
# dist_thresh = 30

# provider_data = f1.load_provider_data()
# zip_geo_data = f1.load_zip_geo_data()
# rates_data = f1.load_rates_data()

# # start = time.time()


# # run_model(provider_data, zip_geo_data, rates_data, state, dist_thresh, True)

# best_zip, lowest_score, keep_merged, keep_unassigned, original_score, original_df, original_unassigned = find_best_new_provider(provider_data, zip_geo_data, rates_data, state, dist_thresh)
# print(best_zip)
# # print(time.time() - start)

# # print(best_zip)
# # print(keep_unassigned)

# filter_states_geo_data = f1.filter_out_states(f1.load_states_geo_data(), state, False)
# state_boundary_map = filter_states_geo_data.boundary.plot(figsize=(12,9), color='Black', linewidth=.25)
# keep_unassigned.plot(ax=state_boundary_map, column='picked', legend=True)
# plt.show()



# filter_states_geo_data = f1.filter_out_states(f1.load_states_geo_data(), state, False)
# state_boundary_map = filter_states_geo_data.boundary.plot(figsize=(12,9), color='Black', linewidth=.25)
# original_unassigned.plot(ax=state_boundary_map, column='picked', legend=True)
# plt.show()

