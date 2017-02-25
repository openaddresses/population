#!/usr/bin/env python2
from __future__ import print_function, division
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

def main(iso_code):
    '''
    '''
    path = os.path.dirname(__file__)
    countries_path = os.path.join(path, '..', 'data', 'ne_50m_admin_0_countries.geojson.gz')
    gridded_path = os.path.join(path, '..', 'data', 'gpwv4-2015-1deg.geojson.gz')
    counts_path = os.path.join(path, '..', 'data', 'OA-counts.geojson.gz')
    
    country_feature = filter(lambda f: f['properties']['iso_a2'] == iso_code, load_gzipped_geojson(countries_path))[0]
    gridded_features = filter(lambda f: f['properties']['iso_a2'] == iso_code, load_gzipped_geojson(gridded_path))
    counts_features = filter(lambda f: f['properties']['ISO 3166'] == iso_code, load_gzipped_geojson(counts_path))
    
    output_features = []
    
    for grid_feature in gridded_features:
        grid_geometry = grid_feature['geometry'].intersection(country_feature['geometry'])
        count_geoms = list()
        
        for count_feature in counts_features:
            count_geom = count_feature['geometry']
            count_props = count_feature['properties']
            
            if not count_geom.intersects(grid_geometry):
                continue
            
            if 'Polygon' in count_geom.type:
                count_subgeom = count_geom.intersection(grid_geometry)
                count_geoms.append(count_subgeom)
            
            elif count_geom.type is 'Point':
                pass
            else:
                pass
    
        output_feature = dict(type='Feature')
        output_feature.update(properties={
            'iso_a2': iso_code,
            'population': float(grid_feature['properties']['population']),
            'area': float(grid_feature['properties']['area']),
            
            # land area covered by OA
            'address area': 0,
            
            # population covered by OA
            'address population': 0
            })
        
        if count_geoms:
            grid_count_geom = reduce(dissolve, count_geoms)
            output_feature.update(geometry=shapely.geometry.mapping(grid_count_geom))
            
            area_fraction = grid_count_geom.area / grid_geometry.area

            output_feature['properties']['address area'] \
                = area_fraction * output_feature['properties']['area']

            output_feature['properties']['address population'] \
                = area_fraction * output_feature['properties']['population']

        output_features.append(output_feature)
    
    total_pop = sum([F['properties']['population'] for F in output_features])
    addr_pop = sum([F['properties']['address population'] for F in output_features])
    total_area = sum([F['properties']['area'] for F in output_features])
    addr_area = sum([F['properties']['address area'] for F in output_features])
    
    summary = {
        'total population': total_pop,
        'total area': total_area,
        'address population': addr_pop,
        'address area': addr_area,
        'population percent': (100 * addr_pop / total_pop),
        'area percent': (100 * addr_area / total_area),
        }
    
    print(json.dumps(summary, indent=2), file=sys.stderr)
    
    output_geojson = dict(type='FeatureCollection', features=output_features)
    output_geojson.update(summary=summary)
    json.dump(output_geojson, sys.stdout)

if __name__ == '__main__':
    _, iso_code = sys.argv
    exit(main(iso_code))