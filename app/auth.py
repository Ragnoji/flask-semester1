import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db


bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        db, cur = get_db()
        cur.execute('SELECT * FROM "user" WHERE id = (%s);', (user_id,))
        g.user = cur.fetchone()

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
        cur.execute('SELECT id FROM "user" WHERE username = (%s);', (username,))
        if cur.fetchone() is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            cur.execute(
                'INSERT INTO "user" (username, password) VALUES (%s, %s);',
                (username, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)
    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = str(request.form['username'])
        password = str(request.form['password'])
        db, cur = get_db()
        error = None

        cur.execute('SELECT * FROM "user" WHERE username = (%s);', (username,))
        user = cur.fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('auth.login')) # TODO: redirect to index

        flash(error)

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login')) # TODO: redirect to index


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view