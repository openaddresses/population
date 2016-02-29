#!/usr/bin/env python

import dbf
import sys
import csv

if __name__ == '__main__':
    input, output = sys.argv[1:]
    
    with dbf.Table(input) as table:
        fields = table.field_names

        with open(output, 'w') as file:
            output = csv.DictWriter(file, fields)
            output.writerow({f: f for f in fields})
            
            for record in table:
                row = {f: str(record[f]).strip() for f in fields}
                output.writerow(row)
