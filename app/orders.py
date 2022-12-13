import base64

from flask import (
    Blueprint, current_app, flash, g, redirect, render_template, request,
    url_for, jsonify, session
)

from app.db import get_db
from app.auth import jwt_required
from app.products import wishlist_size

bp = Blueprint('orders', __name__, url_prefix='/orders')


@bp.route('/', methods=['GET'])
@jwt_required()
def orders():
    uid = g.user['id']
    db, cur = get_db()
    cur.execute('select * from "order" where user_id=%s', [uid])
    orders = cur.fetchall()
    orders = {str(o[0]): {'cost': o[2], 'date': o[3].strftime('%d.%m.%Y'), 'products': {}} for o in orders}
    if not orders:
        return render_template('/orders/index.html', wishlist_size=wishlist_size())
    cur.execute('''select order_id, product_id, quantity, price, product_img, title from order_products op
                   join product p on order_id in %s and op.product_id=p.id''', (tuple(orders.keys()),))
    items = cur.fetchall()
    for i in items:
        orders[str(i[0])]['products'][str(i[1])] = {'title': i[5], 'qty': i[2], 'price': i[3], 'img': base64.b64encode(i[4]).decode('utf-8') if i[4] else ''}
    return render_template('/orders/index.html', wishlist_size=wishlist_size(), orders=orders)
