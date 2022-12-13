import base64
import re
import os

from flask import (
    Blueprint, current_app, flash, g, redirect, render_template, request,
    session, url_for, jsonify
)

from app.db import get_db
from app.auth import jwt_required

bp = Blueprint('products', __name__)


@bp.route('/', methods=['GET'])
def index():
    db, cur = get_db()
    q = """select * from category"""
    cur.execute(q)
    categories = [{'id': str(c[0]), 'name': c[1]} for c in cur.fetchall()]
    context = query()
    context['categories'] = categories
    return render_template('/products/index.html', title='Каталог', wishlist_size=wishlist_size(), **context)


@bp.route('/query', methods=['GET'])
def query():
    db, cur = get_db()
    args = request.args
    html = 'html' in args
    offset = int(args.get('start', 0))
    limit = int(args.get('count', 5))
    s = args.get('search', '').replace("'", '"')
    search = ''
    if s:
        search = cur.mogrify('''WHERE to_tsvector(title) @@ to_tsquery(%s)''', [s.replace(' ', '+') + ':*']).decode('utf-8')
    sort_column_enum = {'created_at': 'created_at', 'price': 'price'}
    orderby = sort_column_enum.get(args.get('orderby', default='creation').split()[0], 'created_at')
    sort_dir = args.get('orderby', default='.. desc').split()[1]
    if sort_dir not in ('desc', 'asc'):
        sort_dir = 'desc'
    category_id = args.get('category', default='')
    features = [(int(k.split('_')[1]), v) for k, v in args.items() if re.match(r'feature_[1-9]\d*\b', k) and v != '']
    print(features)

    c_f_d = {}
    if category_id:
        query1 = """SELECT  *
                                FROM    (
                                        SELECT pr.id, title, product_img, description, price
                                        FROM	product pr
                                        %s
                                        join	category_products cp on cp.product_id = pr.id and cp.category_id = %s
                                        order by %s %s
                                        ) mo
                          """ % (search, category_id, orderby, sort_dir)
        query1_size = """SELECT  count(*)
                                FROM    (
                                        SELECT pr.id, title, product_img, description, price
                                        FROM	product pr
                                        %s
                                        join	category_products cp on cp.product_id = pr.id and cp.category_id = %s
                                        order by %s %s
                                        ) mo
                          """ % (search, category_id, orderby, sort_dir)
        query2 = """SELECT  *
                                FROM    (
                                        SELECT f.id, f.name, fv.value, fv.id as fv
                                        FROM	feature_value fv
                                        join	feature f on fv.feature_id = f.id
                                        order by f.name
                                        ) f_v
                    where EXISTS (
                        SELECT NULL FROM category_products cp
                        join feature_products fp
                        on cp.product_id = fp.product_id and cp.category_id = %s and fp.feature_value_id = f_v.fv
                    )""" % category_id
        cur.execute(query2)
        c_f = cur.fetchall()
        c_f_d = {'features': {}}
        for r in c_f:
            c_f_d['features'].setdefault(r[0], {})
            c_f_d['features'][r[0]].setdefault('name', r[1])
            c_f_d['features'][r[0]].setdefault('values', [])
            c_f_d['features'][r[0]]['values'].append(r[2])
    else:
        query1 = """SELECT  *
                                        FROM    (
                                                SELECT pr.id, title, product_img, description, price
                                                FROM	product pr
                                                %s
                                                order by %s %s
                                                ) mo
                                                """ % (search, orderby, sort_dir)
        query1_size = """SELECT  count(*)
                                        FROM    (
                                                SELECT pr.id, title, product_img, description, price
                                                FROM	product pr
                                                %s
                                                order by %s %s
                                                ) mo
                                                """ % (search, orderby, sort_dir)
    feature_query = ""
    if features:
        feature_query = """WHERE   NOT EXISTS
                                        (
                                        SELECT  NULL
                                        FROM    ("""
        feature_query += " SELECT %s as feature_id, '%s' as value" % (features[0][0], features[0][1])
        for f in features[1:]:
            if f[1] == '':
                continue
            feature_query += " UNION ALL"
            feature_query += " SELECT %s, '%s'" % (f[0], f[1])
        feature_query += """) list
                            WHERE   NOT EXISTS
                                (
                                SELECT  NULL
                                FROM    feature_products fp
                                join    feature_value fv
                                on fv.id = fp.feature_value_id
                                WHERE   fp.product_id = mo.id
                                        AND fv.feature_id = list.feature_id and fv.value = list.value
                                )
                            )"""
    limit_query = " LIMIT %s OFFSET %s" % (limit, offset)
    user = g.get('user', '')
    favorites = []
    if user:
        userid = user[0]
        favorite_query = f"SELECT p.id FROM ({query1 + feature_query + limit_query}) p " \
                         f"join usr_fav_products ufp on ufp.user_id=%s and ufp.product_id=p.id"
        cur.execute(favorite_query, [userid])
        favorites = [i[0] for i in cur.fetchall()]
    cur.execute(query1 + feature_query + limit_query)
    products = cur.fetchall()
    cur.execute(query1_size + feature_query)
    total_count = cur.fetchone()[0]

    pr_d = {'products': [{'id': str(p[0]), 'name': p[1], 'img': base64.b64encode(p[2]).decode('utf-8') if p[2] else '', 'desc': p[3], 'price': p[4],
                          'favorite': p[0] in favorites} for p in products]}
    context = dict(pr_d, **{'search': s, 'total_count': total_count, 'start': offset, 'count': limit,
                            'category': category_id})
    if c_f_d:
        context = dict(c_f_d, **context)
        print(context['features'])

    context['current_page'] = context['start'] // context['count'] + 1
    pages_before = context['current_page'] - 1
    pages_before = 4 if pages_before > 4 else pages_before
    pages_after = context['total_count'] // context['count'] - context['current_page']
    pages_after = 3 if pages_after > 3 else pages_after
    context['pages'] = [i for i in range(context['count'] * (context['current_page'] - pages_before - 1),
                                         context['count'] * (context['current_page'] + pages_after) + 1,
                                         context['count'])]
    if not html:
        return context
    context['search_results'] = render_template('/products/search_results.html', **context)
    return context


@bp.route('/add_favorite', methods=['POST'])
@jwt_required()
def add_favorite():
    p_id = request.json.get('id')
    if not p_id or not isinstance(p_id, int):
        return {'success': 0}

    usr_id = g.user['id']
    db, cur = get_db()
    cur.execute('''select 1 from product
    where id=%s''', [p_id])
    if not cur.fetchone():
        return {'success': -1}

    cur.execute('''select 1 from usr_fav_products
    where user_id=%s and product_id=%s''', (usr_id, p_id))

    if cur.fetchone():
        return {'success': 1}

    try:
        cur.execute('''insert into usr_fav_products (user_id, product_id) values (%s, %s)''', (usr_id, p_id))
    except Exception:
        return {'success': 0}

    return {'success': 1}


@bp.route('/remove_favorite', methods=['POST'])
@jwt_required()
def remove_favorite():
    p_id = request.json.get('id')
    if not p_id or not isinstance(p_id, int):
        return {'success': 0}

    usr_id = g.user['id']
    db, cur = get_db()
    cur.execute('''select 1 from product
    where id=%s''', [p_id])
    if not cur.fetchone():
        return {'success': -1}

    cur.execute('''select 1 from usr_fav_products
    where user_id=%s and product_id=%s''', (usr_id, p_id))

    if not cur.fetchone():
        return {'success': 1}

    try:
        cur.execute('''delete from usr_fav_products where user_id=%s and product_id=%s''', (usr_id, p_id))
    except Exception:
        return {'success': 0}

    return {'success': 1}


@bp.route('/wishlist/', methods=['GET'])
@jwt_required()
def wishlist():
    uid = g.user['id']
    db, cur = get_db()

    cur.execute('''SELECT p.id, title, product_img, description, price from product p
                   join usr_fav_products ufp on ufp.user_id=%s and ufp.product_id=p.id''', [uid])
    products = cur.fetchall()
    products = {str(p[0]): {'name': p[1], 'img': base64.b64encode(p[2]).decode('utf-8') if p[2] else '', 'desc': p[3], 'price': p[4],
                            } for p in products}
    return render_template('/wishlist/index.html', products=products, wishlist_size=len(products))


def wishlist_size():
    if not g.get('user'):
        return False

    db, cur = get_db()
    uid = g.user['id']
    cur.execute('''select count(*) from usr_fav_products
                   where user_id=%s''', [uid])
    return cur.fetchone()[0]