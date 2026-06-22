from flask_login import login_user


def test_accueil(auth_client):
    r = auth_client.get('/')
    assert r.status_code == 200
def test_health_check(client):
    import json
    r = client.get('/sante')
    assert r.status_code == 200
    data = json.loads(r.data)
    assert data['statut'] == 'ok'

def test_projet_existant(auth_client, projet_test):
    # Plus besoin de manipuler la session manuellement !
    r = auth_client.get(f'/projet/{projet_test}')
    assert r.status_code == 200


def test_projet_inexistant(auth_client):
    # Idem ici
    r = auth_client.get('/projet/9999')
    assert r.status_code == 404