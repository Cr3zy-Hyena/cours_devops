import logging
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, abort
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Project, User, Paiement

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


@main.route('/')
@login_required
def index():
    projets = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('index.html', projets=projets)


@main.route('/projet/<int:id>')
@login_required
def detail_projet(id):
    projet = Project.query.get_or_404(id)

    # Vérifier si l'utilisateur a déjà payé pour ce projet
    deja_paye = False
    if projet.verrouille:
        deja_paye = Paiement.query.filter_by(
            projet_id=id,
            user_id=current_user.id,
            statut='reussi'
        ).first() is not None

    return render_template('detail.html', projet=projet, deja_paye=deja_paye)


@main.route('/a-propos')
def a_propos():
    return render_template('a_propos.html')


@main.route('/sante')
def health_check():
    return jsonify({'statut': 'ok', 'service': 'devportfolio'}), 200


# ── Authentification ───────────────────────────────────────────────────────────

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


# ── Paiement fictif (simulation interne) ──────────────────────────────────────

@main.route('/projet/<int:id>/payer')
@login_required
def payer(id):
    """Affiche le formulaire de paiement fictif."""
    projet = Project.query.get_or_404(id)

    if not projet.verrouille:
        return redirect(url_for('main.detail_projet', id=id))

    # Déjà payé ?
    deja_paye = Paiement.query.filter_by(
        projet_id=id, user_id=current_user.id, statut='reussi'
    ).first()
    if deja_paye:
        return redirect(url_for('main.detail_projet', id=id))

    return render_template('paiement_fictif.html', projet=projet)


@main.route('/projet/<int:id>/payer/confirmer', methods=['POST'])
@login_required
def payer_confirmer(id):
    """Valide le paiement fictif — n'importe quelle carte est acceptée."""
    projet = Project.query.get_or_404(id)

    # Vérification minimale : le formulaire doit être rempli
    carte = request.form.get('carte', '').replace(' ', '')
    if len(carte) < 8:
        return redirect(url_for('main.payer', id=id))

    # Enregistrer le paiement comme réussi directement
    import uuid
    paiement = Paiement(
        projet_id=id,
        user_id=current_user.id,
        stripe_session_id=f'fictif_{uuid.uuid4().hex}',  # ID unique simulé
        montant_centimes=100,
        statut='reussi',
    )
    db.session.add(paiement)
    db.session.commit()

    logger.info("Paiement fictif validé", extra={
        'projet_id': id, 'user_id': current_user.id
    })

    return render_template('paiement_succes.html', projet=projet)