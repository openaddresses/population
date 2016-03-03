#!/usr/bin/env python

from __future__ import division

from osgeo import gdal
import numpy
import math
import gzip
import csv
import sys
import util

def iterate_squares(ds, size):
    '''
    '''
    xoff, xstride, _, yoff, _, ystride = ds.GetGeoTransform()
    
    xmin, ymax = xoff, yoff
    xmax = xoff + ds.RasterXSize * xstride
    ymin = yoff + ds.RasterYSize * ystride
    
    x = xmin
    while x < xmax:
        print >> sys.stderr, 'lon:', x
        y = ymin
        while y < ymax:
            left = round((x - xoff) / xstride)
            top = round((y + size - yoff) / ystride)
            width, height = round(size / xstride), round(size / -ystride)

            yield (round(x, 2), round(y, 2), int(left), int(top), int(width), int(height))
        
            y += size
        x += size

def hscale(degrees):
    return math.cos(degrees * math.pi / 180)

_arrays = dict()

def make_area_array(south, size, cols, rows):
    ''' Return array filled with sq. km values.
    '''
    if (south, size, cols, rows) in _arrays:
        return _arrays[(south, size, cols, rows)]

    north = south + size
    height_km = (size / rows) * math.pi * 6378.137 / 180
    array = numpy.zeros((rows, cols))
    
    for row in range(rows):
        lat = north - size * (row / rows)
        aspect = cols / rows
        area_km = height_km * height_km * aspect * hscale(lat)
        array[row,:] = area_km
    
    _arrays[(south, size, cols, rows)] = array
    return array

if __name__ == '__main__':
    
    gpwv4, gluntlbnds, gluntlbnds_ids, output = sys.argv[1:]
    
    _, _, ne_country_iso_a3_countries = util.load_ne_country_dicts()
    
    with open(gluntlbnds_ids) as file:
        ids_rows = csv.DictReader(file)
        ids_lookup = {int(r['VALUE']): r['ISO3V10'] for r in ids_rows}

    ds_ids = gdal.Open(gluntlbnds)
    ids_band = ds_ids.GetRasterBand(1)

    ds_pop = gdal.Open(gpwv4)
    pop_band = ds_pop.GetRasterBand(1)
    
    with gzip.GzipFile(output, 'w') as file:
        columns = 'iso_a2', 'iso_a3', 'lon', 'lat', 'size', 'year', 'population', 'area'
        output = csv.DictWriter(file, columns)
        output.writerow({c: c for c in columns})
        
        for size in [1., .1]:
            for square in iterate_squares(ds_ids, size):
                (lon, lat), bbox = square[:2], square[2:]
                
                ids_array = ids_band.ReadAsArray(*bbox)
                pop_array = pop_band.ReadAsArray(*bbox).clip(0.0)
                are_array = make_area_array(lat, size, bbox[2], bbox[3])
            
                for index in numpy.unique(ids_array):
                    if index not in ids_lookup:
                        continue
                
                    people = numpy.sum(pop_array[ids_array == index])
                    area_km = numpy.sum(are_array[ids_array == index])
                    iso_a3 = ids_lookup[index]
                    iso_a2 = ne_country_iso_a3_countries.get(iso_a3, {}).get('iso_a2', '')
                    
                    out = dict(iso_a3=iso_a3, iso_a2=iso_a2, area=round(area_km, 3),
                               lat=lat, lon=lon, size=size, year='2015',
                               population=round(people, 3))
                
                    output.writerow(out)
