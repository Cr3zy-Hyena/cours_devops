import os
import uuid
import logging

from flask import (Blueprint, render_template, jsonify, request,
                   redirect, url_for, abort, flash)
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models import Project, User, Paiement
from app import limiter

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

TEST_FREE_MODE = os.getenv('STRIPE_TEST_FREE', 'false').lower() == 'true'


# ── Pages principales ──────────────────────────────────────────────────────────

@main.route('/')
@login_required
def index():
    projets = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('index.html', projets=projets)


@main.route('/projet/<int:id>')
@login_required
def detail_projet(id):
    projet = Project.query.get_or_404(id)

    deja_paye = False
    if projet.verrouille:
        deja_paye = Paiement.query.filter_by(
            projet_id=id,
            user_id=current_user.id,
            statut='reussi'
        ).first() is not None

    return render_template('detail.html', projet=projet, deja_paye=deja_paye,
                           test_free_mode=TEST_FREE_MODE)


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
@limiter.limit("5 per minute", methods=["POST"])
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


# ── Paiement ───────────────────────────────────────────────────────────────────

@main.route('/projet/<int:id>/payer')
@login_required
def payer(id):
    """Redirige vers la page de paiement fictif intégrée."""
    projet = Project.query.get_or_404(id)

    if not projet.verrouille:
        return redirect(url_for('main.detail_projet', id=id))

    deja_paye = Paiement.query.filter_by(
        projet_id=id, user_id=current_user.id, statut='reussi'
    ).first()
    if deja_paye:
        return redirect(url_for('main.detail_projet', id=id))

    return redirect(url_for('main.checkout_fictif', id=id))


@main.route('/projet/<int:id>/checkout', methods=['GET'])
@login_required
def checkout_fictif(id):
    """Page de paiement fictif avec formulaire carte bancaire."""
    projet = Project.query.get_or_404(id)

    if not projet.verrouille:
        return redirect(url_for('main.detail_projet', id=id))

    deja_paye = Paiement.query.filter_by(
        projet_id=id, user_id=current_user.id, statut='reussi'
    ).first()
    if deja_paye:
        return redirect(url_for('main.detail_projet', id=id))

    return render_template('paiement_fictif.html', projet=projet)


@main.route('/projet/<int:id>/checkout', methods=['POST'])
@login_required
def debloquer_fictif(id):
    """
    Valide le paiement fictif.
    Accepte n'importe quelles coordonnées bancaires.
    Crée un Paiement reussi sans aucun appel Stripe.
    """
    projet = Project.query.get_or_404(id)

    existant = Paiement.query.filter_by(
        projet_id=id, user_id=current_user.id, statut='reussi'
    ).first()
    if existant:
        return jsonify({'redirect': url_for('main.detail_projet', id=id)})

    fake_session_id = f"fictif_{uuid.uuid4().hex}"

    paiement = Paiement(
        projet_id=id,
        user_id=current_user.id,
        stripe_session_id=fake_session_id,
        montant_centimes=100,
        statut='reussi',
    )
    db.session.add(paiement)
    db.session.commit()

    logger.info("Paiement fictif validé", extra={
        'projet_id': id, 'user_id': current_user.id
    })

    return jsonify({'redirect': url_for('main.paiement_succes_test', id=id)})


@main.route('/projet/<int:id>/debloquer-test', methods=['POST'])
@login_required
def debloquer_test(id):
    """Déverrouillage gratuit 0€ — bouton test (STRIPE_TEST_FREE=true)."""
    if not TEST_FREE_MODE:
        abort(403, "Mode test gratuit désactivé.")

    projet = Project.query.get_or_404(id)

    if not projet.verrouille:
        return redirect(url_for('main.detail_projet', id=id))

    existant = Paiement.query.filter_by(
        projet_id=id, user_id=current_user.id, statut='reussi'
    ).first()
    if existant:
        return redirect(url_for('main.detail_projet', id=id))

    fake_session_id = f"test_free_{uuid.uuid4().hex}"

    paiement = Paiement(
        projet_id=id,
        user_id=current_user.id,
        stripe_session_id=fake_session_id,
        montant_centimes=0,
        statut='reussi',
    )
    db.session.add(paiement)
    db.session.commit()

    return redirect(url_for('main.paiement_succes_test', id=id))


@main.route('/projet/<int:id>/paiement/succes')
@login_required
def paiement_succes(id):
    projet = Project.query.get_or_404(id)
    session_id = request.args.get('session_id')

    if not session_id:
        abort(400, "Session ID manquant")

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == 'paid':
            paiement = Paiement.query.filter_by(
                stripe_session_id=session_id
            ).first()

            if paiement and paiement.statut != 'reussi':
                paiement.statut = 'reussi'
                db.session.commit()

        return render_template('paiement_succes.html', projet=projet)

    except stripe.error.StripeError as e:
        abort(500, f"Impossible de vérifier le paiement : {e.user_message}")


@main.route('/projet/<int:id>/paiement/succes-test')
@login_required
def paiement_succes_test(id):
    projet = Project.query.get_or_404(id)
    return render_template('paiement_succes.html', projet=projet, test_mode=True)



@main.route('/projet/<int:id>/paiement/annule')
@login_required
def paiement_annule(id):
    projet = Project.query.get_or_404(id)

    paiement = Paiement.query.filter_by(
        projet_id=id, user_id=current_user.id, statut='en_attente'
    ).order_by(Paiement.created_at.desc()).first()

    if paiement:
        paiement.statut = 'annule'
        db.session.commit()

    return render_template('paiement_annule.html', projet=projet)


