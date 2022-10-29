from datetime import datetime
from datetime import timezone
from datetime import timedelta

from flask import (
    Blueprint, current_app, flash, redirect, render_template, request,
    session, url_for, make_response, g
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
    try:
        verify_jwt_in_request()
        g.user = current_user
    except NoAuthorizationError:
        pass
    except ExpiredSignatureError:
        return redirect(url_for('auth.refresh_expiring_jwts'))
    except RevokedTokenError:
        resp = make_response(redirect(url_for('auth.login')))
        resp.delete_cookie('csrf_token')
        resp.delete_cookie('csrf_refresh_token')
        resp.delete_cookie('csrf_access_token')
        resp.delete_cookie('refresh_token_cookie')
        resp.delete_cookie('access_token_cookie')
        return resp

@bp.route('/refresh')
@jwt_required(refresh=True)
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt()['sub'])
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        print(2)
        return response


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    db, cur = get_db()
    cur.execute('SELECT * FROM usr WHERE username = (%s);', (identity,))
    return cur.fetchone()


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = str(request.form['username'])
        password = str(request.form['password'])
        db, cur = get_db()

        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        cur.execute('SELECT id FROM usr WHERE username = (%s);', (username,))
        if cur.fetchone() is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            cur.execute(
                'INSERT INTO usr (username, password) VALUES (%s, %s);',
                (username, generate_password_hash(password))
            )
            db.commit()
            current_app.logger.info("User %s has been created.", username)
            return redirect(url_for('auth.login'))

        current_app.logger.error(error)
        flash(error)
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = str(request.form['username'])
        password = str(request.form['password'])
        db, cur = get_db()
        error = None

        cur.execute('SELECT * FROM usr WHERE username = (%s);', (username,))
        user = cur.fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            access_token = create_access_token(identity=username)
            refresh_token = create_refresh_token(identity=username)

            resp = make_response(redirect(url_for('auth.login')))
            set_access_cookies(resp, access_token)
            set_refresh_cookies(resp, refresh_token)
            current_app.logger.info(
                "User %s (%s) has logged in.", user['username'], user['id']
            )
            return resp

        current_app.logger.error(error)
        flash(error)

    context = {}
    try:
        verify_jwt_in_request()
        context['csrf_token'] = get_jwt().get("csrf")
    except NoAuthorizationError:
        pass
    return render_template('auth/login.html', **context)


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
    if cur.fetchone() is not None:
        return redirect(url_for('auth.login'))

    cur.execute(
        'INSERT INTO blocked_jwt (jti, created_at) VALUES (%s, %s);',
        (jti, now)
    )
    db.commit()
    current_app.logger.info("Token has been added to block list")
    resp = make_response(redirect(url_for('auth.login')))
    resp.delete_cookie('csrf_token')
    resp.delete_cookie('csrf_refresh_token')
    resp.delete_cookie('csrf_access_token')
    resp.delete_cookie('refresh_token_cookie')
    resp.delete_cookie('access_token_cookie')
    return resp
