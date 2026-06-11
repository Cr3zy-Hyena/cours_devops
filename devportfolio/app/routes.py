from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.models import Project #import du modèle de données
from app import db  #import de la base de données
main= Blueprint('main', __name__)  #création d'un blueprint pour les routes principales 
@main.route('/') #route pour la page d'accueil
def index():
    projets: Project.query.order_by(Project.created_at.desc()).all()    #récupération de tous les projets de la base de données, triés par date de création décroissante
    return render_template('index.html', projets=projets)      #rendu du template index
@main.route('/projet/<int:id>')       #route pour afficher les détails d'un projet
def detail_projet(id):
    projet = Project.query.get_or_404(id)   #récupération du projet par son ID, ou 404 si non trouvé
    return render_template('detail.html',projet=projet)     #rendu du template de détail
@main.route('/a-propos')    
def a_propos():
    return render_template('a_propos.html') #rendu du template à propos
@main.route('/sante')
def health_check():
    return jsonify({'statut': 'ok', 'service': 'devportfolio'}), 200    #route pour vérifier la santé de l'application, retourne un JSON avec le statut OK