# Projet Cours DevOps

Ce dépôt contient plusieurs projets DevOps développés ensemble :

- `cours_devops_jour/jour3` : application calculatrice Flask avec interface HTML, API JSON, Docker, Nginx et tests.
- `devportfolio` : application de portfolio pour développeurs avec Flask, PostgreSQL, Docker et GitHub Actions.

## Structure globale

- `cours_devops_jour/jour3/README.md` : documentation détaillée du projet calculatrice.
- `devportfolio/README.md` : documentation du projet DevPortfolio.
- `.github/workflows/ci-cd.yml` : workflow GitHub Actions pour le projet calculatrice.

## Résumé des sous-projets

### Calculatrice DevOps (`cours_devops_jour/jour3`)

- Application Flask avec :
  - GET `/` pour la page web de saisie
  - POST `/calculer` pour exécuter les opérations JSON
  - support de l’addition, soustraction, multiplication et division
- Dockerisé avec un `Dockerfile` optimisé
- Serveur Nginx en reverse-proxy via Docker Compose
- Tests unitaires avec `pytest`
- CI GitHub Actions dans `.github/workflows/ci-cd.yml`

### DevPortfolio (`devportfolio`)

- Application web de portfolio pour développeurs
- Stack annoncée : Flask, PostgreSQL, Docker, GitHub Actions, Nginx
- Lancement rapide prévu dans `devportfolio/README.md`

## Commandes de démarrage

### Calculatrice DevOps

```bash
cd cours_devops_jour/jour3
docker compose up -d --build
```

Ou en local :

```bash
python -m pip install -r requirements.txt
python app.py
```

### DevPortfolio

```bash
cd devportfolio
cp .env.example .env
docker compose up -d
```

## Notes

- Ouvre `cours_devops_jour/jour3/README.md` pour la documentation complète de la calculatrice.
- Ouvre `devportfolio/README.md` pour la documentation complète du portfolio.
- Le workflow GitHub Actions existant couvre au moins les tests, le build Docker et la publication Docker Hub pour le projet calculatrice.
