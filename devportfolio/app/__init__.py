import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def create_app(config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'sqlite:///devportfolio.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if config:
        app.config.update(config)

    from app.logger import setup_logging

    setup_logging(app)
    db.init_app(app)

    from app.api import api
    from app.routes import main

    app.register_blueprint(api)
    app.register_blueprint(main)

    return app
