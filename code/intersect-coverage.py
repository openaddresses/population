#!/usr/bin/env python2
from __future__ import print_function
import os, sys, gzip, csv, shapely.geometry, json, itertools

def load_gzipped_geojson(path):
    '''
    '''
    features = list()
    
    with gzip.open(path) as file:
        geojson = json.load(file)
        
        for (index, feature) in enumerate(geojson['features']):
            geometry = shapely.geometry.shape(feature['geometry'])
            
            if not geometry.is_valid:
                print('Bad geometry in', path, 'feature', index, file=sys.stderr)
            else:
                feature['geometry'] = geometry
                features.append(feature)
    
    print(path, '-', feature['properties'])
    return features

def main():
    '''
    '''
    path = os.path.dirname(__file__)
    gridded_path = os.path.join(path, '..', 'data', 'gpwv4-2015-1deg.geojson.gz')
    counts_path = os.path.join(path, '..', 'data', 'OA-counts.geojson.gz')
    
    gridded_features = load_gzipped_geojson(gridded_path)
    counts_features = load_gzipped_geojson(counts_path)
    
    gridded_iso_key = lambda feature: feature['properties']['iso_a2']
    gridded_iso_features = sorted(gridded_features, key=gridded_iso_key)
    gridded_iso_groups = itertools.groupby(gridded_iso_features, key=gridded_iso_key)
    gridded_iso_lists = {iso: list(Fs) for (iso, Fs) in gridded_iso_groups}
    
    print({key: len(Fs) for (key, Fs) in gridded_iso_lists.items()}, file=sys.stderr)
    
    counts_iso_key = lambda feature: feature['properties']['ISO 3166']
    counts_iso_features = sorted(counts_features, key=counts_iso_key)
    counts_iso_groups = itertools.groupby(counts_iso_features, key=counts_iso_key)
    counts_iso_lists = {iso: list(Fs) for (iso, Fs) in counts_iso_groups}
    
    print({key: len(Fs) for (key, Fs) in counts_iso_lists.items()}, file=sys.stderr)
    
    iso_codes = set(gridded_iso_lists.keys()) & set(counts_iso_lists.keys())
    
    for iso_code in sorted(iso_codes):
        gridded_list = gridded_iso_lists[iso_code]
        counts_list = counts_iso_lists[iso_code]
        print(iso_code, len(gridded_list), len(counts_list), file=sys.stderr)
        
        for (grid_feature, count_feature) in itertools.product(gridded_list, counts_list):
            grid_geom, count_geom = grid_feature['geometry'], count_feature['geometry']
            grid_props, count_props = grid_feature['properties'], count_feature['properties']
            if not grid_geom.intersects(count_geom):
                continue
            print(grid_props, '&', count_props, file=sys.stderr)

if __name__ == '__main__':
    exit(main())
