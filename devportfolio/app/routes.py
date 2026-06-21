from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_user, logout_user, login_required
from app import db
from app.models import Project, User

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    projets = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('index.html', projets=projets)

@main.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        existing = User.query.filter_by(username=username).first()

        if existing:
            return "Utilisateur déjà existant"

        user = User(username=username)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('main.login'))

    return render_template('register.html')


@main.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):

            login_user(user)

            return redirect(url_for('main.index'))

        return "Identifiants invalides"

    return render_template('login.html')


@main.route('/logout')
@login_required
def logout():

    logout_user()

    return redirect(url_for('main.login'))

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