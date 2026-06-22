from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class Project(db.Model):
    __tablename__ = 'projets'
    id          = db.Column(db.Integer, primary_key=True)
    titre       = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    technologies= db.Column(db.String(500))
    url_github  = db.Column(db.String(500))
    url_demo    = db.Column(db.String(500))
    statut      = db.Column(db.String(50), default='en_cours')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    verrouille  = db.Column(db.Boolean, default=False)  # True = contenu caché jusqu'au paiement

    def to_dict(self):
        return {
            'id': self.id,
            'titre': self.titre,
            'description': self.description,
            'technologies': self.technologies,
            'url_github': self.url_github,
            'url_demo': self.url_demo,
            'statut': self.statut,
            'created_at': self.created_at.isoformat(),
            'verrouille': self.verrouille,
        }

    def __repr__(self):
        return f'<Project {self.titre}>'


class Paiement(db.Model):
    """Trace chaque paiement Stripe réussi pour déverrouiller un projet."""
    __tablename__ = 'paiements'
    id                 = db.Column(db.Integer, primary_key=True)
    projet_id          = db.Column(db.Integer, db.ForeignKey('projets.id'), nullable=False)
    user_id            = db.Column(db.Integer, db.ForeignKey('users.id'),   nullable=False)
    stripe_session_id  = db.Column(db.String(200), unique=True, nullable=False)  # ID session Stripe
    montant_centimes   = db.Column(db.Integer, default=100)   # 100 = 1,00 €
    statut             = db.Column(db.String(50), default='en_attente')  # en_attente | reussi | echec
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)

    projet = db.relationship('Project', backref='paiements')
    user   = db.relationship('User',    backref='paiements')

    def __repr__(self):
        return f'<Paiement projet={self.projet_id} statut={self.statut}>'


from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
