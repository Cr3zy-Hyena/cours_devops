import json


def test_lister_vide(auth_client):
    r = auth_client.get('/api/projets')
    assert r.status_code == 200
    data = json.loads(r.data)
    assert data['total'] == 0


def test_creer(auth_client):
    r = auth_client.post('/api/projets', json=
    {'titre': 'Nouveau', 'description': 'Desc', 'technologies': 'Flask'})
    assert r.status_code == 201
    data = json.loads(r.data)
    assert data['titre'] == 'Nouveau'


def test_creer_sans_titre(auth_client):
    r = auth_client.post('/api/projets', json={'description': 'Desc'})
    assert r.status_code == 400


def test_supprimer(auth_client, projet_test):
    r = auth_client.delete(f'/api/projets/{projet_test}')
    assert r.status_code == 200
    r2 = auth_client.get(f'/api/projets/{projet_test}')
    assert r2.status_code == 404