import os

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from flask import Flask

from flask_jwt_extended import JWTManager


def create_app(test_config=None):
    """Create and configure the app"""
    app = Flask(__name__, instance_relative_config=True)

    ACCESS_EXPIRES = timedelta(hours=12)
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

        from . import (auth, views)
        app.register_blueprint(auth.bp)
        app.register_blueprint(views.bp)

    @app.teardown_request
    def teardown_request(exception):
        if exception:
            app.logger.error(exception)
            db.rollback_db()

    return app
