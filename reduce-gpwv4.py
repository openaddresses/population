#!/usr/bin/env python

from __future__ import division

from osgeo import gdal
import numpy
import gzip
import csv
import sys

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

if __name__ == '__main__':
    
    gpwv4, gluntlbnds, gluntlbnds_ids, output = sys.argv[1:]
    
    with open(gluntlbnds_ids) as file:
        ids_rows = csv.DictReader(file)
        ids_lookup = {int(r['VALUE']): r['ISO3V10'] for r in ids_rows}

    ds_ids = gdal.Open(gluntlbnds)
    ids_band = ds_ids.GetRasterBand(1)

    ds_pop = gdal.Open(gpwv4)
    pop_band = ds_pop.GetRasterBand(1)
    
    with gzip.GzipFile(output, 'w') as file:
        columns = 'iso_a3', 'lon', 'lat', 'size', 'year', 'population'
        output = csv.DictWriter(file, columns)
        output.writerow({c: c for c in columns})
        
        for size in [1., .1]:
            for square in iterate_squares(ds_ids, size):
                (lon, lat), bbox = square[:2], square[2:]
            
                ids_array = ids_band.ReadAsArray(*bbox)
                pop_array = pop_band.ReadAsArray(*bbox).clip(0.0)
            
                for index in numpy.unique(ids_array):
                    if index not in ids_lookup:
                        continue
                
                    population = numpy.sum(pop_array[ids_array == index])
                    
                    out = dict(iso_a3=ids_lookup[index],
                               lat=lat, lon=lon, size=size, year='2015',
                               population=round(population, 3))
                
                    output.writerow(out)
