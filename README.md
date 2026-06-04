# Todo Stack - Flask + Nginx + Docker

## Lancer la stack
docker compose up -d --build

## Tester
curl http://localhost/
curl -X POST http://localhost/tache -H "Content-Type: application/json" -d '{"titre": "Test"}'
curl http://localhost/tache/1

## Arrêter
docker compose down# Mon Projet DevOps\nCe projet est créé pendant mon cours DevOps.
