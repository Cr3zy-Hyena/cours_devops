from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Instance SQLAlchemy exportée pour être utilisée dans les autres modules
db = SQLAlchemy()


def create_app(config=None):
    """Crée et configure l'application Flask.

    Les blueprints sont importés et enregistrés ici pour éviter
    les importations circulaires lors de l'import au niveau module.
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///devportfolio.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if config:
        app.config.update(config)

    # Initialiser l'extension SQLAlchemy avec l'app
    db.init_app(app)

    # Importer et enregistrer les blueprints après la création de l'app
    from app.api import api
    app.register_blueprint(api)
    from app.routes import main
    app.register_blueprint(main)

    return app