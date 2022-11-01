import re

from flask import (
    Blueprint, current_app, flash, g, redirect, render_template, request,
    session, url_for
)

from app.db import get_db
from app.auth import jwt_required

from psycopg2 import sql

bp = Blueprint('shop', __name__)


@bp.route('/')
def index():

    render_template('index.html')


@bp.route('/query')
def query():
    db, cur = get_db()
    args = request.args
    offset = args.get('start', 0)
    limit = args.get('count', 10)
    sort_column_enum = {'creation': 'created_at', 'price': 'price'}
    sort_column = sort_column_enum.get(args.get('sort_column', default='creation'), 'created_at')
    sort_dir = args.get('sort_dir', default='desc')
    if sort_dir not in ('desc', 'asc'):
        sort_dir = 'desc'
    category_id = args.get('category', default=None)
    features = [(int(k.split('_')[1]), v) for k, v in args.items() if re.match(r'feature_[1-9]*\d\b', k)]

    if category_id:
        query1 = """SELECT  *
                                FROM    (
                                        SELECT pr.id, title, product_img, description, price
                                        FROM	product pr
                                        join	category_products cp on cp.product_id = pr.id and cp.category_id = %s
                                        order by %s %s
                                        ) mo
                          """ % (category_id, sort_column, sort_dir)
    else:
        query1 = """SELECT  *
                                        FROM    (
                                                SELECT pr.id, title, product_img, description, price
                                                FROM	product pr
                                                order by %s %s
                                                ) mo
                                                """ % (sort_column, sort_dir)
    feature_query = ""
    if features:
        feature_query = """WHERE   NOT EXISTS
                                        (
                                        SELECT  NULL
                                        FROM    ("""
        feature_query += " SELECT %s as feature_id, '%s' as value" % (features[0][0], features[0][1])
        for f in features[1:]:
            feature_query += " UNION ALL"
            feature_query += " SELECT %s, '%s'" % (f[0], f[1])
        feature_query += """) list
                            WHERE   NOT EXISTS
                                (
                                SELECT  NULL
                                FROM    feature_products fp
                                join	feature fr on fp.feature_id = fr.id
                                WHERE   fp.product_id = mo.id
                                        AND fp.feature_id = list.feature_id and fr.value = list.value
                                )
                            )"""
    limit_query = " LIMIT %s OFFSET %s" % (limit, offset)
    cur.execute(query1 + feature_query + limit_query)
    products = cur.fetchall()
    return products
