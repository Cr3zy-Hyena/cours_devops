import json

def test_lister_vide(client):
    r = client.get('/api/projets')
    assert r.status_code == 200
    data = json.loads(r.data)
    assert data['total'] == 0

def test_creer(client):
    r = client.post('/api/projets', json=
    {'titre':'Nouveau','description':'Desc','technologies':'Flask'})
    assert r.status_code == 201
    data = json.loads(r.data)
    assert data['titre'] == 'Nouveau'

def test_creer_sans_titre(client):
    r = client.post('/api/projets', json={'description':'Desc'})
    assert r.status_code == 400

def test_supprimer(client, projet_test):
    r = client.delete(f'/api/projets/{projet_test}')
    assert r.status_code == 200
    r2 = client.get(f'/api/projets/{projet_test}')
    assert r2.status_code == 404
    


           

    