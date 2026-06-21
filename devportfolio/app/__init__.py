import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

try:
    from prometheus_flask_exporter import PrometheusMetrics
    from prometheus_client import CollectorRegistry
except ImportError:
    PrometheusMetrics = None


db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "main.login"

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
    login_manager.init_app(app)
    if PrometheusMetrics:
        registry = CollectorRegistry()  # registre isolé : évite les collisions
                                         # quand create_app() est appelé plusieurs
                                         # fois (ex: un nouvel objet app par test pytest)
        metrics = PrometheusMetrics(app, registry=registry)
        metrics.info('app_info', 'Info', version='1.0', service='devportfolio')

    from app.api import api
    from app.routes import main

    app.register_blueprint(api)
    app.register_blueprint(main)
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    return app