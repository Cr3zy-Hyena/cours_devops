from app import create_app, db
from app.models import Project, User

PROJETS_INITIAUX = [
    dict(titre='Calculatrice Python', description='CLI avec gestion des erreurs.', technologies='Python, pytest', statut='termine', verrouille=False),
    dict(titre='API REST Flask', description='API de gestion de tâches avec auth.', technologies='Flask, SQLAlchemy', statut='en_cours', verrouille=False),
    dict(titre='Devportfolio', description='Ce projet ! Pipeline DevOps complet.', technologies='Flask, Docker, GitHub Actions', statut='en_cours', verrouille=False),
    dict(titre='Projet Premium 🔒', description='Contenu exclusif — déverrouillez pour accéder au code source complet.', technologies='À découvrir après déverrouillage...', statut='termine', verrouille=True),
]

def seed():
    projets = [Project(**data) for data in PROJETS_INITIAUX]
    db.session.add_all(projets)
    db.session.commit()
    print(f'{len(projets)} projets insérés.')

def seed_if_empty():
    if Project.query.count() == 0:
        seed()
    else:
        # Ajouter uniquement les projets manquants par titre
        titres_existants = {p.titre for p in Project.query.all()}
        for data in PROJETS_INITIAUX:
            if data['titre'] not in titres_existants:
                db.session.add(Project(**data))
                print(f"Projet ajouté : {data['titre']}")
        db.session.commit()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed()
