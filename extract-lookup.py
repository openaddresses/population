#!/usr/bin/env python

from osgeo import gdal
import sys
import csv

if __name__ == '__main__':
    input, output = sys.argv[1:]
    
    ds = gdal.Open(input)
    rat = ds.GetRasterBand(1).GetDefaultRAT()
    
    indices = range(rat.GetColumnCount())
    fields = [rat.GetNameOfCol(j) for j in indices]
    
    with open(output, 'w') as file:
        output = csv.writer(file)
        output.writerow(fields)
        
        for i in range(rat.GetRowCount()):
            row = [rat.GetValueAsString(i, j) for j in indices]
            output.writerow(row)
