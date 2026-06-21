from app import db  # import de l'instance de base de données SQLAlchemy depuis app/__init__.py
from datetime import datetime  # import de datetime pour gérer les dates de création des projets
from werkzeug.security import generate_password_hash, check_password_hash

class Project(db.Model):  # définition du modèle Project qui correspond à une table SQL
    __tablename__ = 'projets'  # nom de la table dans la base de données
    id = db.Column(db.Integer, primary_key=True)  # identifiant unique du projet, clé primaire
    titre = db.Column(db.String(100), nullable=False)  # titre du projet, champ obligatoire
    description = db.Column(db.Text, nullable=False)  # description du projet, champ obligatoire
    technologies = db.Column(db.String(500))  # technologies utilisées, champ texte facultatif
    url_github = db.Column(db.String(500))  # URL du dépôt GitHub du projet
    url_demo = db.Column(db.String(500))  # URL de démonstration ou du site en ligne
    statut = db.Column(db.String(50), default='en_cours')  # statut du projet, valeur par défaut 'en_cours'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # date de création du projet

    def to_dict(self):  # méthode pour convertir l'objet en dictionnaire
        return {
            'id': self.id,  # identifiant du projet
            'titre': self.titre,  # titre du projet
            'description': self.description,  # description du projet
            'technologies': self.technologies,  # technologies associées au projet
            'url_github': self.url_github,  # lien GitHub du projet
            'url_demo': self.url_demo,  # lien de démonstration du projet
            'statut': self.statut,  # statut du projet
            'created_at': self.created_at.isoformat(),  # date de création formatée en ISO
        }


    def __repr__(self):  # méthode de représentation texte de l'objet
        return f'<Project {self.titre}>'  # chaîne affichée pour l'objet lors du débogage

from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)