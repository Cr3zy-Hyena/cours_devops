import pytest
from app import create_app, db
from app.models import Project, User


# Fixture principale utilisee par les tests.
# Elle cree une application Flask configuree en mode test avec une base SQLite
# en memoire, ce qui evite de modifier la vraie base de donnees du projet.
@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })

    # Le contexte d'application permet a Flask-SQLAlchemy d'acceder a la config
    # et a la base de donnees pendant la creation et la suppression des tables.
    with app.app_context():
        # Creation des tables avant le test.
        db.create_all()

        # Le test s'execute ici avec l'application prete a etre utilisee.
        yield app

        # Nettoyage de la base apres le test.
        db.drop_all()


# Fixture qui fournit un client de test Flask.
# Elle permet de simuler des requetes HTTP sans lancer le serveur web.
@pytest.fixture
def client(app):
    return app.test_client()


# Fixture qui fournit un client deja authentifie.
# Cree un utilisateur de test puis se connecte via POST /login,
# pour les routes protegees par @login_required (ex: '/').
@pytest.fixture
def auth_client(client, app):
    with app.app_context():
        user = User(username='testuser')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()

    client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    return client


# Fixture de donnee de test.
# Elle ajoute un projet en base et retourne son identifiant pour les tests.
@pytest.fixture
def projet_test(app):
    with app.app_context():
        p = Project(titre='Test', description='Desc test',
                    technologies='Python')

        # Enregistrement du projet de test dans la base temporaire.
        db.session.add(p)
        db.session.commit()

        return p.id
