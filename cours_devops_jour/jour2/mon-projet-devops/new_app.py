from flask import Flask
import os
nom=os.getenv('APP_NAME', 'DevOps App')
app = Flask(__name__)


@app.route('/')
def accueil():
    return f'<h1>Bienvenue sur {nom} !</h1><p>Version 1.0</p>'


@app.route('/sante')
def sante():
    return {'statut': 'OK', 'service': 'mon-app', 'version': '1.0'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
