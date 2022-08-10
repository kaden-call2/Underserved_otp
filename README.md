# Underserved_otp

Data links
rates - https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-opioid-prescribing-rates/medicare-part-d-opioid-prescribing-rates-by-geography/data
prescriber  - https://data.cms.gov/provider-characteristics/medicare-provider-supplier-enrollment/opioid-treatment-program-providers/data



Set up your python project in your repo:

 - requirements.txt
   - only include libraries you need, e.g. pandas (prob geopandas as well), others??
 - create conda environment

 - work on code to automate downloading of the data, and save locally, e.g. you may have the structure
 
root
 main.py [or can use jupyter for final analysis]
 /data
   - download.py [downloads the data in the data folder]
 /src
   - func1.py [local functions for analysis, will point to
               data downloaded in /data folder]

 - Create an outline for the project steps, e.g. something like:
   - Geocode registry data
   - create choropleth map prescriptions
   - create pin map providers, etc.
   - calculate distance to nearest for each census tract
   etc.



Next
    - Find data to nomalize and implement it
    x Add marker for locations of a provider on distance map
    - Make distance map interactive? hover will show you prescription number, zip code, distance to provider, population on medicare
    - add a interactive part to provider to show how many prescriptions where that is the nearest provider

    - Fix the continental US filter
