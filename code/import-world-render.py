#!/usr/bin/env python2
''' Populate Postgres areas table with latest coverage data from OpenAddresses.
'''
from __future__ import print_function, division
from urlparse import urljoin
from osgeo import ogr
import psycopg2, tempfile
import sys, json, os
import requests

is_point = lambda geom: bool(geom.GetGeometryType() in (ogr.wkbPoint, ogr.wkbMultiPoint))
is_polygon = lambda geom: bool(geom.GetGeometryType() in (ogr.wkbPolygon, ogr.wkbMultiPolygon))

def validate_geometry(geometry):
    '''
    '''
    if is_point(geometry):
        # Points are easy, we love points
        return geometry

    elif is_polygon(geometry):
        # Polygons may be invalid
        if geometry.IsValid():
            return geometry
        else:
            # Buffer by a tiny amount to force validity
            return geometry.Buffer(0.00000001, 2)

    else:
        # Don't know what to do with other geometry types, so ignore them
        return None

def guess_iso_a2(feature):
    '''
    '''
    iso_a2 = None

    if feature.GetField('ISO 3166'):
        # Read directly from ISO 3166 field
        iso_a2 = feature.GetField('ISO 3166')

    elif feature.GetField('ISO 3166-2'):
        # Read from first half of dash-delimited ISO 3166-2 field
        iso_a2, _ = feature.GetField('ISO 3166-2').split('-', 2)

    elif feature.GetField('US Census GEOID'):
        # Assume US based on Census GEOID
        iso_a2 = 'US'

    elif feature.GetField('source paths'):
        # Read from paths, like "sources/xx/place.json"
        paths = feature.GetField('source paths')
        _, iso_a2, _ = paths.upper().split(os.path.sep, 2)

    return iso_a2

start_url = 'https://results.openaddresses.io/index.json'
index = requests.get(start_url).json()
geojson_url = urljoin(start_url, index['render_geojson_url'])
print('Downloading', geojson_url, '...', file=sys.stderr)

handle, filename = tempfile.mkstemp(prefix='render_geojson-', suffix='.geojson')
geojson = os.write(handle, requests.get(geojson_url).content)
os.close(handle)

with psycopg2.connect('postgres://localhost/oa_population') as conn:
    with conn.cursor() as db:

        ogr.UseExceptions()
        rendered_ds = ogr.Open(filename)

        db.execute('''
            CREATE TEMPORARY TABLE rendered_world
            (
                iso_a2  VARCHAR(2),
                count   INTEGER,
                geom    GEOMETRY(MultiPolygon, 4326)
            );
            ''')

        for feature in rendered_ds.GetLayer(0):
            geom = validate_geometry(feature.GetGeometryRef())
            iso_a2 = guess_iso_a2(feature)
    
            if not geom:
                continue
            
            print(geom.GetGeometryType(), iso_a2, feature.GetField('address count'), feature.GetField('source count'), feature.GetField('source paths'))
            
            if is_point(geom):
                # Ask PostGIS to buffer points by 10km, as a reasonable city size
                db.execute('SELECT ST_AsText(ST_Buffer(%s::geography, 10000))', (geom.ExportToWkt(), ))
                (geom_wkt, ) = db.fetchone()
            else:
                geom_wkt = geom.ExportToWkt()
            
            db.execute('''INSERT INTO rendered_world (iso_a2, count, geom)
                          VALUES(%s, %s, ST_Multi(ST_SetSRID(%s::geometry, 4326)))''',
                       (iso_a2, feature.GetField('address count'), geom_wkt))
        
        db.execute('''
            TRUNCATE areas;
            
            INSERT INTO areas (iso_a2, addr_count, buffer_km, geom)
            SELECT iso_a2, SUM(count), 10, ST_Multi(ST_Union(geom))
            FROM rendered_world GROUP BY iso_a2;
            ''')

os.remove(filename)
