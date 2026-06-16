import time
import random
import requests

BASE_URL = "http://localhost:5000/api/projets"

def simuler_trafic():
    print("🚀 Début de la simulation de trafic vers l'API Flask...")
    
    # Liste de technologies pour la simulation de création
    techs = ["Flask", "React", "Docker", "Prometheus", "Grafana", "PostgreSQL"]
    
    while True:
        action = random.choice(["LISTER", "OBTENIR_OK", "OBTENIR_404", "CREER", "CREER_PROVENANT_D_ERREUR", "SUPPRIMER"])
        
        try:
            if action == "LISTER":
                # Simule un GET global ou avec filtre alternatif
                statut_filtre = random.choice([None, "en_cours", "termine"])
                params = {'statut': statut_filtre} if statut_filtre else {}
                res = requests.get(BASE_URL, params=params)
                print(f"[GET] Liste des projets (Filtre: {statut_filtre}) -> Code {res.status_code}")
                
            elif action == "OBTENIR_OK":
                # Tente de récupérer le projet ID 1 (en supposant qu'il existe)
                res = requests.get(f"{BASE_URL}/1")
                print(f"[GET] Projet ID 1 -> Code {res.status_code}")
                
            elif action == "OBTENIR_404":
                # ID inexistant pour déclencher le logger.warning de la route obtenir
                id_invalide = random.randint(9999, 99999)
                res = requests.get(f"{BASE_URL}/{id_invalide}")
                print(f"[GET] Projet ID {id_invalide} (Inexistant) -> Code {res.status_code}")
                
            elif action == "CREER":
                # Création valide
                payload = {
                    "titre": f"Projet Automatique {random.randint(100, 999)}",
                    "description": "Généré par le script de simulation",
                    "technologies": random.choice(techs),
                    "statut": random.choice(["en_cours", "termine"])
                }
                res = requests.post(BASE_URL, json=payload)
                print(f"[POST] Création projet -> Code {res.status_code}")
                
            elif action == "CREER_PROVENANT_D_ERREUR":
                # Envoi d'un payload incomplet (sans description) pour provoquer une 400
                payload = {"titre": "Projet Incomplet Invalide"}
                res = requests.post(BASE_URL, json=payload)
                print(f"[POST] Tentative invalide (Attendu: 400) -> Code {res.status_code}")
                
            elif action == "SUPPRIMER":
                # Tente de supprimer un ID aléatoire (provoque des 404 ou 200 selon la BDD)
                id_cible = random.randint(1, 5)
                res = requests.delete(f"{BASE_URL}/{id_cible}")
                print(f"[DELETE] Suppression ID {id_cible} -> Code {res.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Impossible de joindre l'API Flask. Vérifiez qu'elle tourne sur http://localhost:5000")
            
        # Attend entre 0.5 et 3 secondes avant la prochaine requête
        time.sleep(random.uniform(0.5, 3.0))

if __name__ == "__main__":
    simuler_trafic()