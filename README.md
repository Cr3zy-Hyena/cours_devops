# Calculatrice DevOps

[![CI](https://github.com/Cr3zy-Hyena/calculatrice-devops/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Cr3zy-Hyena/calculatrice-devops/actions/workflows/ci-cd.yml)

## Description

Application Flask simple qui propose une interface HTML pour l'utilisateur et une API JSON pour effectuer des calculs.

- GET `/` : page web de saisie
- POST `/calculer` : exécute l'opération JSON et retourne le résultat
- Supporte addition, soustraction, multiplication, division
- Division par zéro renvoie une erreur 400 avec message clair

## Structure

- `cours_devops_jour/jour3/app.py` : application Flask
- `cours_devops_jour/jour3/calc.py` : logique de calcul
- `cours_devops_jour/jour3/templates/index.html` : interface utilisateur
- `cours_devops_jour/jour3/requirements.txt` : dépendances Python
- `cours_devops_jour/jour3/Dockerfile` : image Docker optimisée
- `docker-compose.yml` : application + Nginx reverse proxy
- `.github/workflows/ci-cd.yml` : pipeline CI GitHub Actions

## Installation locale

```bash
python -m pip install -r cours_devops_jour/jour3/requirements.txt
python cours_devops_jour/jour3/app.py
```

Ouvrez ensuite `http://localhost:5000`.

## Exemples d'utilisation de l'API

```bash
curl -X POST http://localhost:5000/calculer \
  -H "Content-Type: application/json" \
  -d '{"a": 6, "b": 2, "op": "div"}'
```

## Docker

```bash
docker compose up -d --build
```

L'application sera accessible sur `http://localhost`.

## Tests

```bash
python -m pytest -q cours_devops_jour/jour3/tests -q
```

## GitHub Actions

Le workflow exécute :

1. tests unitaires
2. build et publication Docker Hub
3. vérification du déploiement

## Remarques

- Ajoutez les secrets `DOCKERHUB_USERNAME` et `DOCKERHUB_TOKEN` dans GitHub pour la publication Docker Hub.

