def test_accueil(client):
    r = client.get('/')
    assert r.status_code == 200
def test_health_check(client):
    import json
    r = client.get('/sante')
    assert r.status_code == 200
    data = json.loads(r.data)
    assert data['statut'] == 'ok'
def test_projet_inexistant(client):
    r = client.get('/projet/9999')
    assert r.status_code == 404
def test_projet_existant(client, projet_test):
    r = client.get(f'/projet/{projet_test}')
    assert r.status_code == 200