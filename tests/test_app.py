import pytest
import json
from new_app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_accueil(client):
    reponse = client.get('/')
    assert reponse.status_code == 200
    assert b'Bonjour' in reponse.data

def test_sante(client):
    reponse = client.get('/sante')
    assert reponse.status_code == 200
    data = json.loads(reponse.data)
    assert data['statut'] == 'OK'
