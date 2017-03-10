#!/usr/bin/env python2
from __future__ import print_function, division
import os, sys, remote, requests, zipfile, csv, psycopg2
from urlparse import urljoin

def stream_summary_files(start_url):
    '''
    '''
    index = requests.get(start_url).json()
    collection_url = urljoin(start_url, index['collections']['global']['sa']['url'])
    print('Downloading', collection_url, '...', file=sys.stderr)

    collection = zipfile.ZipFile(remote.RemoteFileObject(collection_url))
    
    for name in collection.namelist():
        # CSV file paths look like "summary/{iso}/{etc}.csv"
        iso_a2 = os.path.relpath(name, 'summary').split(os.path.sep)[0].upper()
        _, ext = os.path.splitext(name)
        
        if (iso_a2 == '..') or (ext != '.csv'):
            continue # Need a CSV file for the requested ISO code.

        for row in csv.DictReader(collection.open(name)):
            lon, lat = float(row['lon']), float(row['lat'])
            count, geom_wkt = int(row['count']), row['area']

            print(iso_a2, count, 'in', lon, lat)
            yield (iso_a2, count, lon, lat, 0.1)

def summarize_country_coverage(db, iso_a2):
    ''' ????
    '''
    print(iso_a2, '...')
    db.execute('''
        WITH
            --
            -- .1x.1 box IDs of Natural Earth coverage, with GPWv4 population.
            --
            ne_boxes AS (
            SELECT box.id, ne.name, gpw.population
            FROM ne_50m_admin_0_countries as ne, gpwv4_2015 as gpw, boxes as box
            WHERE ne.iso_a2 = %s
              AND ne.iso_a2 = gpw.iso_a2
              AND gpw.box_id = box.id
              AND box.size = 0.1
            ),
            --
            -- .1x.1 boxes of OpenAddresses counts with box IDs.
            --
            oa_boxes AS (
            SELECT box.id, SUM(oa.count) AS count
            FROM world_summaries as oa, gpwv4_2015 as gpw, boxes as box
            WHERE oa.iso_a2 = %s
              AND oa.iso_a2 = gpw.iso_a2
              AND gpw.box_id = box.id
              AND box.lat = oa.lat
              AND box.lon = oa.lon
              AND box.size = oa.size
              AND box.size = 0.1
            GROUP BY box.id
            )
        
        SELECT
            --
            ne_boxes.name,
            min(oa_boxes.count/ne_boxes.population) AS min_cpp,
            avg(oa_boxes.count/ne_boxes.population) AS avg_cpp,
            max(oa_boxes.count/ne_boxes.population) AS max_cpp,
            stddev_pop(oa_boxes.count/ne_boxes.population) AS std_cpp,
            count(oa_boxes.count/ne_boxes.population) AS count_cpp
        FROM oa_boxes LEFT JOIN ne_boxes
        ON ne_boxes.id = oa_boxes.id
        GROUP BY ne_boxes.name
        ''',
        (iso_a2, iso_a2))
    
    print(db.fetchone())
    return
    
    (area_total, pop_total, area_pct, pop_pct, name) = db.fetchone()
    
    db.execute('''UPDATE areas SET name = %s, area_total = %s, area_pct = %s,
                  pop_total = %s, pop_pct = %s WHERE iso_a2 = %s''',
               (name, area_total, area_pct, pop_total, pop_pct, iso_a2))

start_url = 'https://results.openaddresses.io/index.json'

with psycopg2.connect(os.environ['DATABASE_URL']) as conn:
    with conn.cursor() as db:

        iso_a2s = set()

        db.execute('''
            DROP TABLE IF EXISTS world_summaries;

            CREATE TABLE world_summaries
            (
                iso_a2  VARCHAR(2),
                count   INTEGER,
                lon     FLOAT NOT NULL,
                lat     FLOAT NOT NULL,
                size    FLOAT NOT NULL
            );
            ''')

        for (iso_a2, count, lon, lat, size) in stream_summary_files(start_url):
            iso_a2s.add(iso_a2)
            db.execute('''INSERT INTO world_summaries
                          (iso_a2, count, lon, lat, size)
                          VALUES (%s, %s, %s, %s, %s)''',
                       (iso_a2, count, lon, lat, size))
        
        db.execute('''CREATE INDEX world_summaries_countries ON world_summaries (iso_a2)''')
        
        for (index, iso_a2) in [(0, 'IT')]: # enumerate(sorted(iso_a2s)):
            print('Counting up {} ({}/{})...'.format(iso_a2, index+1, len(iso_a2s)), file=sys.stderr)
            summarize_country_coverage(db, iso_a2)
