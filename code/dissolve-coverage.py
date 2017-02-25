#!/usr/bin/env python2
from __future__ import print_function
import sys, json, itertools, shapely.geometry, operator

def dissolve(geometry1, geometry2):
    '''
    '''
    try:
        return geometry1.union(geometry2)
    except:
        if geometry2.is_valid and not geometry1.is_valid:
            return geometry2
        if geometry1.is_valid and not geometry2.is_valid:
            return geometry1
        raise

def main():
    '''
    '''
    input_geojson = json.load(sys.stdin)
    key = lambda F: (F['properties']['ISO 3166'], F['geometry']['type'].replace('Multi', ''))
    iso_groups = itertools.groupby(sorted(input_geojson['features'], key=key), key=key)
    output_geojson = dict(type='FeatureCollection', features=[])
    
    for ((iso_a2, geom_type), iso_features) in iso_groups:
        feature_list = list(iso_features)
        
        try:
            counts = [feature['properties']['address count']
                      for feature in feature_list]

            geometries = [shapely.geometry.shape(feature['geometry'])
                          for feature in feature_list]

            count = reduce(operator.add, counts)
            geometry = reduce(dissolve, geometries)
        except:
            print('Skipping', iso_a2, file=sys.stderr)
            continue
        
        print(iso_a2, geom_type, '-', len(feature_list), 'features', count, 'addresses', file=sys.stderr)
        
        output_feature = dict(type='Feature', geometry=shapely.geometry.mapping(geometry))
        output_feature.update(properties={'ISO 3166': iso_a2, 'address count': count})
        output_geojson['features'].append(output_feature)
    
    json.dump(output_geojson, sys.stdout)

if __name__ == '__main__':
    exit(main())
