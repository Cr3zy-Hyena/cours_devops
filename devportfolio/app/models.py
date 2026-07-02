from app import db
from datetime import datetime, timedelta
import secrets
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
    verrouille  = db.Column(db.Boolean, default=False)

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
    __tablename__ = 'paiements'
    id                 = db.Column(db.Integer, primary_key=True)
    projet_id          = db.Column(db.Integer, db.ForeignKey('projets.id'), nullable=False)
    user_id            = db.Column(db.Integer, db.ForeignKey('users.id'),   nullable=False)
    stripe_session_id  = db.Column(db.String(200), unique=True, nullable=False)
    montant_centimes   = db.Column(db.Integer, default=100)
    statut             = db.Column(db.String(50), default='en_attente')
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
    email         = db.Column(db.String(120), unique=True, nullable=False)
    email_verifie = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_active(self):
        return self.email_verifie


class EmailVerificationToken(db.Model):
    __tablename__ = 'email_verification_tokens'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token      = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used       = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='verification_tokens')

    @staticmethod
    def create_for_user(user):
        token = EmailVerificationToken(
            user_id=user.id,
            token=secrets.token_urlsafe(48),
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.session.add(token)
        db.session.commit()
        return token

    @property
    def is_valid(self):
        return not self.used and datetime.utcnow() < self.expires_at


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token      = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used       = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='reset_tokens')

    @staticmethod
    def create_for_user(user):
        PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({'used': True})
        token = PasswordResetToken(
            user_id=user.id,
            token=secrets.token_urlsafe(48),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.session.add(token)
        db.session.commit()
        return token

    @property
    def is_valid(self):
        return not self.used and datetime.utcnow() < self.expires_at