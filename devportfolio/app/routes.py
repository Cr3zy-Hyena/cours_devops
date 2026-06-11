from flask import Blueprint, render_template, jsonify
from app.models import Project
from app import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    projets = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('index.html', projets=projets)

@main.route('/projet/<int:id>')
def detail_projet(id):
    projet = Project.query.get_or_404(id)
    return render_template('detail.html', projet=projet)

@main.route('/a-propos')
def a_propos():
    return render_template('a_propos.html')

@main.route('/sante')
def health_check():
    return jsonify({'statut': 'ok', 'service': 'devportfolio'}), 200