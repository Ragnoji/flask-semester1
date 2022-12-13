import base64

from flask import (
    Blueprint, current_app, flash, g, redirect, render_template, request,
    url_for, jsonify, session
)

from app.db import get_db
from app.auth import jwt_required
from app.products import wishlist_size

bp = Blueprint('cart', __name__, url_prefix='/cart')


@bp.route('/append', methods=['POST'])
def append():
    p_id = request.json.get('id')
    if not p_id or not isinstance(p_id, int):
        return {'success': 0}
    p_id = str(p_id)

    db, cur = get_db()
    validate = """
    select price from product
    where id = %s
    """
    cur.execute(validate, p_id)
    item = cur.fetchone()
    if not item:
        return {'success': -1}

    cart = session.get('cart')
    if p_id in cart['products'].keys():
        return {'success': -1}
    cart['products'].setdefault(p_id, {'qty': 1, 'price': float(item[0])})
    cart['cost'] += float(item[0])
    cart['qty'] += 1
    session.modified = True
    return {'success': 1, 'qty': cart['qty'], 'cost': f"{cart['cost']} ₽"}


@bp.route('/change_quantity', methods=['POST'])
def change_quantity():
    p_id = request.json.get('id')
    action = request.json.get('action')
    if action not in ['+', '-'] or not p_id or not isinstance(p_id, int):
        return {'success': 0}
    p_id = str(p_id)

    cart = session.get('cart')
    if action == '-':
        if p_id not in cart['products'].keys():
            return {'success': 2, 'qty': cart['qty'], 'cost': f"{cart['cost']} ₽"}

        cart['products'][p_id]['qty'] -= 1
        cart['cost'] -= cart['products'][p_id]['price']
        cart['qty'] -= 1
        session.modified = True
        if cart['products'][p_id]['qty'] == 0:
            del cart['products'][p_id]
            session.modified = True
            return {'success': 2, 'qty': cart['qty'], 'cost': f"{cart['cost']} ₽"}
        return {'success': 1, 'p_qty': cart['products'][p_id]['qty'],
                'p_cost': cart['products'][p_id]['price'] * cart['products'][p_id]['qty'],
                'qty': cart['qty'], 'cost': f"{cart['cost']} ₽"}
    else:
        if p_id not in cart['products'].keys():
            return {'success': 0}
        cart['cost'] += cart['products'][p_id]['price']
        cart['qty'] += 1
        cart['products'][p_id]['qty'] += 1
        session.modified = True
        return {'success': 1, 'p_qty': cart['products'][p_id]['qty'],
                'p_cost': round(cart['products'][p_id]['price'] * cart['products'][p_id]['qty'], 2),
                'qty': cart['qty'], 'cost': f"{cart['cost']} ₽"}


@bp.route('/remove', methods=['POST'])
def remove():
    p_id = request.json.get('id')
    if not p_id or not isinstance(p_id, int):
        return {'success': 0}
    p_id = str(p_id)

    cart = session.get('cart')
    if p_id not in cart['products'].keys():
        return {'success': 1, 'qty': cart['qty'], 'cost': f"{cart['cost']} ₽"}

    cart['cost'] -= cart['products'][p_id]['price'] * cart['products'][p_id]['qty']
    cart['qty'] -= cart['products'][p_id]['qty']
    del cart['products'][p_id]
    session.modified = True
    return {'success': 1, 'qty': cart['qty'], 'cost': f"{cart['cost']} ₽"}


@bp.route('/')
def index():
    cart = session.get('cart')

    db, cur = get_db()
    product_ids = {i[0]: i[1] for i in cart.get('products').items() if i[0].isdigit()}
    products = []
    if product_ids:
        select_products = """
        select * from product
        where id in %s
        """
        cur.execute(select_products, (tuple(product_ids.keys()),))
        products = cur.fetchall()
        product_ids = {str(p[0]): cart['products'][str(p[0])] for p in products}
        products = {str(p[0]): {'name': p[1], 'img': base64.b64encode(p[3]).decode('utf-8') if p[3] else '', 'desc': p[4], 'price': p[5],
                                } for p in products}
    cart['products'] = product_ids
    session.modified = True

    return render_template('cart/index.html', products=products, wishlist_size=wishlist_size())


@bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    if 'cart' not in session or session['cart'].get('qty') == 0:
        return {'success': 0}

    cart = session['cart']
    db, cur = get_db()
    db.autocommit = False
    order_create_query = '''
    insert into "order"(user_id, cost) values (%s, %s)
    returning id
    '''

    try:
        cur.execute(order_create_query, (g.user['id'], cart['cost']))
    except:
        db.rollback()
        return {'success': 0}
    order_id = cur.fetchone()[0]

    products = {int(i[0]): i[1] for i in cart.get('products').items() if i[0].isdigit()}
    select_products = """
        select * from product
        where id in %s
        """
    cur.execute(select_products, (tuple(products.keys()),))
    products = cur.fetchall()
    products = {p[0]: cart['products'][str(p[0])] for p in products}
    insert_orderproducts = """
    insert into order_products(order_id, product_id, quantity)
    values 
    """
    args_str = ','.join(cur.mogrify("(%s, %s, %s)", (order_id, p, products[p]['qty'])).decode('utf-8')
                        for p in products.keys())
    try:
        cur.execute(insert_orderproducts + args_str)
    except:
        db.rollback()
        return {'success': 0}
    db.commit()

    cart['qty'] = 0
    cart['cost'] = 0
    cart['products'] = {}
    session.modified = True
    return {'success': 1}
