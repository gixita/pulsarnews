from flask import flash, redirect, render_template, request, url_for, jsonify, current_app, session
from flask_login import current_user, login_user, logout_user


from werkzeug.urls import url_parse
import json

from app import db, oauth
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

class Microsoft:
    def __init__(self):
        self.microsoft = None
        
    def set_microsoft(self, client_id, tenant_id, client_secret):
        tenant_name = tenant_id
        self.microsoft = oauth.remote_app(
            'microsoft',
            consumer_key=client_id,
            consumer_secret=client_secret,
            request_token_params={'scope': 'User.ReadBasic.All'},
            base_url='https://graph.microsoft.com/v1.0/',
            request_token_url=None,
            access_token_method='POST',
            access_token_url=str.format('https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token', tenant=tenant_name),
            authorize_url=str.format('https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize', tenant=tenant_name),
        )

    def get_microsoft(self):
        return self.microsoft

microsoft_app = Microsoft()

@bp.route("/", methods=["GET", "POST"])
@bp.route("/login", methods=["GET", "POST"])
def login(subdomain='www'):
    flash("This is an alpha version and could be unstable", "warning")
    if current_user.is_authenticated:
        return redirect(url_for("main.index", subdomain=subdomain))
    form = LoginEmailForm()
    if form.validate_on_submit():
        mail_provider = MailProviders.query.filter_by(domain=form.email.data.split('@')[1]).first()
        if not mail_provider:
            user = User.query.filter_by(email=form.email.data).first()
            # TODO check domain if company have an account
            if user is None:
                flash("You don't have an account yet", "warning")
                return redirect(url_for("auth.register", subdomain=subdomain, email=form.email.data))
            else:
                formPassword = LoginPasswordForm(email = form.email.data)
                return redirect(url_for("auth.login_with_password", subdomain=subdomain, email=form.email.data))
        else:
            flash("Only corporate account are allowed to connect", "warning")
    return render_template("auth/login_email.html", title="Sign In", subdomain=subdomain, args=request.args.items(), form=form)

@bp.route("/login_azure_old")
def login_azure_old(subdomain='www'):
    microsoft_app.set_microsoft(client_id = current_app.config['CLIENT_ID'], tenant_id=current_app.config['TENANT'], client_secret=current_app.config['CLIENT_SECRET'])
    microsoft = microsoft_app.get_microsoft()
    session.clear()
    if 'microsoft_token' in session:
        return redirect(url_for('main.index', subdomain=subdomain))
    # Generate the guid to only accept initiated logins
    guid = uuid.uuid4()
    session['state'] = guid
    print(url_for('auth.authorized', subdomain=subdomain, _external=True))
    return microsoft.authorize(callback=url_for('auth.authorized', subdomain=subdomain, _external=True), state=guid)

@bp.route("/login_azure")
def login_azure(subdomain='www'):
    client_id = current_app.config['CLIENT_ID']
    tenant_id = tenant_id=current_app.config['TENANT']
    return render_template("auth/login_azure.html", title="Sign In", subdomain=subdomain, client_id=client_id, tenant_id=tenant_id, args=request.args.items())

@bp.route('/signin-oidc')
def authorized(subdomain='www'):
    client_id = current_app.config['CLIENT_ID']
    user = User.query.filter_by(id=1).first()
    login_user(user, remember=True)
    return render_template("auth/login_authorized_azure.html", title="Authorized", subdomain=subdomain, client_id=client_id, args=request.args.items())

@bp.route('/signin-oidc-old')
def authorized_old(subdomain='www'):
    response = microsoft_app.get_microsoft().authorized_response()
    if response is None:
        return "Access Denied: Reason=%s\nError=%s" % (
            response.get('error'), 
            request.get('error_description')
        )
    # Check response for state
    print("Response: " + str(response))
    if str(session['state']) != str(request.args['state']):
        raise Exception('State has been messed with, end authentication')
    # Okay to store this in a local variable, encrypt if it's going to client
    # machine or database. Treat as a password. 
    session['microsoft_token'] = (response['access_token'], '')
    user = User.query.filter_by(id=1).first()
    login_user(user, remember=True)
    return redirect(url_for('main.index', subdomain=subdomain)) 


@bp.route("/login_azure2")
def login_azure2(subdomain='www'):
    session.clear()
    session["flow"] = _build_auth_code_flow(scopes=current_app.config['SCOPE'], subdomain=subdomain)
    return render_template("auth/login_azure.html", subdomain=subdomain, auth_url=session["flow"]["auth_uri"], version=msal.__version__)

@bp.route("/signin2-oidc")  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized2(subdomain='www'):
    try:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}), request.args)
        if "error" in result:
            return render_template("auth/auth_error.html", subdomain=subdomain, result=result)
        session["user"] = result.get("id_token_claims")
        user = User.query.filter_by(id=1).first()
        login_user(user, remember=True)
        _save_cache(cache)
    except ValueError:  # Usually caused by CSRF
        pass  # Simply ignore them
    return redirect(url_for("main.index", subdomain=subdomain))

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        current_app.config['CLIENT_ID'], authority=authority or current_app.config['AUTHORITY'],
        client_credential=current_app.config['CLIENT_SECRET'], token_cache=cache)

def _build_auth_code_flow(authority=None, scopes=None, subdomain='www'):
    return _build_msal_app(authority=authority).initiate_auth_code_flow(
        scopes or [],
        redirect_uri=url_for("auth.authorized", subdomain=subdomain, _external=True))
        
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
        mail_provider = MailProviders.query.filter_by(domain=email.split('@')[1]).first()
        if not mail_provider:
            user = User.query.filter_by(email=email).first()
            if user is None or not user.check_password(form.password.data):
                flash("Invalid username or password", "warning")
                return redirect(url_for("auth.login", subdomain=subdomain))
            # TODO in post method already authenticated user can relogin without get the flash message of "you are already looged in"
            login_user(user, remember=True)
            next_page = request.args.get("next")
            if not next_page or url_parse(next_page).netloc != "":
                next_page = url_for("main.index", subdomain=subdomain)
            return redirect(next_page)
        else:
            flash("Only corporate account are allowed to connect", "warning")
    return render_template("auth/login_password.html", subdomain=subdomain, title="Sign In", form=form)


@bp.route("/logout")
def logout(subdomain='www'):
    logout_user()
    return redirect(url_for("auth.login", subdomain=subdomain))


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
        checkUser = User.query.filter_by(email=form.email.data).first()
        user = User(username=form.username.data, email=form.email.data)
        # TODO the verification of the domain to add the company_id should be done after the email has been verified
        query_domain = Domains.query.filter_by(name=form.email.data.split('@')[1]).first()
        mail_provider = MailProviders.query.filter_by(domain=form.email.data.split('@')[1]).first()
        if mail_provider:
            flash("Only corporate account are allowed to connect", "danger")
            return redirect(url_for("auth.login", subdomain=subdomain))
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
            send_verification_email(current_user, subdomain=subdomain)
            flash("Congratulations, you are now a registered user!", "success")
            return redirect(url_for("auth.login", subdomain=subdomain))
        else:
            flash("You have already an account on PulsarNews", "danger")
    return render_template("auth/register.html", subdomain=subdomain, title="Register", form=form)


@bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request(subdomain='www'):
    if current_user.is_authenticated:
        return redirect(url_for("main.index", subdomain=subdomain))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user, subdomain=subdomain)
        flash("An email with instructions was sent to your address.", "success")
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
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset.", "success")
        return redirect(url_for("auth.login", subdomain=subdomain))
    return render_template("auth/reset_password.html", subdomain=subdomain, title="Reset password", form=form)



