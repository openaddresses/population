#!/usr/bin/env python2
import flask

app = flask.Flask(__name__)

@app.route('/')
def get_index():
    return 'Hello world'

def main():
    app.run(debug=True)

if __name__ == '__main__':
    exit(main())
