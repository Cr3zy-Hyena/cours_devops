"""
Script de simulation de trafic pour DevPortfolio.

Genere des requetes variees (GET/POST/DELETE) sur toutes les routes de
l'app, y compris des cas d'erreur (404, 400), afin que les metriques
Prometheus exposees par prometheus_flask_exporter (compteurs de requetes,
durees, codes HTTP...) aient des donnees a afficher.

Usage:
    python simulate_traffic.py

Variables d'environnement optionnelles:
    APP_URL   -> URL de base de l'app (defaut: http://localhost:5000)
    DURATION  -> duree de la simulation en secondes (defaut: 120)
    PAUSE     -> pause entre deux requetes en secondes (defaut: 0.3)
"""

import os
import random
import time

import requests

BASE_URL = os.getenv('APP_URL', 'http://localhost:5000')
DURATION = float(os.getenv('DURATION', '120'))
PAUSE = float(os.getenv('PAUSE', '0.3'))

SAMPLE_PROJECTS = [
    {
        'titre': 'Portfolio DevOps',
        'description': 'Pipeline CI/CD avec Docker et GitHub Actions',
        'technologies': 'Python, Flask, Docker',
        'statut': 'en_cours',
    },
    {
        'titre': 'API Meteo',
        'description': 'API REST renvoyant des previsions meteo',
        'technologies': 'FastAPI, PostgreSQL',
        'statut': 'termine',
    },
    {
        'titre': 'Bot Discord',
        'description': 'Bot de moderation automatique pour un serveur Discord',
        'technologies': 'Python, discord.py',
        'statut': 'en_cours',
    },
    {
        'titre': 'Site vitrine',
        'description': 'Site vitrine pour un artisan local',
        'technologies': 'HTML, CSS, JavaScript',
        'statut': 'termine',
    },
]


def hit(method, path, **kwargs):
    """Effectue une requete HTTP et affiche le resultat."""
    url = f"{BASE_URL}{path}"
    try:
        r = requests.request(method, url, timeout=5, **kwargs)
        print(f"{method:6} {path:28} -> {r.status_code}")
        return r
    except requests.RequestException as e:
        print(f"{method:6} {path:28} -> ERREUR ({e})")
        return None


def simulate_traffic(duration_seconds, pause):
    created_ids = []
    end_time = time.time() + duration_seconds

    actions = [
        'accueil', 'a_propos', 'sante',
        'liste_projets', 'liste_filtree',
        'creer', 'creer_invalide',
        'obtenir', 'obtenir_inexistant',
        'detail_html',
        'supprimer',
    ]

    while time.time() < end_time:
        action = random.choice(actions)

        if action == 'accueil':
            hit('GET', '/')
        elif action == 'a_propos':
            hit('GET', '/a-propos')
        elif action == 'sante':
            hit('GET', '/sante')
        elif action == 'liste_projets':
            hit('GET', '/api/projets')
        elif action == 'liste_filtree':
            statut = random.choice(['en_cours', 'termine'])
            hit('GET', '/api/projets', params={'statut': statut})
        elif action == 'creer':
            payload = random.choice(SAMPLE_PROJECTS)
            r = hit('POST', '/api/projets', json=payload)
            if r is not None and r.status_code == 201:
                created_ids.append(r.json()['id'])
        elif action == 'creer_invalide':
            # Manque le champ 'description' -> doit renvoyer 400
            hit('POST', '/api/projets', json={'titre': 'Projet incomplet'})
        elif action == 'obtenir':
            id_ = random.choice(created_ids) if created_ids else 1
            hit('GET', f'/api/projets/{id_}')
        elif action == 'obtenir_inexistant':
            hit('GET', '/api/projets/999999')
        elif action == 'detail_html':
            id_ = random.choice(created_ids) if created_ids else 1
            hit('GET', f'/projet/{id_}')
        elif action == 'supprimer':
            if created_ids:
                id_ = created_ids.pop()
                hit('DELETE', f'/api/projets/{id_}')
            else:
                hit('DELETE', '/api/projets/999999')

        time.sleep(pause * random.uniform(0.5, 1.5))


if __name__ == '__main__':
    print(f"Simulation de trafic vers {BASE_URL} pendant {DURATION:.0f}s...\n")
    simulate_traffic(DURATION, PAUSE)
    print("\nSimulation terminee.")