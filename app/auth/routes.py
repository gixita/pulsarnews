from flask import flash, redirect, render_template, request, url_for, jsonify, current_app, session
from flask_login import current_user, login_user, logout_user

import datetime
from werkzeug.urls import url_parse
import json

from app import db, subdomain_config
import uuid
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
import msal
from cryptography.fernet import Fernet
import base64

# TODO block user in case of multiple invalid logins
@bp.route("/", methods=["GET", "POST"])
@bp.route("/login", methods=["GET", "POST"])
def login(subdomain='www'):
    #flash("This is an alpha version and could be unstable", "warning")
    # Check if the user should be directed to a SSO credentials based on subdomain or args (from Microsoft Teams)
    tenant = ''
    sso_credentials = False
    company = None
    if 'tenant' in request.args:
        tenant = request.args['tenant']
    if current_user.is_authenticated:
        return redirect(url_for("main.index", subdomain=subdomain))
    if subdomain != 'www':
        company = Company.query.filter_by(premium=True, subdomain=subdomain).first()
    elif tenant != '':
        company = Company.query.filter_by(premium=True, tenant=tenant).first()
    if company:
        sso_credentials = True
        session['tenant'] = company.tenant
    else:
        sso_credentials = False

    form = LoginEmailForm()
    if form.validate_on_submit():

        # If user is connected normally (www outside Teams), if its domain is fully managed for SSO, redirect to SSO
        tenant = _is_user_or_company_premium_and_fully_managed(form.email.data, form, subdomain, request.args)
        if tenant != '':
            return redirect(url_for("auth.login", subdomain=subdomain, tenant=tenant))
        
        # Check that the user is using an authorized email provider
        mail_in_blacklist = MailProviders.query.filter_by(domain=form.email.data.split('@')[1]).first()
        if not mail_in_blacklist:
            user = User.query.filter_by(email=form.email.data).first()
            # If user don't have an account yet, go the registration page
            if user is None:
                flash("You don't have an account yet", "warning")
                return redirect(url_for("auth.register", subdomain=subdomain, email=form.email.data))
            else:
                company = Company.query.filter_by(id=user.company_id, premium=True).first()
                # If user company have SSO, push SSO
                if company:
                    tenant = company.tenant
                    sso_credentials = True
                    return render_template(
                        "auth/login_email.html", 
                        title="Sign In", 
                        subdomain=subdomain,
                        sso_credentials = sso_credentials,
                        tenant = tenant, 
                        args=request.args.items(), 
                        form=form
                        )
                else:
                    # If user exist, have a corporate email and the company doesn't have SSO go to normal password registration
                    formPassword = LoginPasswordForm(email = form.email.data)
                    return redirect(url_for("auth.login_with_password", subdomain=subdomain, email=form.email.data))
        else:
            flash("Only corporate account are allowed to connect", "warning")
    return render_template(
        "auth/login_email.html", 
        title="Sign In", 
        subdomain=subdomain,
        sso_credentials = sso_credentials,
        tenant = tenant, 
        args=request.args.items(), 
        form=form
        )

# If website not displayed in iFrame and have SSO, he is redirected here
@bp.route("/login_azure_desktop")
def login_azure_desktop(subdomain='www'):
    if 'tenant' in session:
        company = Company.query.filter_by(premium=True, tenant=session['tenant']).first()
        if company:
            session["flow"] = _build_auth_code_flow(company=company, subdomain=subdomain)
            return redirect(session["flow"]["auth_uri"])
        else:
            flash("Something went wrong with the authentication process", "danger")
    elif 'tenant' in request.args:
        company = Company.query.filter_by(premium=True, tenant=request.args['tenant']).first()
        if company:
            session["flow"] = _build_auth_code_flow(company=company, subdomain=subdomain)
            return redirect(session["flow"]["auth_uri"])
        else:
            flash("Something went wrong with the authentication process", "danger")
    return redirect(url_for("main.index", subdomain=subdomain))
    
# TODO fix it
@bp.route("/login_azure")
def login_azure(subdomain='www'):
    if 'tenant' in request.args or 'tenant' in session:
        tenant = ''
        if 'tenant' in request.args:
            tenant = request.args['tenant']
        elif 'tenant' in session:
            tenant = session['tenant']
        company = Company.query.filter_by(premium=True, tenant=tenant).first()
        if company:
            tenant_id = company.tenant
            client_id = company.client_id
            scopes = company.scope.split(',')

            return render_template("auth/login_azure.html", title="Sign In", subdomain=subdomain, client_id=client_id, tenant_id=tenant_id, scopes=scopes, args=request.args.items())
        else:
            flash("Your company seems not to have a premium account to integrate with Teams", "warning")
    else:
        return redirect("errors.internal_error", subdomain=subdomain)
    return redirect(url_for("main.index", subdomain=subdomain))
    
@bp.route('/signin-oidc')
def authorized(subdomain='www'):
    try:
        cache = _load_cache()
        tenant = ''
        if 'tenant' in request.args:
            tenant = request.args['tenant']
        elif 'tenant' in session:
            tenant = session['tenant']  
        company = Company.query.filter_by(premium=True, tenant=tenant).first()
        if company:
            if company.banned:
                flash("Sorry, your company is not allowed to use our service.", "danger")
                return redirect(url_for("main.index", "danger"))
            result = _build_msal_app(company=company, cache=cache).acquire_token_by_auth_code_flow(
                session.get("flow", {}), request.args)
            if "error" in result:
                # TODO create template for error of azure login
                flash("You seems not authorized by your administrator to get access, contact your admin", "danger")
                return redirect(url_for("main.index", subdomain=subdomain))
            session["user"] = result.get("id_token_claims")
            
            # Do a few verification on the token (as mentionned on Microsoft OAuth docs)
            validation_token = True
            if 'aud' in session["user"] and 'tid' in session["user"] and 'email' in session["user"]:
                if (session["user"]["aud"] != company.client_id) or (session["user"]["tid"] != company.tenant):
                    validation_token = False
            else:
                validation_token = False

            if validation_token:    
                user = User.query.filter_by(email=session["user"]["email"]).first()
                if user:
                    login_user(user, remember=True)
                else:
                    if 'name' in session["user"]:
                        name = session["user"]["name"]
                    else:
                        name = "John Doe"
                    user = User(username=name, email=session["user"]["email"], company_id=company.id, verified=1)
                    db.session.add(user)
                    db.session.commit()
                    login_user(user, remember=True)
                _save_cache(cache)
            return redirect(url_for("main.index", subdomain=subdomain))
        else:
            flash("Something went wrong with the authentication process", "danger")
            return redirect(url_for("main.index", subdomain=subdomain))
    except ValueError:  # Usually caused by CSRF
        pass  # Simply ignore them
    return render_template("auth/login_authorized_azure.html", title="Authorized", subdomain=subdomain, client_id=client_id, args=request.args.items())

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, company=None):
    if company:
        authority = company.authority+company.tenant
        cipher = Fernet(current_app.config['ENCRYPTION_KEY'].encode('utf-8'))
    return msal.ConfidentialClientApplication(
        company.client_id, authority=authority,
        client_credential=cipher.decrypt(company.client_secret).decode('utf-8'), token_cache=cache)

def _build_auth_code_flow(company=None, subdomain='www'):
    scopes = company.scope.split(',')
    authority = company.authority+company.tenant
    if subdomain_config.is_subdomain_enable:
        redirect_uri=url_for("auth.authorized", subdomain=subdomain, _external=True)
    else:
        redirect_uri=url_for("auth.authorized", _external=True)
    return _build_msal_app(company=company).initiate_auth_code_flow(
        scopes or [],
        redirect_uri=redirect_uri)
        
def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result

@bp.route("/login_password", methods=["GET", "POST"])
def login_with_password(subdomain='www'):
    if current_user.is_authenticated:
        flash("You are already logged in", "warning")
        return redirect(url_for("main.index", subdomain=subdomain))
    email = request.args.get("email")
    if not email:
        flash("Invalid authentication, please enter an email", "error")
        return redirect(url_for("auth.login", subdomain=subdomain))
    form = LoginPasswordForm()
    if form.validate_on_submit():
        mail_in_blacklist = MailProviders.query.filter_by(domain=email.split('@')[1]).first()
        if not mail_in_blacklist:
            user = User.query.filter_by(email=email).first()
            if user is None:
                flash("Invalid username or password", "warning")
                return redirect(url_for("auth.login", subdomain=subdomain))
            else:
                if user.nb_conn_attempt > 2 and user.conn_blocked_timestamp > datetime.datetime.utcnow():
                    flash("Your account was locked due to invalid credentials, please wait a minute", "danger")
                    return redirect(url_for("auth.login", subdomain=subdomain))
                else:
                    if user.check_password(form.password.data):
                        # TODO in post method already authenticated user can relogin without get the flash message of "you are already looged in"
                        user.nb_conn_attempt = 0
                        db.session.commit()
                        login_user(user, remember=True)
                        next_page = request.args.get("next")
                        if not next_page or url_parse(next_page).netloc != "":
                            next_page = url_for("main.index", subdomain=subdomain)
                        return redirect(next_page)
                    else:
                        user.nb_conn_attempt += 1
                        flash("Invalid username or password", "warning")
                        if user.nb_conn_attempt > 2:
                            user.conn_blocked_timestamp = datetime.datetime.utcnow()+datetime.timedelta(0,60)
                            flash("Your account is now lock due to multiple invalid credentials, please wait a minute", "danger")
                        db.session.commit()
                        return redirect(url_for("auth.login", subdomain=subdomain))  
        else:
            flash("Only corporate account are allowed to connect", "warning")
    return render_template("auth/login_password.html", subdomain=subdomain, title="Sign In", form=form)


@bp.route("/logout")
def logout(subdomain='www'):
    logout_user()
    return redirect(url_for("auth.login", subdomain=subdomain))

# return tenant
def _is_user_or_company_premium_and_fully_managed(email, form, subdomain, args=None):
    redirect_to_sso = False
    
    # Check that user is in company under SSO
    user = User.query.filter_by(email=email).first()
    if user:
        company = Company.query.filter_by(id=user.company_id, premium=True).first()
        if company:
            redirect_to_sso = True
    else:
    # if user don't exist, check if the company have SSO and fully manage its current domain
        domain = Domains.query.filter_by(name=email.split('@')[1], fully_managed_domain=1).first()
        if domain:
            company = Company.query.filter_by(id=domain.company_id, premium=True).first()
            if company:
                redirect_to_sso = True
    
    if redirect_to_sso:
        return company.tenant
    else: 
        return ''


@bp.route("/register", methods=["GET", "POST"])
def register(subdomain='www'):
    if current_user.is_authenticated:
        if request.args.get("token") is not None:
            company_id_by_token = verify_invitation_token(request.args.get("token"))
            current_user.company_id = company_id_by_token
            db.session.add(current_user)
            db.session.commit()
            flash('Your account as been added to a new company', 'success')
        return redirect(url_for("main.index", subdomain=subdomain))
    if request.args.get("email"):
        form = RegistrationForm(username=request.args.get("email").split('@')[0], email=request.args.get("email"), current_user=current_user)
    else:
        form = RegistrationForm(current_user=current_user)
    if form.validate_on_submit():
        # Check that the user should not be redirected to login with SSO
        tenant = _is_user_or_company_premium_and_fully_managed(form.email.data, form, subdomain, request.args)
        if tenant != '':
            return redirect(url_for("auth.login", subdomain=subdomain, tenant=tenant))

        checkUser = User.query.filter_by(email=form.email.data).first()
        user = User(username=form.username.data, email=form.email.data)
        # TODO the verification of the domain to add the company_id should be done after the email has been verified
        query_domain = Domains.query.filter_by(name=form.email.data.split('@')[1]).first()
        mail_in_blacklist = MailProviders.query.filter_by(domain=form.email.data.split('@')[1]).first()
        if mail_in_blacklist:
            flash("Only corporate account are allowed to connect", "danger")
            return redirect(url_for("auth.login", subdomain=subdomain))
        
        # Verify why this is here, this should be inside verify_account
        if request.args.get("token") is not None:
            company_id_by_token = verify_invitation_token(request.args.get("token"))
            user.company_id = company_id_by_token
        if query_domain is not None:
            if query_domain.fully_managed_domain==1:
                user.company_id = query_domain.company_id   
        # Until here

        if checkUser is None:
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            send_verification_email(current_user, subdomain=subdomain)
            flash("Congratulations, you are now a registered user!", "success")
            return redirect(url_for("auth.login", subdomain=subdomain))
        else:
            flash("You have already an account on PulsarNews", "danger")
    return render_template("auth/register.html", subdomain=subdomain, title="Register", form=form)


@bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request(subdomain='www'):
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            company = Company.query.filter_by(id=user.company_id, premium=False).first()
            if company:
                send_password_reset_email(user, subdomain=subdomain)
                flash("An email with instructions was sent to your address.", "success")
            else:
                flash("Your company manage your password, we can't modify it", "warning")
        return redirect(url_for("auth.login", subdomain=subdomain))
    return render_template(
        "auth/reset_password_request.html", subdomain=subdomain, title="Reset Password", form=form
    )

@bp.route("/send_verification_email_token", methods=["GET", "POST"])
def verification_email_request(subdomain='www'):
    if current_user.is_authenticated:
        if not (current_user.verified == 0 or current_user.verified is None):
            flash('Your account is already verified', 'success')
            return redirect(url_for("main.index", subdomain=subdomain))
        else:
            send_verification_email(current_user)
            flash("An email with instructions was sent to your address.", "success")
            return redirect(url_for("auth.verify_account", subdomain=subdomain))
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
        return redirect(url_for("auth.login", subdomain=subdomain))
    return render_template(
        "auth/send_email_verification.html", subdomain=subdomain, title="Request email verification token", form=form
    )

@bp.route("/verify_account", methods=["GET", "POST"])
def verify_account(subdomain='www'):
    if current_user.is_authenticated:
        if (current_user.verified == 1):
            return redirect(url_for("main.index", subdomain=subdomain))
    if (request.args.get('token')):
        user = User.verify_mail_token(request.args.get('token'))
        if user:
            if (user.verified == 1):
                flash("Your account is already verified", "success")
                return redirect(url_for("main.index", subdomain=subdomain))
            else:
                user.verified = 1
                db.session.add(user)
                db.session.commit()
                flash("Your account is verified, welcome !", "success")
                return redirect(url_for("main.index", subdomain=subdomain))
        else:
            flash('Your verification token is expired or invalid, please click on resend a new link.', 'danger')
    return render_template("auth/verify_account.html", subdomain=subdomain, title="Account verification")

@bp.route("/create_company", methods=["GET", "POST"])
def create_company(subdomain='www'):
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", subdomain=subdomain))
    domain = current_user.email.split('@')[1]
    name = domain.split(".")[0]
    query_domain = Domains.query.filter_by(name=domain).first()
    if query_domain is not None:
        if query_domain.fully_managed_domain == 1:
            current_user.company_id = query_domain.company_id
            db.session.add(current_user)
            db.session.commit()
            return redirect(url_for("main.index", subdomain=subdomain))
        else:
            return redirect(url_for("main.invitation_required", subdomain=subdomain))
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
        return redirect(url_for("main.index", subdomain=subdomain))
    return render_template("auth/create_company.html", subdomain=subdomain, title="Create company", form=form, domain=domain)



@bp.route("/reset_password/", methods=["GET", "POST"])
def reset_password(subdomain='www'):
    token = request.args.get("token")
    if token:
        user = User.verify_reset_password_token(token)
        if not user:
            flash("Your token is not valid or expired, request a new one from the login page", "danger")
            return redirect(url_for("main.index", subdomain=subdomain))
    if current_user.is_authenticated:
        user = current_user
    form = ResetPasswordForm()
    if form.validate_on_submit() and user:
        company = Company.query.filter_by(id=user.company_id, premium=False).first()
        if company:
            user.set_password(form.password.data)
            db.session.commit()
            flash("Your password has been reset.", "success")
        else:
            flash("Your company manage your password, we can't modify it", "danger")
        return redirect(url_for("auth.login", subdomain=subdomain))
        
    return render_template("auth/reset_password.html", subdomain=subdomain, title="Reset password", form=form)



