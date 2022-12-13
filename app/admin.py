import os
import base64
import decimal

from flask import (
    Blueprint, current_app, flash, g, redirect, render_template, request,
    url_for, jsonify, session, make_response
)
from werkzeug.utils import secure_filename

from app.db import get_db
from app.auth import jwt_required, admin_required
from app.products import wishlist_size

bp = Blueprint('admin', __name__, url_prefix='/admin')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in current_app.config['ALLOWED_EXTENSIONS']


@bp.route('/', methods=['GET'])
@jwt_required()
@admin_required
def index():
    db, cur = get_db()

    cur.execute('''select id, name from category''')
    categories = cur.fetchall()
    categories = {str(c[0]): {'name': c[1]} for c in categories}
    cur.execute('''select fv.id, f.name, fv.value from feature_value fv
                   join feature f on fv.feature_id=f.id''')
    feature_values = cur.fetchall()
    feature_values = {str(fv[0]): {'name': fv[1], 'value': fv[2]} for fv in feature_values}
    cur.execute('''select id, name from feature''')
    features = cur.fetchall()
    features = {str(f[0]): {'name': f[1]} for f in features}
    cur.execute('''select p.id, title, description, c.category_id, product_img, price from product p
                   left join category_products c on p.id=c.product_id''')
    products = cur.fetchall()
    products = {str(p[0]): {'title': p[1], 'desc': p[2], 'category_name': categories[str(p[3])]['name'] if p[3] else 'Пусто',
                            'img': base64.b64encode(p[4]).decode('utf-8') if p[4] else '', 'price': p[5]}
                for p in products}
    print(products)
    context = {
        'features': features,
        'feature_values': feature_values,
        'categories': categories,
        'products': products,
        'wishlist_size': wishlist_size()
    }
    return render_template('/admin/index.html', **context)


@bp.route('/add_product', methods=['POST'])
@jwt_required()
@admin_required
def add_product():
    title = request.form.get('title')
    description = request.form.get('description')
    price = request.form.get('price')
    img = request.files.get('product_img')
    category = request.form.get('category')
    if not title or not price:
        return {'success': 0, 'err': 'Не введены название или цена товара'}
    if category and not category.isdigit():
        return {'success': 0, 'err': 'ID категории некорректного формата'}
    db, cur = get_db()
    if category:
        cur.execute('select 1 from category where id=%s', [int(category)])
        if not cur.fetchone():
            return {'success': 0, 'err': 'Указанная категория не существует'}
    if img and not allowed_file(img.filename):
        return {'success': 0, 'err': 'Некорректный файл'}

    db.autocommit = False
    try:
        if img:
            bt = img.read()
            cur.execute('''insert into product(title, description, price, product_img)
                           values (%s, %s, %s, %s) returning id''', (title, description, price, bt))
        else:
            cur.execute('''insert into product(title, description, price)
                           values (%s, %s, %s) returning id''', (title, description, price))
        pid = cur.fetchone()[0]
        if category:
            cur.execute('''insert into category_products(category_id, product_id) values (%s, %s)''',
                        (int(category), pid))
    except Exception as e:
        print(e)
        db.rollback()
        return {'success': 0, 'err': 'Ошибка во время добавления строки в БД'}
    db.commit()
    return {'success': 1}


@bp.route('/add_category', methods=['POST'])
@jwt_required()
@admin_required
def add_category():
    name = request.form.get('title')
    if not name:
        return {'success': 0, 'err': 'Некорректное название'}
    db, cur = get_db()
    db.autocommit = False
    try:
        cur.execute('''insert into category(name) values (%s)''', [name])
    except Exception as e:
        print(e)
        db.rollback()
        return {'success': 0, 'err': 'Ошибка на этапе запроса к БД'}
    db.commit()
    return {'success': 1}


@bp.route('/add_feature', methods=['POST'])
@jwt_required()
@admin_required
def add_feature():
    name = request.form.get('title')
    if not name:
        return {'success': 0, 'err': 'Некорректное название'}
    db, cur = get_db()
    db.autocommit = False
    try:
        cur.execute('''insert into feature(name) values (%s)''', [name])
    except Exception as e:
        print(e)
        db.rollback()
        return {'success': 0, 'err': 'Ошибка на этапе запроса к БД'}
    db.commit()
    return {'success': 1}


@bp.route('/add_feature_value', methods=['POST'])
@jwt_required()
@admin_required
def add_feature_value():
    feature = request.form.get('feature')
    value = request.form.get('value')
    if not feature or not value:
        return {'succes': 0, 'err': 'Не введены фича или значение'}
    if not feature.isdigit():
        return {'success': 0, 'err': 'Некорректная фича'}
    db, cur = get_db()
    cur.execute('''select 1 from feature where id=%s''', [int(feature)])
    if not cur.fetchone():
        return {'success': 0, 'err': 'Указанная фича не найдена'}
    db.autocommit = False
    try:
        cur.execute('''insert into feature_value(feature_id, value) values (%s, %s)''',
                    [int(feature), value])
    except Exception as e:
        print(e)
        db.rollback()
        return {'success': 0, 'err': 'Ошибка на этапе запроса к БД'}
    db.commit()
    return {'success': 1}


@bp.route('/bind_feature_value', methods=['POST'])
@jwt_required()
@admin_required
def bind_feature_value():
    product = request.form.get('product')
    fv = request.form.get('feature')
    if not fv or not product:
        return {'succes': 0, 'err': 'Не введены фича или значение'}
    if not fv.isdigit() or not product.isdigit():
        return {'success': 0, 'err': 'Некорректная фича'}
    db, cur = get_db()
    cur.execute('''select 1 from feature_value where id=%s''', [int(fv)])
    if not cur.fetchone():
        return {'success': 0, 'err': 'Указанная фича не найдена'}
    cur.execute('''select 1 from product where id=%s''', [int(product)])
    if not cur.fetchone():
        return {'success': 0, 'err': 'Указанный продукт не найден'}
    db.autocommit = False
    try:
        cur.execute('''insert into feature_products(feature_value_id, product_id) values (%s, %s)''',
                    [int(fv), int(product)])
    except Exception as e:
        print(e)
        db.rollback()
        return {'success': 0, 'err': 'Ошибка на этапе запроса к БД'}
    db.commit()
    return {'success': 1}


@bp.route('/edit_product/<int:id>', methods=['GET'])
@jwt_required()
@admin_required
def edit_product(id):
    db, cur = get_db()
    cur.execute('''select p.id, title, description, c.category_id, product_img, price from product p
                       left join category_products c on p.id=c.product_id and p.id=%s''', [id])
    product = cur.fetchone()
    if not product:
        return 'Такого продукта нет'

    product = {'id': id, 'title': product[1], 'description': product[2], 'category': str(product[3]) if product[3] else '',
               'img': base64.b64encode(product[4]).decode('utf-8') if product[4] else '',
               'price': product[5]}
    cur.execute('''select id, name from category''')
    categories = cur.fetchall()
    categories = {str(c[0]): {'name': c[1]} for c in categories}
    cur.execute('''select fv.id, f.name, fv.value from feature_value fv
                       join feature f on fv.feature_id=f.id''')
    feature_values = cur.fetchall()
    feature_values = {str(fv[0]): {'name': fv[1], 'value': fv[2]} for fv in feature_values}
    cur.execute('''select id, name from feature''')
    context = {
        'product': product,
        'categories': categories,
        'feature_values': feature_values,
        'wishlist_size': wishlist_size()
    }
    return render_template('/admin/edit.html', **context)


@bp.route('/update_product/<int:id>', methods=['POST'])
@jwt_required()
@admin_required
def update_product(id):
    title = request.form.get('title')
    price = request.form.get('price')
    description = request.form.get('description')
    category = request.form.get('category')
    img = request.files.get('product_img')

    if not title or not price:
        return {'success': 0, 'err': 'Не введены название или цена'}
    try:
        price = decimal.Decimal(price)
    except Exception as e:
        print(e)
        return {'success': 0, 'err': 'Некорректная цена'}

    if not category:
        return {'success': 0, 'err': 'Категория не ввиде числа'}
    if img and not allowed_file(img.filename):
        return {'success': 0, 'err': 'Некорректное изображение'}

    db, cur = get_db()
    db.autocommit = False
    try:
        if img:
            cur.execute('''update product
                           set title=%s, price=%s, description=%s, product_img=%s
                           where id=%s''', [title, price, description, img.read(), id])
        else:
            cur.execute('''update product
                           set title=%s, price=%s, description=%s, product_img=Null
                           where id=%s''',
                        [title, price, description, id])
    except Exception as e:
        print(e)
        db.rollback()
        return {'success': 0, 'err': 'Ошибка на этапе обновления продукта'}
    cur.execute('''select category_id from category_products
                   where product_id=%s''', [id])
    prev_category = str(cur.fetchone()[0])
    if prev_category == category:
        return {'success': 1}
    cur.execute('''select 1 from category where id=%s''', [int(category)])
    if not cur.fetchone():
        db.rollback()
        return {'success': 0, 'err': 'Такой категории нет'}
    cur.execute('''delete from category_products where id=%s''', [int(category)])
    cur.execute('''insert into category_products(category_id, product_id) values (%s, %s)''',
                [int(category), id])
    return {'success': 1}