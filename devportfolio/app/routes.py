import os
import uuid
import logging

from flask import (Blueprint, render_template, jsonify, request,
                   redirect, url_for, abort, flash)
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models import Project, User, Paiement, PasswordResetToken, SecurityQuestion
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

@main.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')

@main.route('/sante')
def health_check():
    return jsonify({'statut': 'ok', 'service': 'devportfolio'}), 200


# ── Authentification ───────────────────────────────────────────────────────────

QUESTIONS_DISPONIBLES = [
    "Quel est le prénom de votre mère ?",
    "Quel est le nom de votre animal de compagnie d'enfance ?",
    "Dans quelle ville êtes-vous né(e) ?",
    "Quel est le prénom de votre meilleur(e) ami(e) d'enfance ?",
    "Quel était le modèle de votre première voiture ?",
    "Quel est le nom de votre école primaire ?",
]


@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        q1 = request.form.get('question1', '')
        r1 = request.form.get('reponse1', '').strip()
        q2 = request.form.get('question2', '')
        r2 = request.form.get('reponse2', '').strip()
        q3 = request.form.get('question3', '')
        r3 = request.form.get('reponse3', '').strip()

        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est déjà pris.", "error")
            return render_template('register.html', questions=QUESTIONS_DISPONIBLES)

        if not all([q1, r1, q2, r2, q3, r3]):
            flash("Veuillez répondre aux 3 questions de sécurité.", "error")
            return render_template('register.html', questions=QUESTIONS_DISPONIBLES)

        if len({q1, q2, q3}) < 3:
            flash("Veuillez choisir 3 questions différentes.", "error")
            return render_template('register.html', questions=QUESTIONS_DISPONIBLES)

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        sq = SecurityQuestion(
            user_id=user.id,
            question1=q1, reponse1=r1,
            question2=q2, reponse2=r2,
            question3=q3, reponse3=r3,
        )
        db.session.add(sq)
        db.session.commit()

        flash("Compte créé ! Vous pouvez vous connecter.", "success")
        return redirect(url_for('main.login'))

    return render_template('register.html', questions=QUESTIONS_DISPONIBLES)


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

@main.route('/mot-de-passe-oublie', methods=['GET', 'POST'])
def mot_de_passe_oublie():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        user = User.query.filter_by(username=username).first()
        if not user or not user.security_questions:
            flash("Aucun compte trouvé avec ce nom d'utilisateur.", "error")
            return render_template('mot_de_passe_oublie.html')
        return redirect(url_for('main.verifier_questions', username=username))
    return render_template('mot_de_passe_oublie.html')


@main.route('/verifier-questions/<username>', methods=['GET', 'POST'])
def verifier_questions(username):
    user = User.query.filter_by(username=username).first_or_404()
    sq   = user.security_questions
    if not sq:
        flash("Questions de sécurité non configurées.", "error")
        return redirect(url_for('main.mot_de_passe_oublie'))
    if request.method == 'POST':
        r1 = request.form.get('reponse1', '')
        r2 = request.form.get('reponse2', '')
        r3 = request.form.get('reponse3', '')
        if sq.verifier_reponses(r1, r2, r3):
            token_obj = PasswordResetToken.create_for_user(user)
            return redirect(url_for('main.reinitialiser_mot_de_passe', token=token_obj.token))
        flash("Une ou plusieurs réponses sont incorrectes.", "error")
    return render_template('verifier_questions.html', sq=sq)


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


@main.route('/admin/migration-questions')
def migration_questions():
    from sqlalchemy import text
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS security_questions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                question1 VARCHAR(200) NOT NULL,
                reponse1 VARCHAR(255) NOT NULL,
                question2 VARCHAR(200) NOT NULL,
                reponse2 VARCHAR(255) NOT NULL,
                question3 VARCHAR(200) NOT NULL,
                reponse3 VARCHAR(255) NOT NULL
            )
        """))
        db.session.commit()
        return "Migration questions OK ✅"
    except Exception as e:
        db.session.rollback()
        return f"Erreur : {e}"


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


