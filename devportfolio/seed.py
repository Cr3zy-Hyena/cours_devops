from app import create_app, db  # import de create_app et db depuis app/__init__.py
from app.models import Project  # import du modèle Project depuis app/models.py


def seed():  # fonction pour insérer des données initiales dans la base de données
    projets = [  # liste des projets à insérer
        Project(titre='Calculatrice Python',  # premier projet : titre
                description='CLI avec gestion des erreurs.',  # description du projet
                technologies='Python, pytest',  # technologies utilisées
                statut='termine'),  # statut du projet
        Project(titre='API REST Flask',  # deuxième projet : titre
                description='API de gestion de tache avec auth.',  # description du projet
                technologies='Flask, SQLAlchemy',  # technologies utilisées
                statut='en_cours'),  # statut du projet
        Project(titre='Devportfolio',  # troisième projet : titre
                description='Ce projet ! Pipeline Devops complet.',  # description du projet
                technologies='Flask, Docker, Github Actions',  # technologies utilisées
                url_github='https://github.com/TON_PSEUDO/devportfolio',  # lien du dépôt GitHub
                statut='en_cours'),  # statut du projet
    ]
    db.session.add_all(projets)  # ajouter tous les projets à la session SQLAlchemy
    db.session.commit()  # valider les changements dans la base de données
    print(f'{len(projets)} projets insérés.')  # afficher le nombre de projets inséré


if __name__ == '__main__':  # vérifier que le script est exécuté directement
    app = create_app()  # créer l'application Flask
    with app.app_context():  # créer un contexte d'application pour accéder à la base de données
        db.drop_all()  # supprimer toutes les tables
        db.create_all()  # créer toutes les tables
        seed()  # exécuter la fonction seed pour insérer les données
