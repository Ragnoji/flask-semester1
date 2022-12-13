import os

from datetime import datetime
from datetime import timedelta
from datetime import timezone

import jinja2
from flask import Flask
from flask_session import Session

from flask_jwt_extended import JWTManager


def create_app(test_config=None):
    """Create and configure the app"""
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = os.urandom(24)

    ACCESS_EXPIRES = timedelta(hours=12)
    UPLOAD_FOLDER = '/static/img/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
    app.config["JWT_COOKIE_SECURE"] = False
    app.config["JWT_SECRET_KEY"] = "enj1FMjk#!*@enqenJQEN@$f4@JWV3NJ23Vn@1;.VNVB43UqeWQ@3134J$@$2n$F44C,24"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_EXPIRES
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']

    # Not actually mapping yet
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )



    if test_config is None:
        # load the instance config
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    with app.app_context():
        from . import db
        db.init_app(app)

        from . import (auth, products, cart, orders, user, admin)
        app.register_blueprint(auth.bp)
        app.register_blueprint(products.bp)
        app.register_blueprint(cart.bp)
        app.register_blueprint(orders.bp)
        app.register_blueprint(user.bp)
        app.register_blueprint(admin.bp)

        @app.template_filter('cart_label')
        def cart_label(value):
            if value in ['0', 0, '']:
                return '<span class="cart-label">Корзина</span>'
            return f'<span class="cart-label cart-cost">{value} ₽</span>'


    @app.teardown_request
    def teardown_request(exception):
        if exception:
            app.logger.error(exception)
            db.rollback_db()

    return app


if __name__ == '__main__':
    create_app().run(debug=True)