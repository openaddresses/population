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
    
    print(path, '-', feature['properties'], file=sys.stderr)
    return features

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
    path = os.path.dirname(__file__)
    gridded_path = os.path.join(path, '..', 'data', 'gpwv4-2015-1deg.geojson.gz')
    counts_path = os.path.join(path, '..', 'data', 'OA-counts.geojson.gz')
    
    gridded_features = load_gzipped_geojson(gridded_path)
    counts_features = load_gzipped_geojson(counts_path)
    
    gridded_iso_key = lambda feature: feature['properties']['iso_a2']
    gridded_iso_features = sorted(gridded_features, key=gridded_iso_key)
    gridded_iso_groups = itertools.groupby(gridded_iso_features, key=gridded_iso_key)
    gridded_iso_lists = {iso: list(Fs) for (iso, Fs) in gridded_iso_groups}
    
    # gridded_iso_lists is a dict keyed by ISO code, each
    # with a list of 1-degree square features for that country.
    print({key: len(Fs) for (key, Fs) in gridded_iso_lists.items()}, file=sys.stderr)
    
    counts_iso_key = lambda feature: feature['properties']['ISO 3166']
    counts_iso_features = sorted(counts_features, key=counts_iso_key)
    counts_iso_groups = itertools.groupby(counts_iso_features, key=counts_iso_key)
    counts_iso_lists = {iso: list(Fs) for (iso, Fs) in counts_iso_groups}
    
    # counts_iso_lists is a dict keyed by ISO code,
    # each with a list of OA features for that country.
    print({key: len(Fs) for (key, Fs) in counts_iso_lists.items()}, file=sys.stderr)
    
    iso_codes = set(gridded_iso_lists.keys()) & set(counts_iso_lists.keys())
    # iso_codes = ['BR']
    
    total_addresses, output_features = 0, []
    
    for iso_code in sorted(iso_codes):
        country_population, country_address_count = 0, 0
        gridded_list = gridded_iso_lists[iso_code]
        counts_list = counts_iso_lists[iso_code]
        
        for grid_feature in gridded_list:
            grid_count_geoms = []
            grid_source_paths = set()
            grid_addr_count_estimates = []

            grid_geom, grid_props = grid_feature['geometry'], grid_feature['properties']
            country_population += float(grid_props['population'])
        
            for count_feature in counts_list:
                count_geom, count_props = count_feature['geometry'], count_feature['properties']

                if not count_geom.intersects(grid_geom):
                    continue
                
                if 'Polygon' in count_geom.type:
                    grid_count_geom = grid_geom.intersection(count_geom)
                    area_fraction = grid_count_geom.area / count_geom.area
                    addr_count_est = area_fraction * count_props['address count']
                    grid_count_geoms.append(grid_count_geom)

                elif count_geom.type is 'Point':
                    area_fraction = None
                    addr_count_est = count_props['address count']

                else:
                    area_fraction = None
                    addr_count_est = 0
                
                grid_addr_count_estimates.append(addr_count_est)
                grid_source_paths.add(count_props['source paths'])
                
                # print(count_props['source paths'], iso_code, grid_props['lat'], grid_props['lon'],
                #       '-', count_props['address count'], 'in', grid_props['population'],
                #       'and', area_fraction, 'for', addr_count_est,
                #       file=sys.stderr)
            
            if not grid_addr_count_estimates:
                continue
            
            grid_addr_count_estimate = sum(grid_addr_count_estimates)
            
            # print(grid_addr_count_estimate, 'from', len(grid_count_geoms), 'in', grid_source_paths, file=sys.stderr)
            
            output_feature = dict(type='Feature')
            
            if grid_count_geoms:
                grid_count_geom = reduce(dissolve, grid_count_geoms)
                output_feature.update(geometry=shapely.geometry.mapping(grid_count_geom))

            output_feature.update(properties={
                'ISO 3166': iso_code, 'population': grid_props['population'],
                'address count': grid_addr_count_estimate,
                'source paths': ', '.join(grid_source_paths)
                })
            
            output_features.append(output_feature)
            total_addresses += grid_addr_count_estimate
            country_address_count += grid_addr_count_estimate
        
        print(iso_code, '-',
              'Added', int(country_address_count), 'addresses',
              'for', int(country_population), 'people', 
              file=sys.stderr)
    
    output_geojson = dict(type='FeatureCollection', features=output_features)
    json.dump(output_geojson, sys.stdout)
    
    print('Wrote', total_addresses, 'total addresses', file=sys.stderr)

if __name__ == '__main__':
    exit(main())
