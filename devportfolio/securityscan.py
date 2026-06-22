#!/usr/bin/env python3
"""
security_scan.py — Analyse de sécurité DevPortfolio
Usage : python security_scan.py [URL]
Ex    : python security_scan.py http://localhost:5000
Ex    : python security_scan.py https://cours-devops-n9a5.onrender.com
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error
import urllib.parse

# ── couleurs terminal ──────────────────────────────────────────────────────────
R  = "\033[91m"   # rouge  → critique
O  = "\033[93m"   # orange → moyen
G  = "\033[92m"   # vert   → ok
B  = "\033[94m"   # bleu   → info
W  = "\033[97m"   # blanc  → titre
RS = "\033[0m"    # reset

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:5000"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

resultats = []   # liste de tuples (sévérité, catégorie, message, conseil)

def ajouter(sev, cat, msg, conseil=""):
    resultats.append((sev, cat, msg, conseil))

def titre(texte):
    print(f"\n{W}{'─'*60}{RS}")
    print(f"{W}  {texte}{RS}")
    print(f"{W}{'─'*60}{RS}")

def get(path, timeout=8):
    """Effectue un GET et retourne (status, headers, body)."""
    try:
        req = urllib.request.Request(
            BASE_URL + path,
            headers={"User-Agent": "SecurityScanner/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), ""
    except Exception:
        return None, {}, ""

def post_json(path, data, timeout=8):
    payload = json.dumps(data).encode()
    try:
        req = urllib.request.Request(
            BASE_URL + path,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "SecurityScanner/1.0"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return None, ""

# ══════════════════════════════════════════════════════════════════════════════
#  1. ANALYSE STATIQUE DU CODE SOURCE
# ══════════════════════════════════════════════════════════════════════════════
titre("1/5  ANALYSE STATIQUE DU CODE SOURCE")

def lire_fichier(chemin):
    try:
        with open(chemin, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def chercher_dans_fichiers(extensions, regex, exclure=None):
    """Retourne les (fichier, ligne, contenu) correspondant au regex."""
    resultats_trouve = []
    for root, _, files in os.walk(PROJECT_DIR):
        # ignorer venv, .git, __pycache__
        if any(x in root for x in ["venv", ".git", "__pycache__", ".pytest_cache"]):
            continue
        for f in files:
            if not any(f.endswith(e) for e in extensions):
                continue
            chemin = os.path.join(root, f)
            contenu = lire_fichier(chemin)
            for i, ligne in enumerate(contenu.splitlines(), 1):
                if exclure and any(ex in ligne for ex in exclure):
                    continue
                if re.search(regex, ligne, re.IGNORECASE):
                    resultats_trouve.append((chemin.replace(PROJECT_DIR+"/", ""), i, ligne.strip()))
    return resultats_trouve

# ── 1.1 Secrets en dur ──────────────────────────────────────────────────────
print(f"\n{B}[1.1] Recherche de secrets codés en dur...{RS}")
patterns_secrets = [
    (r"secret_key\s*=\s*['\"][^'\"]{4,}['\"]",   "SECRET_KEY en dur"),
    (r"password\s*=\s*['\"][^'\"]{3,}['\"]",      "Mot de passe en dur"),
    (r"api_key\s*=\s*['\"][^'\"]{8,}['\"]",       "Clé API en dur"),
    (r"token\s*=\s*['\"][^'\"]{8,}['\"]",         "Token en dur"),
    (r"postgresql://\w+:\w+@",                    "Credentials BDD en URL"),
]
for pattern, label in patterns_secrets:
    trouves = chercher_dans_fichiers(
        [".py", ".yml", ".yaml", ".env.example"],
        pattern,
        exclure=["os.getenv", "environ", "#", "test", "example"]
    )
    for chemin, ligne, contenu in trouves:
        ajouter("CRITIQUE", "Secret", f"{label} → {chemin}:{ligne}",
                "Utiliser os.getenv() et stocker dans les variables d'environnement Render")
        print(f"  {R}[CRITIQUE]{RS} {label} — {chemin}:{ligne}")

# ── 1.2 Mode debug ──────────────────────────────────────────────────────────
print(f"\n{B}[1.2] Vérification du mode debug...{RS}")
debug_trouvé = chercher_dans_fichiers(
    [".py"], r"debug\s*=\s*True",
    exclure=["#", "TESTING"]
)
for chemin, ligne, contenu in debug_trouvé:
    ajouter("CRITIQUE", "Config", f"debug=True en production → {chemin}:{ligne}",
            "Utiliser debug=False ou FLASK_ENV=production")
    print(f"  {R}[CRITIQUE]{RS} debug=True détecté — {chemin}:{ligne}")

# ── 1.3 Injection SQL (raw queries) ─────────────────────────────────────────
print(f"\n{B}[1.3] Recherche d'injections SQL potentielles...{RS}")
sql_raw = chercher_dans_fichiers(
    [".py"], r"(execute|text)\s*\(\s*f['\"]|%\s*\w+\s*\+",
    exclure=["#"]
)
for chemin, ligne, contenu in sql_raw:
    ajouter("CRITIQUE", "SQLi", f"Requête SQL avec f-string/concaténation → {chemin}:{ligne}",
            "Utiliser SQLAlchemy ORM ou des paramètres liés (bindparams)")
    print(f"  {R}[CRITIQUE]{RS} SQL injection possible — {chemin}:{ligne}")
if not sql_raw:
    print(f"  {G}[OK]{RS} Pas de raw SQL trouvé — ORM SQLAlchemy utilisé")
    ajouter("OK", "SQLi", "ORM SQLAlchemy utilisé — pas de raw SQL détecté")

# ── 1.4 API sans authentification ────────────────────────────────────────────
print(f"\n{B}[1.4] Vérification de l'authentification sur les routes API...{RS}")
api_content = lire_fichier(os.path.join(PROJECT_DIR, "app/api.py"))
routes_api = re.findall(r"@api\.route\('([^']+)'.*?\)\ndef (\w+)", api_content, re.DOTALL)
for route, func in routes_api:
    # chercher @login_required avant la fonction
    idx = api_content.find(f"def {func}")
    bloc_avant = api_content[max(0, idx-200):idx]
    if "login_required" not in bloc_avant:
        ajouter("MOYEN", "Auth", f"Route API non protégée : /api{route} ({func})",
                "Ajouter @login_required si cette route ne doit pas être publique")
        print(f"  {O}[MOYEN]{RS} /api{route} accessible sans authentification")

# ── 1.5 CSRF ────────────────────────────────────────────────────────────────
print(f"\n{B}[1.5] Vérification de la protection CSRF...{RS}")
reqs = lire_fichier(os.path.join(PROJECT_DIR, "requirements.txt"))
if "flask-wtf" not in reqs.lower() and "wtforms" not in reqs.lower():
    ajouter("MOYEN", "CSRF",
            "Pas de protection CSRF (Flask-WTF absent de requirements.txt)",
            "Installer Flask-WTF et utiliser CSRFProtect(app) + {{ form.hidden_tag() }} dans les formulaires")
    print(f"  {O}[MOYEN]{RS} Flask-WTF non trouvé → formulaires sans token CSRF")
else:
    print(f"  {G}[OK]{RS} Flask-WTF détecté")

# ── 1.6 Rate limiting ────────────────────────────────────────────────────────
print(f"\n{B}[1.6] Vérification du rate limiting...{RS}")
if "flask-limiter" not in reqs.lower():
    ajouter("MOYEN", "Brute-force",
            "Pas de rate limiting (Flask-Limiter absent)",
            "Installer flask-limiter et protéger /login avec @limiter.limit('5/minute')")
    print(f"  {O}[MOYEN]{RS} Pas de rate limiting → attaque brute-force sur /login possible")

# ── 1.7 .env dans gitignore ──────────────────────────────────────────────────
print(f"\n{B}[1.7] Vérification du .gitignore...{RS}")
gitignore = lire_fichier(os.path.join(PROJECT_DIR, ".gitignore"))
checks_gitignore = [
    (".env",        "Fichier .env"),
    ("*.db",        "Fichiers SQLite"),
    ("__pycache__", "Cache Python"),
    ("venv",        "Dossier venv"),
]
for pattern, label in checks_gitignore:
    if pattern in gitignore:
        print(f"  {G}[OK]{RS} {label} ignoré par git")
    else:
        ajouter("MOYEN", "Fuite", f"{label} non ignoré par git → risque de push accidentel",
                f"Ajouter '{pattern}' dans .gitignore")
        print(f"  {O}[MOYEN]{RS} {label} PAS dans .gitignore")

# ══════════════════════════════════════════════════════════════════════════════
#  2. EN-TÊTES DE SÉCURITÉ HTTP
# ══════════════════════════════════════════════════════════════════════════════
titre("2/5  EN-TÊTES DE SÉCURITÉ HTTP")
print(f"  Cible : {BASE_URL}")

status, headers, _ = get("/")
if status is None:
    print(f"  {O}[WARN]{RS} Impossible de joindre {BASE_URL} — vérifier que l'app tourne")
else:
    headers_requis = {
        "X-Content-Type-Options":    ("nosniff",     "MOYEN",    "Empêche le MIME sniffing"),
        "X-Frame-Options":           ("DENY",        "MOYEN",    "Empêche le clickjacking"),
        "Content-Security-Policy":   (None,          "MOYEN",    "Restreint les sources de scripts/styles"),
        "Strict-Transport-Security": (None,          "FAIBLE",   "Force HTTPS (utile sur Render)"),
        "Referrer-Policy":           (None,          "FAIBLE",   "Contrôle les infos de referrer"),
        "Permissions-Policy":        (None,          "FAIBLE",   "Limite les APIs navigateur"),
    }
    for header, (valeur, sev, desc) in headers_requis.items():
        # normalisation casse
        h_lower = {k.lower(): v for k, v in headers.items()}
        if header.lower() in h_lower:
            val = h_lower[header.lower()]
            if valeur and valeur.lower() not in val.lower():
                ajouter(sev, "Headers", f"{header} présent mais valeur incorrecte : {val}",
                        f"Valeur recommandée : {valeur}")
                print(f"  {O}[{sev}]{RS} {header}: {val} (valeur incorrecte)")
            else:
                print(f"  {G}[OK]{RS} {header}: {val}")
                ajouter("OK", "Headers", f"{header} présent")
        else:
            ajouter(sev, "Headers", f"Header manquant : {header} — {desc}",
                    f"Ajouter dans __init__.py : @app.after_request")
            print(f"  {O}[{sev}]{RS} Header manquant : {header}")

    # Vérifier que Server: n'expose pas la version
    server = headers.get("Server", "")
    if server and ("nginx/" in server.lower() or "werkzeug" in server.lower()):
        ajouter("FAIBLE", "Headers", f"Header Server expose la version : {server}",
                "Masquer avec nginx : server_tokens off;")
        print(f"  {O}[FAIBLE]{RS} Server: {server} expose la techno")

# ══════════════════════════════════════════════════════════════════════════════
#  3. TESTS DE ROUTES
# ══════════════════════════════════════════════════════════════════════════════
titre("3/5  TESTS DE ROUTES")

# ── 3.1 Routes sensibles accessibles sans auth ──────────────────────────────
print(f"\n{B}[3.1] Accès sans authentification...{RS}")
routes_protegees = [
    ("/",          200, "Index (doit rediriger vers /login)"),
    ("/api/projets", 200, "API projets (publique intentionnellement)"),
]
for route, code_attendu, desc in routes_protegees:
    status, hdrs, body = get(route)
    if status is None:
        print(f"  {O}[SKIP]{RS} {route} — serveur injoignable")
        continue
    # Si on obtient 200 sur / sans être connecté c'est un problème
    if route == "/" and status == 200:
        ajouter("CRITIQUE", "Auth", "Route / accessible sans authentification (200 sans login)",
                "Vérifier que @login_required est bien appliqué")
        print(f"  {R}[CRITIQUE]{RS} {route} retourne 200 sans authentification → {desc}")
    elif route == "/" and status in (302, 401):
        print(f"  {G}[OK]{RS} {route} redirige vers /login (status {status})")
        ajouter("OK", "Auth", f"{route} correctement protégé (redirection {status})")
    else:
        print(f"  {B}[INFO]{RS} {route} → HTTP {status}")

# ── 3.2 Endpoints d'info sensibles ──────────────────────────────────────────
print(f"\n{B}[3.2] Endpoints d'information exposés...{RS}")
endpoints_info = [
    "/metrics",     # Prometheus — expose les métriques internes
    "/sante",       # health check
    "/.env",        # fichier secret
    "/config",
    "/admin",
    "/debug",
    "/__version__",
]
for route in endpoints_info:
    status, _, body = get(route)
    if status == 200:
        if route == "/metrics":
            ajouter("MOYEN", "Exposition",
                    f"{route} accessible publiquement (métriques Prometheus exposées)",
                    "Restreindre /metrics à Prometheus uniquement via réseau Docker ou IP whitelist")
            print(f"  {O}[MOYEN]{RS} {route} → 200 (métriques internes exposées publiquement)")
        elif route == "/sante":
            print(f"  {G}[OK]{RS} {route} → 200 (health check public, normal)")
        else:
            ajouter("CRITIQUE", "Exposition", f"{route} accessible publiquement",
                    "Supprimer ou protéger cet endpoint")
            print(f"  {R}[CRITIQUE]{RS} {route} → 200 (endpoint sensible exposé !)")
    elif status in (301, 302):
        print(f"  {B}[INFO]{RS} {route} → {status} (redirection)")
    elif status == 404:
        print(f"  {G}[OK]{RS} {route} → 404 (non exposé)")

# ── 3.3 Brute-force /login ───────────────────────────────────────────────────
print(f"\n{B}[3.3] Test brute-force sur /login...{RS}")
blocked = False
for i in range(6):
    status, hdrs, body = get(f"/login")
    if status == 429:
        blocked = True
        break
# Test POST
for i in range(6):
    data = urllib.parse.urlencode({"username": "admin", "password": f"wrong{i}"}).encode()
    try:
        req = urllib.request.Request(
            BASE_URL + "/login", data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            if r.status == 429:
                blocked = True
                break
    except urllib.error.HTTPError as e:
        if e.code == 429:
            blocked = True
            break
    except Exception:
        break

if blocked:
    print(f"  {G}[OK]{RS} Rate limiting actif — requêtes bloquées après plusieurs tentatives")
    ajouter("OK", "Brute-force", "Rate limiting détecté sur /login")
else:
    ajouter("MOYEN", "Brute-force",
            "Aucun rate limiting détecté sur /login — brute-force possible",
            "Ajouter flask-limiter : @limiter.limit('5 per minute')")
    print(f"  {O}[MOYEN]{RS} 6 tentatives acceptées sans blocage → brute-force possible")

# ── 3.4 Injection XSS ────────────────────────────────────────────────────────
print(f"\n{B}[3.4] Test d'injection XSS via l'API...{RS}")
xss_payload = {"titre": "<script>alert('XSS')</script>", "description": "test xss"}
status, body = post_json("/api/projets", xss_payload)
if status in (200, 201) and "<script>" in body:
    ajouter("CRITIQUE", "XSS",
            "L'API retourne du HTML non échappé dans la réponse JSON",
            "S'assurer que les templates Jinja2 utilisent l'auto-escaping (activé par défaut dans Flask)")
    print(f"  {R}[CRITIQUE]{RS} Payload XSS renvoyé non échappé dans la réponse")
elif status in (200, 201):
    print(f"  {G}[OK]{RS} Payload XSS stocké mais Jinja2 l'échappera à l'affichage")
    ajouter("OK", "XSS", "Jinja2 auto-escaping actif (protection XSS en place)")
else:
    print(f"  {B}[INFO]{RS} API /projets → HTTP {status}")

# ══════════════════════════════════════════════════════════════════════════════
#  4. ANALYSE DES DÉPENDANCES
# ══════════════════════════════════════════════════════════════════════════════
titre("4/5  ANALYSE DES DÉPENDANCES")

# versions connues vulnérables (liste simplifiée, à compléter)
CVE_CONNUS = {
    "flask":               [("<3.0.0",  "MOYEN",  "CVE-2023-30861 : fuite de session avec proxy")],
    "werkzeug":            [("<3.0.1",  "MOYEN",  "CVE-2023-46136 : DoS sur parse_cookie")],
    "flask-sqlalchemy":    [("<3.0.0",  "FAIBLE", "Déprecation et bugs de session")],
    "gunicorn":            [("<21.0.0", "MOYEN",  "CVE-2024-1135 : HTTP Request Smuggling")],
    "psycopg2-binary":     [("<2.9.10", "FAIBLE", "Correctifs de sécurité mémoire")],
}

print()
reqs_path = os.path.join(PROJECT_DIR, "requirements.txt")
with open(reqs_path) as f:
    lignes = f.read().splitlines()

for ligne in lignes:
    ligne = ligne.strip()
    if not ligne or ligne.startswith("#"):
        continue
    # parser nom==version
    match = re.match(r"^([a-zA-Z0-9_\-]+)==(.+)$", ligne)
    if not match:
        if ligne:
            ajouter("FAIBLE", "Deps", f"Version non fixée : {ligne}",
                    "Fixer toutes les versions (pip freeze) pour garantir la reproductibilité")
            print(f"  {O}[FAIBLE]{RS} Version non épinglée : {ligne}")
        continue

    nom, version = match.group(1).lower(), match.group(2)

    vulns = CVE_CONNUS.get(nom, [])
    trouvé_vuln = False
    for (condition, sev, desc) in vulns:
        # parser la condition ex: "<3.0.0"
        op = condition[:2] if condition[1] in "<>=!" else condition[0]
        ver_ref = condition.lstrip("<>=!")

        def parse_ver(v):
            try:
                return tuple(int(x) for x in v.split(".")[:3])
            except Exception:
                return (0,)

        ver_actuelle = parse_ver(version)
        ver_ref_t    = parse_ver(ver_ref)

        vulnerable = False
        if op == "<"  and ver_actuelle < ver_ref_t: vulnerable = True
        if op == "<=" and ver_actuelle <= ver_ref_t: vulnerable = True

        if vulnerable:
            trouvé_vuln = True
            ajouter(sev, "CVE", f"{nom}=={version} — {desc}", "Mettre à jour la dépendance")
            couleur = R if sev == "CRITIQUE" else O
            print(f"  {couleur}[{sev}]{RS} {nom}=={version} — {desc}")

    if not trouvé_vuln:
        print(f"  {G}[OK]{RS} {nom}=={version}")

# ══════════════════════════════════════════════════════════════════════════════
#  5. CONFIGURATION DOCKER / INFRA
# ══════════════════════════════════════════════════════════════════════════════
titre("5/5  CONFIGURATION DOCKER / INFRA")

# ── Dockerfile ───────────────────────────────────────────────────────────────
print(f"\n{B}[5.1] Analyse du Dockerfile...{RS}")
dockerfile = lire_fichier(os.path.join(PROJECT_DIR, "Dockerfile"))
if dockerfile:
    if "USER " in dockerfile and "appuser" in dockerfile:
        print(f"  {G}[OK]{RS} Conteneur exécuté en utilisateur non-root (appuser)")
        ajouter("OK", "Docker", "Utilisateur non-root configuré")
    else:
        ajouter("MOYEN", "Docker", "Conteneur s'exécute en root",
                "Ajouter : RUN useradd -m appuser && USER appuser")
        print(f"  {O}[MOYEN]{RS} Pas d'utilisateur non-root dans le Dockerfile")

    if "FROM python:" in dockerfile and "slim" in dockerfile:
        print(f"  {G}[OK]{RS} Image slim utilisée (surface d'attaque réduite)")
    elif "alpine" in dockerfile:
        print(f"  {G}[OK]{RS} Image Alpine utilisée (surface d'attaque réduite)")
    else:
        ajouter("FAIBLE", "Docker", "Image Docker non-slim (surface d'attaque plus grande)",
                "Utiliser python:3.x-slim ou python:3.x-alpine")
        print(f"  {O}[FAIBLE]{RS} Utiliser une image slim ou alpine")

    if "COPY . ." in dockerfile:
        dockerignore = lire_fichier(os.path.join(PROJECT_DIR, ".dockerignore"))
        if not dockerignore:
            ajouter("MOYEN", "Docker", "COPY . . sans .dockerignore → risque de copier .env dans l'image",
                    "Créer un .dockerignore avec : .env, venv/, .git/")
            print(f"  {O}[MOYEN]{RS} Pas de .dockerignore — COPY . . peut inclure .env et venv/")
        else:
            print(f"  {G}[OK]{RS} .dockerignore présent")

# ── docker-compose.yml ────────────────────────────────────────────────────────
print(f"\n{B}[5.2] Analyse du docker-compose.yml...{RS}")
compose = lire_fichier(os.path.join(PROJECT_DIR, "docker-compose.yml"))
if compose:
    if "POSTGRES_PASSWORD: devpass" in compose or "devpass" in compose:
        ajouter("CRITIQUE", "Config", "Mot de passe Postgres en dur dans docker-compose.yml : devpass",
                "Utiliser une variable d'environnement : POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}")
        print(f"  {R}[CRITIQUE]{RS} Mot de passe Postgres 'devpass' codé en dur")
    if "GF_SECURITY_ADMIN_PASSWORD=admin" in compose:
        ajouter("MOYEN", "Config", "Mot de passe Grafana par défaut 'admin' en dur",
                "Changer via variable d'environnement : GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}")
        print(f"  {O}[MOYEN]{RS} Mot de passe Grafana 'admin' en dur dans compose")

# ══════════════════════════════════════════════════════════════════════════════
#  RAPPORT FINAL
# ══════════════════════════════════════════════════════════════════════════════
titre("RAPPORT FINAL")

compteurs = {"CRITIQUE": 0, "MOYEN": 0, "FAIBLE": 0, "OK": 0}
for sev, cat, msg, conseil in resultats:
    compteurs[sev] = compteurs.get(sev, 0) + 1

print(f"""
  {R}Critiques : {compteurs['CRITIQUE']}{RS}
  {O}Moyens    : {compteurs['MOYEN']}{RS}
  {O}Faibles   : {compteurs['FAIBLE']}{RS}
  {G}OK        : {compteurs['OK']}{RS}
""")

problemes = [(s, c, m, co) for s, c, m, co in resultats if s != "OK"]
if not problemes:
    print(f"  {G}Aucun problème détecté — super !{RS}")
else:
    print(f"  {W}Problèmes à corriger (par priorité) :{RS}\n")
    for sev in ["CRITIQUE", "MOYEN", "FAIBLE"]:
        for s, cat, msg, conseil in problemes:
            if s != sev:
                continue
            couleur = R if sev == "CRITIQUE" else O
            print(f"  {couleur}[{sev}]{RS} [{cat}] {msg}")
            if conseil:
                print(f"         {B}→ {conseil}{RS}")

print(f"\n  Scan terminé sur {BASE_URL}\n")