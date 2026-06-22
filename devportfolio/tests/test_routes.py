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

def test_projet_existant(client, projet_test):
    # Code pour te connecter ou simuler une session utilisateur ici
    # Exemple si tu as un helper ou si tu utilises le client de test Flask-Login :
    with client.session_transaction() as sess:
        sess['_user_id'] = '1' # ID d'un utilisateur de test en BDD
        sess['_fresh'] = True

    r = client.get(f'/projet/{projet_test}')
    assert r.status_code == 200
def test_projet_inexistant(client):
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True

    r = client.get('/projet/9999')
    assert r.status_code == 404