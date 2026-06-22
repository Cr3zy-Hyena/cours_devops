import os
import uuid
import stripe
import logging

from flask import (Blueprint, render_template, jsonify, request,
                   redirect, url_for, abort, flash)
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Project, User, Paiement

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# Stripe se configure depuis les variables d'environnement
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')

# Mode test gratuit : déverrouillage sans carte, 0 €
# Activé si STRIPE_TEST_FREE=true dans .env (dev / démo uniquement)
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

    # Vérifier si l'utilisateur a déjà payé pour ce projet
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


# ── Paiement Stripe ────────────────────────────────────────────────────────────

@main.route('/projet/<int:id>/payer')
@login_required
def payer(id):
    """Crée une session Stripe Checkout et redirige vers la page de paiement Stripe."""
    projet = Project.query.get_or_404(id)

    if not projet.verrouille:
        # Projet déjà public, pas besoin de payer
        return redirect(url_for('main.detail_projet', id=id))

    # Déjà payé par cet utilisateur ?
    deja_paye = Paiement.query.filter_by(
        projet_id=id, user_id=current_user.id, statut='reussi'
    ).first()
    if deja_paye:
        return redirect(url_for('main.detail_projet', id=id))

    if not stripe.api_key:
        abort(500, "Clé Stripe manquante — ajouter STRIPE_SECRET_KEY dans .env")

    try:
        # Création d'une session Stripe Checkout
        # amount_total en centimes : 100 = 1,00 €
        # En mode TEST, aucun vrai argent n'est débité
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': 100,          # 1,00 € (simulation — aucun vrai débit)
                    'product_data': {
                        'name': f'Déverrouillage — {projet.titre}',
                        'description': 'Accès complet au projet : code source, démo, GitHub',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            # URLs de retour après paiement
            success_url=url_for('main.paiement_succes',
                                id=id, _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('main.paiement_annule', id=id, _external=True),
            # Métadonnées pour retrouver projet + user dans le webhook
            metadata={
                'projet_id': str(id),
                'user_id':   str(current_user.id),
            },
            client_reference_id=str(current_user.id),
        )

        # On enregistre le paiement en attente avant la redirection
        paiement = Paiement(
            projet_id=id,
            user_id=current_user.id,
            stripe_session_id=session.id,
            montant_centimes=100,
            statut='en_attente',
        )
        db.session.add(paiement)
        db.session.commit()

        logger.info("Session Stripe créée", extra={
            'session_id': session.id, 'projet_id': id, 'user_id': current_user.id
        })

        # Redirection vers la page Stripe hébergée
        return redirect(session.url, code=303)

    except stripe.error.StripeError as e:
        logger.error("Erreur Stripe", exc_info=True)
        abort(500, f"Erreur Stripe : {e.user_message}")


@main.route('/projet/<int:id>/debloquer-test', methods=['POST'])
@login_required
def debloquer_test(id):
    """
    Déverrouillage gratuit en mode test (0 € — aucune carte requise).

    Disponible uniquement si STRIPE_TEST_FREE=true dans .env.
    Simule une transaction Stripe réussie côté serveur sans appel API réel :
    crée un Paiement avec un stripe_session_id factice et statut='reussi'.
    """
    if not TEST_FREE_MODE:
        abort(403, "Mode test gratuit désactivé.")

    projet = Project.query.get_or_404(id)

    if not projet.verrouille:
        return redirect(url_for('main.detail_projet', id=id))

    # Idempotent : si déjà débloqué, on redirige directement
    existant = Paiement.query.filter_by(
        projet_id=id, user_id=current_user.id, statut='reussi'
    ).first()
    if existant:
        return redirect(url_for('main.detail_projet', id=id))

    # ID de session factice mais unique (format similaire à Stripe)
    fake_session_id = f"test_free_{uuid.uuid4().hex}"

    paiement = Paiement(
        projet_id=id,
        user_id=current_user.id,
        stripe_session_id=fake_session_id,
        montant_centimes=0,       # 0 € — simulation pure
        statut='reussi',
    )
    db.session.add(paiement)
    db.session.commit()

    logger.info("Déverrouillage test gratuit", extra={
        'fake_session_id': fake_session_id,
        'projet_id': id,
        'user_id': current_user.id,
    })

    return redirect(url_for('main.paiement_succes_test', id=id))


@main.route('/projet/<int:id>/paiement/succes')
@login_required
def paiement_succes(id):
    """Stripe redirige ici après un paiement réussi."""
    projet = Project.query.get_or_404(id)
    session_id = request.args.get('session_id')

    if not session_id:
        abort(400, "Session ID manquant")

    try:
        # Vérification côté Stripe que le paiement est bien validé
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == 'paid':
            # Mettre à jour le paiement en base
            paiement = Paiement.query.filter_by(
                stripe_session_id=session_id
            ).first()

            if paiement and paiement.statut != 'reussi':
                paiement.statut = 'reussi'
                db.session.commit()
                logger.info("Paiement validé", extra={
                    'session_id': session_id, 'projet_id': id
                })

        return render_template('paiement_succes.html', projet=projet)

    except stripe.error.StripeError as e:
        logger.error("Erreur vérification Stripe", exc_info=True)
        abort(500, f"Impossible de vérifier le paiement : {e.user_message}")


@main.route('/projet/<int:id>/paiement/succes-test')
@login_required
def paiement_succes_test(id):
    """Page de confirmation pour le déverrouillage test gratuit (0 €)."""
    projet = Project.query.get_or_404(id)
    return render_template('paiement_succes.html', projet=projet, test_mode=True)


@main.route('/projet/<int:id>/paiement/annule')
@login_required
def paiement_annule(id):
    """Stripe redirige ici si l'utilisateur annule le paiement."""
    projet = Project.query.get_or_404(id)

    # Marquer le paiement comme échoué / annulé
    paiement = Paiement.query.filter_by(
        projet_id=id, user_id=current_user.id, statut='en_attente'
    ).order_by(Paiement.created_at.desc()).first()

    if paiement:
        paiement.statut = 'annule'
        db.session.commit()

    return render_template('paiement_annule.html', projet=projet)