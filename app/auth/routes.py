from flask import flash, redirect, render_template, request, url_for, jsonify
from flask_login import current_user, login_user, logout_user


from werkzeug.urls import url_parse
import json

from app import db
from app.auth import bp
from app.auth.forms import (
    LoginEmailForm,
    LoginPasswordForm,
    RegistrationForm,
    ResetPasswordRequestForm,
    ResetPasswordForm,
    CreateCompanyForm,
)
import jwt
from app.models import User, Company, Domains, MailProviders
from app.auth.email import send_password_reset_email, send_verification_email
from app.main.invitation import verify_invitation_token


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginEmailForm()
    if form.validate_on_submit():
        mail_provider = MailProviders.query.filter_by(domain=form.email.data.split('@')[1]).first()
        if not mail_provider:
            user = User.query.filter_by(email=form.email.data).first()
            # TODO check domain if company have an account
            if user is None:
                flash("You don't have an account yet", "warning")
                return redirect(url_for("auth.register", email=form.email.data))
            else:
                formPassword = LoginPasswordForm(email = form.email.data)
                return redirect(url_for("auth.login_with_password", email=form.email.data))
                #return render_template("auth/login_password.html", title="Sign In", form=formPassword)
        else:
            flash("Only corporate account are allowed to connect", "warning")
    return render_template("auth/login_email.html", title="Sign In", form=form)

@bp.route("/login_password", methods=["GET", "POST"])
def login_with_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    email = request.args.get("email")
    if not email:
        flash("Invalid authentication, please enter an email", "error")
        return redirect(url_for("auth.login"))
    form = LoginPasswordForm()
    if form.validate_on_submit():
        mail_provider = MailProviders.query.filter_by(domain=email.split('@')[1]).first()
        if not mail_provider:
            user = User.query.filter_by(email=email).first()
            if user is None or not user.check_password(form.password.data):
                flash("Invalid username or password", "warning")
                return redirect(url_for("auth.login"))
            login_user(user, remember=True)
            next_page = request.args.get("next")
            if not next_page or url_parse(next_page).netloc != "":
                next_page = url_for("main.index")
            return redirect(next_page)
        else:
            flash("Only corporate account are allowed to connect", "warning")
    return render_template("auth/login_password.html", title="Sign In", form=form)


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        if request.args.get("token") is not None:
            company_id_by_token = verify_invitation_token(request.args.get("token"))
            current_user.company_id = company_id_by_token
            db.session.add(current_user)
            db.session.commit()
            flash('Your account as been added to a new company', 'success')
        return redirect(url_for("main.index"))
    if request.args.get("email"):
        form = RegistrationForm(username=request.args.get("email").split('@')[0], email=request.args.get("email"), current_user=current_user)
    else:
        form = RegistrationForm(current_user=current_user)
    if form.validate_on_submit():
        checkUser = User.query.filter_by(email=form.email.data).first()
        user = User(username=form.username.data, email=form.email.data)
        # Todo the verification of the domain to add the company_id should be done after the email has been verified
        query_domain = Domains.query.filter_by(name=form.email.data.split('@')[1]).first()
        mail_provider = MailProviders.query.filter_by(domain=form.email.data.split('@')[1]).first()
        if mail_provider:
            flash("Only corporate account are allowed to connect", "danger")
            return redirect(url_for("auth.login"))
        if request.args.get("token") is not None:
            company_id_by_token = verify_invitation_token(request.args.get("token"))
            user.company_id = company_id_by_token
        if query_domain is not None:
            if query_domain.fully_managed_domain==1:
                user.company_id = query_domain.company_id   
        if checkUser is None:
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            send_verification_email(current_user)
            flash("Congratulations, you are now a registered user!", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("You have already an account on PulsarNews", "danger")
    return render_template("auth/register.html", title="Register", form=form)


@bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash("An email with instructions was sent to your address.")
        return redirect(url_for("auth.login"))
    return render_template(
        "auth/reset_password_request.html", title="Reset Password", form=form
    )

@bp.route("/send_verification_email_token", methods=["GET", "POST"])
def verification_email_request():
    if current_user.is_authenticated:
        if not (current_user.verified == 0 or current_user.verified is None):
            flash('Your account is already verified', 'success')
            return redirect(url_for("main.index"))
        else:
            send_verification_email(current_user)
            flash("An email with instructions was sent to your address.", "success")
            return redirect(url_for("auth.verify_account"))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if user.verified == 0 or user.verified is None:
                send_verification_email(user)
                flash("An email with instructions was sent to your address.", "success")
            else:
                flash("Your account is already verified", "success")
        else:
            flash("The email address is incorrect, use a valid email account or create an account.", "danger")        
        return redirect(url_for("auth.login"))
    return render_template(
        "auth/send_email_verification.html", title="Request email verification token", form=form
    )

@bp.route("/verify_account", methods=["GET", "POST"])
def verify_account():
    if current_user.is_authenticated:
        if (current_user.verified == 1):
            return redirect(url_for("main.index"))
    if (request.args.get('token')):
        user = User.verify_mail_token(request.args.get('token'))
        if user:
            if (user.verified == 1):
                flash("Your account is already verified", "success")
                return redirect(url_for("main.index"))
            else:
                user.verified = 1
                db.session.add(user)
                db.session.commit()
                flash("Your account is verified, welcome !", "success")
                return redirect(url_for("main.index"))
        else:
            flash('Your verification token is expired or invalid, please click on resend a new link.', 'danger')
    return render_template("auth/verify_account.html", title="Account verification")

@bp.route("/create_company", methods=["GET", "POST"])
def create_company():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    domain = current_user.email.split('@')[1]
    name = domain.split(".")[0]
    query_domain = Domains.query.filter_by(name=domain).first()
    if query_domain is not None:
        if query_domain.fully_managed_domain == 1:
            current_user.company_id = query_domain.company_id
            db.session.add(current_user)
            db.session.commit()
            return redirect(url_for("main.index"))
        else:
            return redirect(url_for("main.invitation_required"))
    form = CreateCompanyForm(name=name, fully_managed_domain=True)
    if form.validate_on_submit():
        company = Company(name=form.name.data)
        db.session.add(company)
        db.session.commit()
        db.session.refresh(company)
        domain = Domains(name=domain, fully_managed_domain=form.fully_managed_domain.data, company_id=company.id)
        db.session.add(domain)
        current_user.company_id = company.id
        current_user.admin = True
        db.session.commit()
        flash("Congratulations, your company has been registered! You can add other email domains in your profile", "success")
        return redirect(url_for("main.index"))
    return render_template("auth/create_company.html", title="Create company", form=form, domain=domain)



@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for("main.index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset.")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", form=form)

