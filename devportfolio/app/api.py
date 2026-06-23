import logging

from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.models import Project
from app import db

api = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


@api.route('/projets', methods=['GET'])
@login_required
def lister():
    """Liste les projets."""
    statut = request.args.get('statut')
    logger.info("Demande de liste des projets", extra={'statut_filtre': statut})

    q = Project.query
    if statut:
        q = q.filter_by(statut=statut)

    projets = q.order_by(Project.created_at.desc()).all()
    logger.info("Liste des projets récupérés avec succès", extra={'nb_projets': len(projets)})

    return jsonify({'projets': [p.to_dict() for p in projets],
                    'total': len(projets)}), 200


@api.route('/projets/<int:id>', methods=['GET'])
@login_required
def obtenir(id):
    """Récupère un projet par son id."""
    logger.info("Tentative de récupération du projet", extra={'id': id})

    p = Project.query.get(id)
    if not p:
        logger.warning("Projet non trouvé", extra={'id': id})
        return jsonify({'erreur': 'Projet introuvable'}), 404

    logger.info("Projet récupéré avec succès", extra={'id': id, 'titre': p.titre})
    return jsonify(p.to_dict()), 200


@api.route('/projets', methods=['POST'])
@login_required
def creer():
    """Crée un nouveau projet depuis un JSON envoyé en POST."""
    logger.info("Tentative de création d'un nouveau projet")
    data = request.get_json()

    if not data or not data.get('titre') or not data.get('description'):
        champs_fournis = list(data.keys()) if data else []
        logger.warning("Échec de création : Champs requis manquants",
                       extra={'champs_fournis': champs_fournis})
        return jsonify({'erreur': 'titre et description requis'}), 400

    p = Project(titre=data['titre'],
                description=data['description'],
                technologies=data.get('technologies', ''),
                url_github=data.get('url_github'),
                statut=data.get('statut', 'en_cours'))

    try:
        db.session.add(p)
        db.session.commit()
        logger.info('Projet créé avec succès', extra={'id': p.id, 'titre': p.titre})
        return jsonify(p.to_dict()), 201
    except Exception:
        db.session.rollback()
        logger.error("Erreur base de données lors de la création", exc_info=True)
        return jsonify({'erreur': 'Impossible de sauvegarder le projet'}), 500


@api.route('/projets/<int:id>', methods=['DELETE'])
@login_required
def supprimer(id):
    """Supprime un projet par son id."""
    logger.info("Tentative de suppression du projet", extra={'id': id})

    p = Project.query.get(id)
    if not p:
        logger.warning("Échec de la suppression : Projet non trouvé", extra={'id': id})
        return jsonify({'erreur': 'Projet introuvable'}), 404

    try:
        db.session.delete(p)
        db.session.commit()
        logger.info('Projet supprimé avec succès', extra={'id': id})
        return jsonify({'message': f'Projet {id} supprimé'}), 200
    except Exception:
        db.session.rollback()
        logger.error("Erreur base de données lors de la suppression",
                     extra={'id': id}, exc_info=True)
        return jsonify({'erreur': 'Impossible de supprimer le projet'}), 500