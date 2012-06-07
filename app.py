import os
import sqlite3
import urllib2

from flask import Flask, render_template, request, g
app = Flask(__name__)
app.debug = True
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'data/wiki.db')
app.config['KEY'] = ''

nice_str = lambda s: urllib2.unquote(s).replace('_', ' ')


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


CAT_QUERY = """
select * from category
 where cnt between 5 and 40
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
    return (dict(id=r[0], name=nice_str(r[1])) for r in
            res.fetchall())


def get_entities(cat_id):
    res = g.db.execute(ENT_QUERY, (cat_id,))
    return [dict(cat=nice_str(r[0]), url_cat=r[0],
                 name=nice_str(r[1]), url_name=r[1],
                 lat=r[2], lon=r[3]) for r in res]


@app.route('/')
def index():
    g.db = connect_db()

    search_string = request.args.get('search_string', '')
    cat_id = request.args.get('cat_id')

    categories = get_categories(search_string=search_string)

    if cat_id is not None:
        entities = get_entities(cat_id)
    else:
        entities = []
    
    return render_template('index.html', 
                           categories=categories,
                           entities=entities,
                           cat_id=cat_id,
                           search_string=search_string)


if __name__ == '__main__':
    if not os.path.isfile(app.config['DATABASE']):
        unzip_db()
    app.run('0.0.0.0')
