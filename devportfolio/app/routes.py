import os
import uuid
import logging

from flask import (Blueprint, render_template, jsonify, request,
                   redirect, url_for, abort, flash)
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models import Project, User, Paiement, EmailVerificationToken, PasswordResetToken
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
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est déjà pris.", "error")
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash("Cette adresse email est déjà utilisée.", "error")
            return render_template('register.html')

        user = User(username=username, email=email, email_verifie=False)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        token_obj   = EmailVerificationToken.create_for_user(user)
        confirm_url = url_for('main.confirmer_email', token=token_obj.token, _external=True)

        logger.info("Inscription : lien de confirmation généré",
                    extra={'user_id': user.id})

        if os.getenv('FLASK_ENV') in ('development', 'testing', None):
            flash(f"[DEV] Lien de confirmation : {confirm_url}", "dev")

        flash("Compte créé ! Confirmez votre adresse email pour vous connecter.", "info")
        return redirect(url_for('main.inscription_en_attente'))

    return render_template('register.html')


@main.route('/inscription-en-attente')
def inscription_en_attente():
    return render_template('inscription_en_attente.html')


@main.route('/confirmer-email/<token>')
def confirmer_email(token):
    token_obj = EmailVerificationToken.query.filter_by(token=token).first()

    if not token_obj or not token_obj.is_valid:
        flash("Ce lien de confirmation est invalide ou a expiré.", "error")
        return redirect(url_for('main.login'))

    token_obj.user.email_verifie = True
    token_obj.used = True
    db.session.commit()

    flash("Adresse email confirmée ! Vous pouvez maintenant vous connecter.", "success")
    return redirect(url_for('main.login'))


@main.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.email_verifie:
                flash("Veuillez confirmer votre adresse email avant de vous connecter.", "error")
                return render_template('login.html')
            login_user(user)
            return redirect(url_for('main.index'))

        flash("Identifiants invalides.", "error")
    return render_template('login.html')


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/mot-de-passe-oublie', methods=['GET', 'POST'])
@limiter.limit('5 per minute')
def mot_de_passe_oublie():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        user = User.query.filter_by(username=username).first()
        flash("Si ce compte existe, un lien de réinitialisation a été généré.", "info")
        if user:
            token_obj = PasswordResetToken.create_for_user(user)
            reset_url = url_for('main.reinitialiser_mot_de_passe',
                                token=token_obj.token, _external=True)
            if os.getenv('FLASK_ENV') in ('development', 'testing', None):
                flash(f"[DEV] Lien : {reset_url}", "dev")
        return redirect(url_for('main.mot_de_passe_oublie'))
    return render_template('mot_de_passe_oublie.html')


@main.route('/reinitialiser/<token>', methods=['GET', 'POST'])
def reinitialiser_mot_de_passe(token):
    token_obj = PasswordResetToken.query.filter_by(token=token).first()
    if not token_obj or not token_obj.is_valid:
        flash("Ce lien est invalide ou a expiré.", "error")
        return redirect(url_for('main.mot_de_passe_oublie'))
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        if len(password) < 8:
            flash("Le mot de passe doit contenir au moins 8 caractères.", "error")
            return render_template('reinitialiser_mot_de_passe.html', token=token)
        if password != confirm:
            flash("Les mots de passe ne correspondent pas.", "error")
            return render_template('reinitialiser_mot_de_passe.html', token=token)
        token_obj.user.set_password(password)
        token_obj.used = True
        db.session.commit()
        flash("Mot de passe modifié avec succès.", "success")
        return redirect(url_for('main.login'))
    return render_template('reinitialiser_mot_de_passe.html', token=token)

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


@main.route('/admin/migration-email')
def migration_email():
    from sqlalchemy import text
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(120)"))
        db.session.execute(text("ALTER TABLE users ADD COLUMN email_verifie BOOLEAN DEFAULT 0"))
        db.session.commit()
        return "Migration OK ✅"
    except Exception as e:
        db.session.rollback()
        return f"Erreur (déjà fait ?) : {e}"

#sqlite3 instance/devportfolio.db
#-- Voir les utilisateurs
#SELECT id, username FROM users;

#-- Supprimer
#DELETE FROM users WHERE username = 'nom_ici'

#sortir
# .quit
