from app import create_app, db
from seed import seed_if_empty

app = create_app()

# Initialiser la BDD (migration simple)
with app.app_context():
    db.create_all()
    seed_if_empty()  # re-seed automatique si la table 'projets' est vide
                      # (cas Render : disque SQLite éphémère à chaque déploiement)

if __name__ == '__main__':
    app.run(debug=False)
