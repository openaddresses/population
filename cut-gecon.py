#!/usr/bin/env python

import xlrd
import gzip
import csv
import sys

if __name__ == '__main__':
    input, output = sys.argv[1:]
    
    sheet = xlrd.open_workbook(input).sheet_by_index(0)
    
    header = [cell.value for cell in sheet.row(0)]
    fields = ['COUNTRY', 'LAT', 'LONGITUDE', 'AREA', 'POPGPW_2005_40']
    indexes = [header.index(field) for field in fields]
    
    print header
    print fields
    print indexes
    
    with gzip.GzipFile(output, 'w') as file:
        output = csv.writer(file)
        output.writerow(fields)
    
        for i in range(1, sheet.nrows):
            row = sheet.row(i)
            output.writerow([row[i].value for i in indexes])