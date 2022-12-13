from flask import (
    Blueprint, current_app, flash, g, redirect, render_template, request,
    url_for, jsonify, session
)

from app.db import get_db
from app.auth import jwt_required
from app.products import wishlist_size

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/', methods=['GET'])
@jwt_required()
def profile():
    return render_template('/user/profile.html', wishlist_size=wishlist_size())


@bp.route('/update', methods=['POST'])
@jwt_required()
def update():
    first_name = request.form['first_name']
    second_name = request.form['second_name']
    print(first_name, second_name)
    uid = g.user['id']
    print(uid)
    db, cur = get_db()
    db.autocommit = False
    try:
        cur.execute('''update usr set first_name=%s, second_name=%s where id=%s''', (first_name, second_name, uid))
    except:
        db.rollback()
        return {'success': 0}
    db.commit()
    return {'success': 1}


