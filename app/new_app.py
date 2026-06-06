from flask import Flask, request, jsonify, abort

app = Flask(__name__)

taches = []
prochain_id = 1

@app.route('/', methods=['GET'])
def liste_taches():
    return jsonify(taches)

@app.route('/tache', methods=['POST'])
def ajouter_tache():
    global prochain_id
    data = request.get_json()
    if not data or 'titre' not in data:
        abort(400, "JSON attendu avec clé 'titre'")
    tache = {"id": prochain_id, "titre": data['titre']}
    prochain_id += 1
    taches.append(tache)
    return jsonify(tache), 201

@app.route('/tache/<int:id_tache>', methods=['GET'])
def get_tache(id_tache):
    for t in taches:
        if t['id'] == id_tache:
            return jsonify(t)
    abort(404, 'Tâche non trouvée')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
