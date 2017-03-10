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
        
        db.execute('''CREATE INDEX world_summaries_boxes ON world_summaries (size, lon, lat)''')
        
        for (index, iso_a2) in enumerate(sorted(iso_a2s)):
            print('Counting up {} ({}/{})...'.format(iso_a2, index+1, len(iso_a2s)), file=sys.stderr)
