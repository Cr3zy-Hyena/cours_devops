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

class SecurityQuestion(db.Model):
    __tablename__ = 'security_questions'
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question1 = db.Column(db.String(200), nullable=False)
    reponse1  = db.Column(db.String(255), nullable=False)
    question2 = db.Column(db.String(200), nullable=False)
    reponse2  = db.Column(db.String(255), nullable=False)
    question3 = db.Column(db.String(200), nullable=False)
    reponse3  = db.Column(db.String(255), nullable=False)

    user = db.relationship('User', backref=db.backref('security_questions', uselist=False))

    def verifier_reponses(self, r1, r2, r3):
        return (
            self.reponse1.lower().strip() == r1.lower().strip() and
            self.reponse2.lower().strip() == r2.lower().strip() and
            self.reponse3.lower().strip() == r3.lower().strip()
        )

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
        from datetime import datetime, timedelta
        import secrets
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
        from datetime import datetime
        return not self.used and datetime.utcnow() < self.expires_at

    class MessageSupport(db.Model):
        """Message envoyé par un utilisateur au support"""
        __tablename__ = 'messages_support'
        id          = db.Column(db.Integer, primary_key=True)
        user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        contenu     = db.Column(db.Text, nullable=False)
        reponse     = db.Column(db.Text, nullable=True)
        lu          = db.Column(db.Boolean, default=False)
        created_at  = db.Column(db.DateTime, default= datetime.utcnow)
        repondu_at  = db.Column(db.DateTime, nullable=True)

        user = db.relationship('User', backref='messages_support')
        