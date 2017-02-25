#!/usr/bin/env python

from __future__ import division

from osgeo import gdal
from ModestMaps.OpenStreetMap import Provider
from ModestMaps.Core import Coordinate
from ModestMaps.Geo import Location
import numpy
import math
import gzip
import csv
import sys
import util

def iterate_squares(ds, zoom):
    '''
    '''
    xoff, xstride, _, yoff, _, ystride = ds.GetGeoTransform()
    
    minlon, maxlat = xoff, yoff
    maxlon = xoff + ds.RasterXSize * xstride
    minlat = yoff + ds.RasterYSize * ystride
    
    if zoom > 11:
        maxlat = min(58, maxlat)
    
    osm = Provider()
    ul = osm.locationCoordinate(Location(maxlat, minlon)).zoomTo(zoom)
    lr = osm.locationCoordinate(Location(minlat, maxlon)).zoomTo(zoom)
    #lr = osm.locationCoordinate(Location(20, -60)).zoomTo(zoom)
    
    row = int(ul.row)
    while row < lr.row:
        lat = osm.coordinateLocation(Coordinate(row, 0, zoom)).lat
        print >> sys.stderr, 'lat:', round(lat, 2)
        col = int(ul.column)
        while col < lr.column:
            coord = Coordinate(row, col, zoom)
            sw = osm.coordinateLocation(coord.down())
            ne = osm.coordinateLocation(coord.right())
            
            west = max(minlon, sw.lon)
            north = min(maxlat, ne.lat)
            east = min(maxlon, ne.lon)
            south = max(minlat, sw.lat)
            
            left = round((west - xoff) / xstride)
            top = round((north - yoff) / ystride)
            width = round((east - xoff) / xstride) - left
            height = round((south - yoff) / ystride) - top
            
            yield (coord, south, north, int(left), int(top), int(width), int(height))
            
            col += 1
        row += 1
    
    return
    
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

def make_area_array(south, north, cols, rows):
    ''' Return array filled with sq. km values.
    '''
    if (south, north, cols, rows) in _arrays:
        return _arrays[(south, north, cols, rows)]

    size = north - south
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
        columns = 'iso_a2', 'iso_a3', 'z', 'x', 'y', 'year', 'population', 'area'
        output = csv.DictWriter(file, columns)
        output.writerow({c: c for c in columns})
        
        for zoom in [8, 11, 13]:
            for square in iterate_squares(ds_ids, zoom):
                (coord, south, north), bbox = square[:3], square[3:]
                
                ids_array = ids_band.ReadAsArray(*bbox)
                pop_array = pop_band.ReadAsArray(*bbox).clip(0.0)
                are_array = make_area_array(south, north, bbox[2], bbox[3])
            
                for index in numpy.unique(ids_array):
                    if index not in ids_lookup:
                        continue
                
                    people = numpy.sum(pop_array[ids_array == index])
                    area_km = numpy.sum(are_array[ids_array == index])
                    iso_a3 = ids_lookup[index]
                    iso_a2 = ne_country_iso_a3_countries.get(iso_a3, {}).get('iso_a2', '')
                    
                    out = dict(iso_a3=iso_a3, iso_a2=iso_a2, area=round(area_km, 3),
                               z=coord.zoom, x=coord.column, y=coord.row, year='2015',
                               population=round(people, 3))
                
                    output.writerow(out)
