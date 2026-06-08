from flask import Flask     #import app
from flask_sqlalchemy import SQLAlchemy     #base de données
import os   #pour les variables d'environnement

db=SQLAlchemy()         #instance de la base de données
def create_app(config=None):    #sera True pour les tests et None pour la prod
    app=Flask(__name__)         #création de l'application Flask
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')   #clé secrète pour les sessions
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL','sqlite://devportfolio.db')    #URI de la base de données, par défaut une base SQLite locale
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False    #désactive le suivi des modifications pour économiser des ressources
    if config: 
        app.config.update(config)  #mise à jour de la configuration avec les paramètres spécifiques (ex: pour les tests)
    db.init_app(app)               #initialsation de la base de données
    from app.routes import main    #import des routes
    app.register_blueprint(main)   #enregistrement des routes
    with app.app_context():        #création de la base de données
        db.create_all()            #crée les tables définies dans les modèles
    return app                     #création de l'application