#!/usr/bin/env python2
from __future__ import print_function, division
import sys, os, tarfile, csv, gzip, itertools, json, tempfile, math
import shapely.wkt, shapely.geometry
from os.path import join, dirname

GPWV4_PATH = join(dirname(__file__), '..', 'data', 'gpwv4-2015.csv.gz')
SUMMARIES_PATH = join(dirname(__file__), '..', 'data', 'summaries-2017-03-06.tar.bz2')
BOX_WKT = 'POLYGON (({xmin:.3f} {ymin:.3f}, {xmin:.3f} {ymax:.3f}, {xmax:.3f} {ymax:.3f}, {xmax:.3f} {ymin:.3f}, {xmin:.3f} {ymin:.3f}))'

def get_population_areas(gpwv4_path, iso_code):
    ''' Generate a stream of (population, polygon, area) tuples for a single ISO.
    '''
    with gzip.open(gpwv4_path) as areas:
        for row in csv.DictReader(areas):
            iso_a2, size = row['iso_a2'], row['size']

            if iso_a2.upper() != iso_code.upper():
                continue # Need population for the requested ISO code.
            
            if size != '0.1':
                continue # Want only 0.1 degree areas, to match summary areas.
            
            xmin, ymin = float(row['lon']), float(row['lat'])
            xmax, ymax = xmin + float(size), ymin + float(size)
            poly = shapely.wkt.loads(BOX_WKT.format(**locals()))
            population, area = float(row['population']), float(row['area'])
            
            yield (population, poly, area)

def get_summary_areas(summaries_path, iso_code):
    ''' Generate a stream of (address count, polygon) tuples for a single ISO.
    '''
    with tarfile.open(summaries_path, 'r:bz2') as summaries:
        for member in summaries:
            if not member.isfile():
                continue # Need a file.
            
            # CSV file paths look like "summary/{iso}/{etc}.csv"
            iso_a2 = os.path.relpath(member.name, 'summary').split(os.path.sep)[0]
            _, ext = os.path.splitext(member.name)
            
            if (iso_a2.upper(), ext) != (iso_code.upper(), '.csv'):
                continue # Need a CSV file for the requested ISO code.
            
            for row in csv.DictReader(summaries.extractfile(member)):
                count, poly = int(row['count']), shapely.wkt.loads(row['area'])

                yield (count, poly)

def get_highres_coverage(population_areas, summary_areas):
    ''' Generate a stream of (polygon, area, address count, population, density) tuples.
    
        Join coverage bboxes from population and summary areas.
    '''
    poly_key = lambda poly: poly.bounds[:2]
    summaries_dict = {poly_key(poly): (co, poly) for (co, poly) in summary_areas}
    
    for (population, poly_p, area) in population_areas:
        poly_p_key = poly_key(poly_p)
        if poly_p_key in summaries_dict:
            count, poly_c = summaries_dict[poly_p_key]
            density = count/population if population else None
        
            yield (poly_p, area, count, population, density)

def get_lowres_coverage(highres_coverage):
    ''' Generate a stream of (polygon, area, address count, population, density) tuples.
    
        Group high-res coverage by coverage_key().
    '''
    sorted_coverage = sorted(highres_coverage, key=coverage_key)
    
    for ((xmin, ymin), areas) in itertools.groupby(sorted_coverage, coverage_key):
        poly = containing_poly(xmin, ymin)
        acp_tuples = [(area, count, pop) for (_, area, count, pop, _) in areas]
        area, count, population = map(sum, zip(*acp_tuples))
        density = count/population if population else None
        
        yield (poly, area, count, population, density)

def containing_coord(poly):
    ''' Return integer degrees for coordinate containing this polygon.
    
        E.g. (1.0, 2.0) for polygon covering (1.5, 2.5, 1.6, 2.6).
    '''
    xmin, ymin, _, _ = map(math.floor, poly.bounds)
    return xmin, ymin

def containing_poly(xmin, ymin):
    ''' Return whole-integer polygon for integer coordinates.
    
        E.g. (1, 2, 2, 3) for (1.0, 2.0).
    '''
    xmax, ymax = xmin + 1, ymin + 1
    poly = shapely.wkt.loads(BOX_WKT.format(**locals()))
    return poly

def coverage_key(coverage):
    ''' Return containing coordinate for coverage tuple.
    '''
    poly, _, _, _, _ = coverage
    return containing_coord(poly)

def coverage_feature(poly, area, count, population, density):
    ''' Return GeoJSON feature for coverage tuple values.
    '''
    properties = {'address count': count, 'population': population, 'density': density, 'area': area}
    feature = dict(type='Feature', properties=properties)
    feature.update(geometry=shapely.geometry.mapping(poly))
    return feature

def main(iso_code):
    '''
    '''
    population_areas = get_population_areas(GPWV4_PATH, iso_code)
    summary_areas = get_summary_areas(SUMMARIES_PATH, iso_code)
    highres_coverage = list()
    
    geojson_hi = dict(type='FeatureCollection', features=list())
    geojson_lo = dict(type='FeatureCollection', features=list())
    
    for (poly, km2, co, pop, den) in get_highres_coverage(population_areas, summary_areas):
        print('({0:.1f}, {1:.1f}) has {pop:.0f} people and {co:.0f} addresses in {km2:.0f} km2'.format(*poly.bounds, **locals()), file=sys.stderr)
        geojson_hi['features'].append(coverage_feature(poly, km2, co, pop, den))
        highres_coverage.append((poly, km2, co, pop, den))
    
    for (poly, km2, co, pop, den) in get_lowres_coverage(highres_coverage):
        print('({0:.0f}, {1:.0f}) has {pop:.0f} people and {co:.0f} addresses in {km2:.0f} km2'.format(*poly.bounds, **locals()), file=sys.stderr)
        geojson_lo['features'].append(coverage_feature(poly, km2, co, pop, den))

    dirpath = tempfile.mkdtemp(prefix='mapped-density-{}-'.format(iso_code.lower()), dir='.')
    filename_hi = 'OA-density-{}.geojson'.format(iso_code.lower())
    filename_lo = 'OA-density-{}-1deg.geojson'.format(iso_code.lower())

    with open(join(dirpath, filename_lo), 'w') as file:
        json.dump(geojson_lo, file)
        print(file.name)

    with open(join(dirpath, filename_hi), 'w') as file:
        json.dump(geojson_hi, file)
        print(file.name)

if __name__ == '__main__':
    _, iso_code = sys.argv
    exit(main(iso_code))
