import pytest
from app import create_app, db
from app.models import Project, User


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,       # désactive CSRF pendant les tests
        'WTF_CSRF_CHECK_DEFAULT': False,  # désactive aussi la vérification par défaut
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client, app):
    with app.app_context():
        user = User(username='testuser')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()

    # Le CSRF étant désactivé, ce POST passe directement
    client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    return client


@pytest.fixture
def projet_test(app):
    with app.app_context():
        p = Project(titre='Test', description='Desc test',
                    technologies='Python')
        db.session.add(p)
        db.session.commit()
        return p.id