from os.path import join, dirname
import csv

def load_ne_country_dicts():
    ''' Return two dictionaries: countries by name, and by ISO code.
    '''
    with open(join(dirname(__file__), 'ne_50m_admin_0_countries-54029.csv')) as file:
        countries = list()
        for row in csv.DictReader(file):
            countries.append({k: v.decode('utf8') for (k, v) in row.items()})
    
    name_countries = {c['name']: c for c in countries}
    iso_a2_countries = {c['iso_a2']: c for c in countries}
    iso_a3_countries = {c['iso_a3']: c for c in countries}
    
    return name_countries, iso_a2_countries, iso_a3_countries
