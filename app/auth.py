from datetime import datetime
from datetime import timezone
from datetime import timedelta

from flask import (
    Blueprint, current_app, redirect, render_template, request,
    url_for, make_response, g, session
)

from flask_jwt_extended import (JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity,
                                set_access_cookies, set_refresh_cookies, current_user, get_jwt, verify_jwt_in_request)
from flask_jwt_extended.exceptions import NoAuthorizationError, RevokedTokenError
from jwt.exceptions import ExpiredSignatureError
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db

jwt = JWTManager(current_app)
bp = Blueprint('auth', __name__)


@bp.before_app_request
def load_logged_in_user():
    if request.endpoint == 'auth.refresh_expiring_jwts':
        return refresh_expiring_jwts()
    if 'cart' not in session:
        session.setdefault('cart', {'qty': 0, 'cost': 0, 'products': {}})
    session.modified = True
    try:
        verify_jwt_in_request()
        g.user = current_user
    except NoAuthorizationError:
        pass
    except ExpiredSignatureError:
        return redirect(url_for('auth.refresh_expiring_jwts'))
    except RevokedTokenError:
        resp = make_response(redirect(url_for('products.index')))
        resp.delete_cookie('csrf_token')
        resp.delete_cookie('csrf_refresh_token')
        resp.delete_cookie('csrf_access_token')
        resp.delete_cookie('refresh_token_cookie')
        resp.delete_cookie('access_token_cookie')
        return resp


@bp.route('/refresh')
@jwt_required(refresh=True)
def refresh_expiring_jwts():
    response = make_response(redirect(url_for('products.index')))
    try:
        access_token = create_access_token(identity=get_jwt()['sub'])
        set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    db, cur = get_db()
    cur.execute('SELECT * FROM usr WHERE username = (%s);', (identity,))
    return cur.fetchone()


@bp.route('/register', methods=['POST'])
def register():
    username = str(request.form['username']).lower()
    password = str(request.form['password'])
    db, cur = get_db()

    error = None
    errors = []
    if not username:
        return {'success': 0, 'error': 'Не указан логин'}
    elif not password:
        return {'success': 0, 'error': 'Не указан пароль'}

    cur.execute('SELECT id FROM usr WHERE username = (%s);', (username,))
    if cur.fetchone() is not None:
        return {'success': 0, 'error': 'Выбранное имя пользователя уже занято'}

    if error is None:
        cur.execute(
            'INSERT INTO usr (username, password) VALUES (%s, %s);',
            (username, generate_password_hash(password))
        )
        db.commit()

        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)

        resp = make_response({'success': 1})
        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)
        return resp

    return {'success': -1}


@bp.route('/login', methods=['POST'])
def login():
    username = str(request.form['username']).lower()
    password = str(request.form['password'])
    db, cur = get_db()
    error = None

    cur.execute('SELECT * FROM usr WHERE username = (%s);', (username,))
    user = cur.fetchone()

    if user is None or not check_password_hash(user['password'], password):
        error = 'Неправильное имя пользователя или пароль'
        return {'success': 0, 'error': error}

    if error is None:
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)

        resp = make_response({'success': 1})
        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)
        load_logged_in_user()
        return resp


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    db, cur = get_db()
    cur.execute('SELECT * from blocked_jwt WHERE jti = (%s);', (jti,))

    return cur.fetchone() is not None


@bp.route('/logout', methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)

    db, cur = get_db()
    cur.execute('SELECT id FROM blocked_jwt WHERE jti = (%s);', (jti,))
    if cur.fetchone() is None:
        cur.execute(
            'INSERT INTO blocked_jwt (jti, created_at) VALUES (%s, %s);',
            (jti, now)
        )
        db.commit()

    resp = make_response(redirect(url_for('products.index')))
    resp.delete_cookie('csrf_token')
    resp.delete_cookie('csrf_refresh_token')
    resp.delete_cookie('csrf_access_token')
    resp.delete_cookie('refresh_token_cookie')
    resp.delete_cookie('access_token_cookie')
    session.clear()
    return resp


def admin_required(func):
    def wrapper(*args, **kwargs):
        if not g.user or g.user['role'] != "admin":
            return make_response(redirect(url_for('products.index'), 302))
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper
