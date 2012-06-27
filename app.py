import os
import sqlite3
import urllib2
import urlparse

from flask import Flask, render_template, request, g, redirect, url_for
app = Flask(__name__)
app.debug = True
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'data/wiki.db')
app.config['KEY'] = ''

def nice_str(val):
    my_val = val
    if isinstance(val, unicode):
        my_val = val.encode('ascii')
    return urllib2.unquote(my_val).replace('_', ' ').decode('utf8')


def unzip_db():
    print 'unzipping geoset database'
    import gzip
    f_in = gzip.open(app.config['DATABASE']+'.gz', 'rb')
    f_out = open(app.config['DATABASE'], 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    print 'done unzipping'

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


SUGGESTED_CATEGORIES = [
    {'id':10795, 'name':'ACRA Racetracks'},
    {'id':12544, 'name':'Airports in Sicily', 'defaultzoom':15},
    {'id':22818, 'name':'Boston Harbor Islands'},
    {'id':24029, 'name':'Bridges in Washington, D.C.'},
    {'id':31495, 'name':'Castles in Bavaria', 'defaultzoom':18},
    {'id':57158, 'name':'Geoglyphs', 'defaultzoom':18},
    {'id':71521, 'name':'Indoor arenas in Brazil', 'defaultzoom':17},
    {'id':81582, 'name':'Major League Baseball Venues', 'defaultzoom':18},
    {'id':83068, 'name':'Maximum security prisons in Australia', 'defaultzoom':17},
]


CAT_QUERY = """
select * from category
 where cnt between 3 and 60
   and (? is null or name like '%'||?||'%')
 order by 2
 limit 1000;
"""

ENT_QUERY = """
select * from wiki
 where cat_id = ?
 order by ent;
"""


def get_categories(search_string=None):
    res = g.db.execute(CAT_QUERY, (search_string, search_string))
    return (dict(id=r[0], name=nice_str(r[1]), url_name=r[1]) for r in
            res.fetchall())


def get_entities(cat_id):
    res = g.db.execute(ENT_QUERY, (cat_id,))
    return [dict(cat=nice_str(r[0]), url_cat=r[0],
                 name=nice_str(r[1]), url_name=r[1],
                 lat=r[2], lon=r[3]) for r in res]


@app.route('/')
def index():

    # missing trailing slash fix (to prevent broken links on sametwsgi)
    if ('REQUEST_URI' in request.environ and
        not urlparse.urlparse(request.environ['REQUEST_URI']).path.endswith('/')):
        return redirect(url_for('index').rstrip('/') + '/')

    g.db = connect_db()

    search_string = request.args.get('search_string', '')
    cat_id = request.args.get('cat_id')
    defaultzoom = request.args.get('defaultzoom', '')

    categories = []
    if search_string:
        categories = get_categories(search_string=search_string)

    if cat_id is not None:
        entities = get_entities(cat_id)
    else:
        entities = []

    return render_template('index.html',
                           categories=categories,
                           entities=entities,
                           cat_id=cat_id,
                           search_string=search_string,
                           suggested_categories=SUGGESTED_CATEGORIES,
                           defaultzoom=defaultzoom
                          )

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    if not os.path.isfile(app.config['DATABASE']):
        unzip_db()
    app.run('0.0.0.0')
