#!/usr/bin/env python

import xlrd
import gzip
import csv
import sys

from os.path import dirname, join

def load_ne_country_dicts():
    ''' Return two dictionaries: countries by name, and by ISO code.
    '''
    with open(join(dirname(__file__), 'ne_50m_admin_0_countries-54029.csv')) as file:
        countries = list()
        for row in csv.DictReader(file):
            countries.append({k: v.decode('utf8') for (k, v) in row.items()})
    
    name_countries = {c['name']: c for c in countries}
    iso_a2_countries = {c['iso_a2']: c for c in countries}
    
    return name_countries, iso_a2_countries

def get_row_iso(row, ne_country_name_countries, ne_country_iso_a2_countries):
    '''
    '''
    country = None

    if row['COUNTRY'] in ne_country_name_countries:
        country = ne_country_name_countries[row['COUNTRY']]
    elif row['COUNTRY'] in gecon_iso_a2s:
        if gecon_iso_a2s[row['COUNTRY']] in ne_country_iso_a2_countries:
            country = ne_country_iso_a2_countries[gecon_iso_a2s[row['COUNTRY']]]

    iso_a2 = country and country['iso_a2']
    iso_a3 = country and country['iso_a3']
    
    return iso_a2, iso_a3

if __name__ == '__main__':
    input, output = sys.argv[1:]
    
    ne_country_name_countries, ne_country_iso_a2_countries = load_ne_country_dicts()
    
    with open(join(dirname(__file__), 'NE-missing.csv')) as file:
        gecon_iso_a2s = {r['Name']: r['ISO A2'] for r in csv.DictReader(file)}

    sheet = xlrd.open_workbook(input).sheet_by_index(0)
    
    header = [cell.value for cell in sheet.row(0)]
    fields = ['COUNTRY', 'LAT', 'LONGITUDE', 'AREA', 'POPGPW_2005_40']
    indexes = [header.index(field) for field in fields]
    
    with gzip.GzipFile(output, 'w') as file:
        columns = 'iso_a2', 'iso_a3', 'lat', 'lon', 'year', 'population', 'area'
        output = csv.DictWriter(file, columns)
        output.writerow({c: c for c in columns})
        
        for i in range(1, sheet.nrows):
            row = {f: sheet.row(i)[j].value for (f, j) in zip(fields, indexes)}
            south, west = int(row['LAT']), int(row['LONGITUDE'])
            iso_a2, iso_a3 = get_row_iso(row, ne_country_name_countries, ne_country_iso_a2_countries)
        
            if not iso_a2 or not iso_a3:
                continue
            
            out = dict(iso_a2=iso_a2, iso_a3=iso_a3, lat=south, lon=west,
                       population='{:g}'.format(float(row['POPGPW_2005_40'] or '0')),
                       area='{:g}'.format(float(row['AREA'])), year='2005')
            
            output.writerow(out)
