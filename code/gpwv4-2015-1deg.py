#!/usr/bin/env python2
from __future__ import print_function
import sys, json, shapely.geometry, os, csv, gzip

def main():
    '''
    '''
    dir = os.path.dirname(os.path.abspath(__file__))
    geojson = dict(type='FeatureCollection', features=[])

    with gzip.open(os.path.join(dir, '..', 'data/gpwv4-2015.csv.gz')) as file:
        rows = [row for row in csv.DictReader(file) if row['size'] == '1.0']
    
    print(len(rows), file=sys.stderr)
    
    for row in rows:
        xmin, ymin = float(row['lon']), float(row['lat'])
        xmax, ymax = xmin + 1, ymin + 1
        coords = [[[xmin, ymin], [xmin, ymax], [xmax, ymax], [xmax, ymin], [xmin, ymin]]]

        feature = dict(type='Feature', properties=row)
        feature.update(geometry=dict(type='Polygon', coordinates=coords))
        geojson['features'].append(feature)

    json.dump(geojson, sys.stdout)

if __name__ == '__main__':
    exit(main())
