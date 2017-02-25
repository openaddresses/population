#!/usr/bin/env python2
from __future__ import print_function
import csv, json, requests, urlparse, io, sys, json, os

def main():
    '''
    '''
    url = 'https://results.openaddresses.io/index.json'
    data = requests.get(url).json()
    
    state_url = urlparse.urljoin(url, data['run_states_url'])
    geojson_url = urlparse.urljoin(url, data['render_geojson_url'])
    
    print('Getting', state_url, file=sys.stderr)
    got_state = requests.get(state_url)
    state_rows = csv.DictReader(io.BytesIO(got_state.content), dialect='excel-tab')
    
    address_counts = {os.path.join('sources', row['source']).decode('utf8'): int(row['address count'])
                      for row in state_rows if row['address count']}
    
    iso_a2_codes = {key: key.split(os.path.sep)[1].upper() for key in address_counts}
    
    print('Got', len(list(address_counts)), 'address counts', file=sys.stderr)
    assert 'sources/us/ca/berkeley.json' in address_counts
    
    print('Getting', geojson_url, file=sys.stderr)
    got_geojson = requests.get(geojson_url)
    geojson = json.loads(got_geojson.content)
    
    print('Got', len(geojson['features']), 'features', file=sys.stderr)
    
    for feature in geojson['features']:
        paths = feature['properties']['source paths'].split(', ')
        counts = [address_counts[path] for path in paths]
        iso_3166 = iso_a2_codes[paths[0]]

        print('paths:', feature['properties']['source paths'], 'ISO:', iso_3166, 'count:', sum(counts), file=sys.stderr)
        feature['properties']['address count'] = sum(counts)
        feature['properties']['ISO 3166'] = iso_3166
    
    json.dump(geojson, sys.stdout)

if __name__ == '__main__':
    exit(main())
