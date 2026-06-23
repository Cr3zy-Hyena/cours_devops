import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

try:
    from prometheus_flask_exporter import PrometheusMetrics
    from prometheus_client import CollectorRegistry
except ImportError:
    PrometheusMetrics = None

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "main.login"
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def create_app(config=None):
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'sqlite:///devportfolio.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # CSRF désactivé en mode test uniquement
    app.config['WTF_CSRF_ENABLED'] = os.getenv('FLASK_ENV') != 'testing'

    if config:
        app.config.update(config)

    from app.logger import setup_logging
    setup_logging(app)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    if PrometheusMetrics:
        registry = CollectorRegistry()
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

    with app.app_context():
        try:
            from sqlalchemy import text
            db.session.execute(text(
                "ALTER TABLE projets ADD COLUMN IF NOT EXISTS verrouille BOOLEAN DEFAULT FALSE;"
            ))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Note: colonne verrouille déjà existante : {e}")

    return app