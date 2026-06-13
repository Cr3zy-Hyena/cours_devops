import pytest
from app import create_app, db
from app.models import Project


# Fixture principale : elle cree une application Flask configuree pour les tests.
@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })

    # Chaque test utilise une base SQLite en memoire, creee puis supprimee ici.
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


# Client de test permettant de simuler des requetes HTTP vers l'application.
@pytest.fixture
def client(app):
    return app.test_client()


# Donnee de test reutilisable : cree un projet et retourne son identifiant.
@pytest.fixture
def projet_test(app):
    with app.app_context():
        p = Project(titre='Test', description='Desc test',
                    technologies='Python')
        db.session.add(p)
        db.session.commit()
        return p.id
