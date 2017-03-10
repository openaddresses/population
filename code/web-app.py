#!/usr/bin/env python2
from __future__ import print_function, division
import flask, psycopg2, psycopg2.extras, os

app = flask.Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route('/')
def get_index():
    with psycopg2.connect(os.environ['DATABASE_URL']) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as db:
            db.execute('''SELECT iso_a2, name, addr_count, area_total, area_pct, pop_total, pop_pct
                          FROM areas WHERE name IS NOT NULL ORDER BY name''')
            areas = db.fetchall()
            
    best_areas, okay_areas, empty_areas = list(), list(), list()
    
    for area in areas:
        if area['pop_pct'] > 0.98:
            best_areas.append(area)
        elif area['pop_pct'] > 0.75:
            okay_areas.append(area)
        else:
            empty_areas.append(area)
    
    return flask.render_template('index.html', best_areas=best_areas,
                                 okay_areas=okay_areas, empty_areas=empty_areas)

@app.template_filter('nice_percentage')
def filter_nice_percentage(number):
    ''' Format a floating point number like '11%'
    '''
    return '{:.1f}%'.format((number or 0) * 100)

@app.template_filter('nice_integer')
def filter_nice_integer(number):
    ''' Format a number like '99M', '9.9M', '99K', '9.9K', or '999'
    '''
    if number > 10000000:
        return '{:.0f}M'.format(number / 1000000)
    
    if number > 1000000:
        return '{:.1f}M'.format(number / 1000000)
    
    if number > 10000:
        return '{:.0f}K'.format(number / 1000)
    
    if number > 1000:
        return '{:.1f}K'.format(number / 1000)
    
    if number >= 1:
        return '{:.0f}'.format(number)
    
    return '0'

def main():
    app.run(debug=True)

if __name__ == '__main__':
    exit(main())
