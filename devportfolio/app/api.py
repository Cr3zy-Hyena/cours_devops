import logging

from flask import Blueprint, jsonify, request
from app.models import Project
from app import db

# Blueprint pour l'API REST des projets (préfixe '/api')
api = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


@api.route('/projets', methods=['GET'])
def lister():
    """Liste les projets.

    Paramètre GET optionnel : 'statut' pour filtrer par statut.
    Retourne JSON avec la liste sérialisée et le nombre total.
    """
    statut = request.args.get('statut')
    q = Project.query
    if statut:
        q = q.filter_by(statut=statut)
    projets = q.order_by(Project.created_at.desc()).all()
    return jsonify({'projets': [p.to_dict() for p in projets],
                    'total': len(projets)}), 200


@api.route('/projets/<int:id>', methods=['GET'])
def obtenir(id):
    """Récupère un projet par son `id`.

    Renvoie 404 si le projet n'existe pas.
    """
    p = Project.query.get_or_404(id)
    return jsonify(p.to_dict()), 200


@api.route('/projets', methods=['POST'])
def creer():
    """Crée un nouveau projet depuis un JSON envoyé en POST.

    Corps attendu (exemples de champs) : `titre`, `description`,
    `technologies`, `url_github`, `statut`.
    Retourne 400 si les champs obligatoires sont manquants.
    """
    data = request.get_json()
    if not data or not data.get('titre') or not data.get('description'):
        return jsonify({'erreur': 'titre et description requis'}), 400

    p = Project(titre=data['titre'],
                description=data['description'],
                technologies=data.get('technologies', ''),
                url_github=data.get('url_github'),
                statut=data.get('statut', 'en_cours'))
    db.session.add(p)
    db.session.commit()
    logger.info('Projet cree', extra={'id': p.id, 'titre': p.titre})
    return jsonify(p.to_dict()), 201


@api.route('/projets/<int:id>', methods=['DELETE'])
def supprimer(id):
    """Supprime un projet par son `id`.

    Renvoie un message de confirmation en JSON.
    """
    p = Project.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'message': f'Projet {id} supprime'}), 200


