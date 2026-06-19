from app import create_app, db  # import de create_app et db depuis app/__init__.py
from app.models import Project  # import du modèle Project depuis app/models.py


PROJETS_INITIAUX = [  # données de démo, réutilisées par seed() et seed_if_empty()
    dict(titre='Calculatrice Python',
         description='CLI avec gestion des erreurs.',
         technologies='Python, pytest',
         statut='termine'),
    dict(titre='API REST Flask',
         description='API de gestion de tache avec auth.',
         technologies='Flask, SQLAlchemy',
         statut='en_cours'),
    dict(titre='Devportfolio',
         description='Ce projet ! Pipeline Devops complet.',
         technologies='Flask, Docker, Github Actions',
         url_github='https://github.com/TON_PSEUDO/devportfolio',
         statut='en_cours'),
]


def seed():  # insère les projets de démo (suppose la table vide)
    projets = [Project(**data) for data in PROJETS_INITIAUX]
    db.session.add_all(projets)
    db.session.commit()
    print(f'{len(projets)} projets insérés.')


def seed_if_empty():  # insère les projets seulement si la table est vide
    # Utile en production (Render) : le disque SQLite est éphémère et se
    # réinitialise à chaque déploiement/redémarrage. Cette fonction est
    # appelée au démarrage de l'app (voir run.py) pour ne jamais laisser
    # la page "Mes Projets" vide.
    if Project.query.count() == 0:
        seed()


if __name__ == '__main__':  # reset complet, à lancer manuellement en local
    app = create_app()
    with app.app_context():
        db.drop_all()  # supprimer toutes les tables
        db.create_all()  # créer toutes les tables
        seed()  # exécuter la fonction seed pour insérer les données
