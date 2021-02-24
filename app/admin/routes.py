from flask import flash, redirect, render_template, request, url_for, jsonify
from flask_login import current_user, login_required
from app.models import Administrator, Company, User, Post, Vote, Comment, Domains
from app import db

from app.admin import bp
from app.admin.forms import EditUserForm, EditCompanyForm, EditDomainForm, EditPostForm

def super_admin_required(f):
    def wrapper(*args, **kwargs):
        if current_user.verified == 0 or current_user.verified is None:
            return redirect(url_for('auth.verify_account', subdomain=subdomain))
        if (current_user.company_id == 0 or current_user.company_id == None):
            return redirect(url_for("auth.create_company", subdomain=subdomain))
        super_admin = Administrator.query.filter_by(user_id=current_user.id).first()
        if super_admin:
            if super_admin.is_admin:
                return f(*args, **kwargs)
        else:
            flash("You cannot access this section, please move on", "danger")
            return redirect(url_for("main.index", subdomain=subdomain))
    wrapper.__doc__ = f.__doc__
    wrapper.__name__ = f.__name__
    return wrapper


@bp.route("/", methods=["GET"])
@bp.route("/index", methods=["GET"])
@login_required
@super_admin_required
def index(subdomain='www'):
    dashboard = {}
    dashboard['COMPANIES_ACTIVE'] = Company.query.filter_by(banned=0).count()
    dashboard['COMPANIES_NOTACTIVE'] = Company.query.filter_by(banned=1).count()
    dashboard['COMPANIES_DOMAINS'] = Domains.query.count()
    dashboard['USERS_VERIFIED'] = User.query.filter_by(verified=1).count()
    dashboard['USERS_UNVERIFIED'] = User.query.filter_by(verified=0).count()
    dashboard['USERS_BANNED'] = User.query.filter_by(banned=1).count()
    dashboard['POSTS'] = Post.query.count()
    dashboard['POSTS_VOTES'] = Vote.query.count()
    dashboard['POSTS_COMMENTS'] = Comment.query.count()
    
    
    return render_template("admin/dashboard.html", subdomain=subdomain, title="Dashboard", dashboard=dashboard)

@bp.route("/users", methods=["GET"])
@login_required
@super_admin_required
def users(subdomain='www'):
    company_id = request.args.get("company_id")
    if company_id:
        users = User.query.filter_by(company_id=company_id).all()
    else:
        users = User.query.all()
    return render_template("admin/users.html", subdomain=subdomain, title="Dashboard - Users", users=users)

@bp.route("/edit_user/<user_id>", methods=["GET", "POST"])
@login_required
@super_admin_required
def edit_user(user_id, subdomain='www'):
    user = User.query.filter_by(id=user_id).first_or_404()
    form = EditUserForm(user)
    # form.email(disabled=True)
    if form.validate_on_submit():
        user.username = form.username.data
        user.about_me = form.about_me.data
        user.email = form.email.data
        user.company_id = form.company_id.data
        user.verified = form.verified.data
        user.admin = form.admin.data
        user.banned = form.banned.data
        db.session.commit()
        flash("Your changes have been saved.", "success")
        return redirect(url_for("admin.users", subdomain=subdomain))
    elif request.method == "GET":
        form.username.data = user.username
        form.about_me.data = user.about_me
        form.email.data = user.email
        form.company_id.data = user.company_id
        form.verified.data = user.verified
        form.admin.data = user.admin
        form.banned.data = user.banned
    return render_template(
        "admin/edit_user.html", subdomain=subdomain, title="Edit profile", form=form
    )

@bp.route("/companies", methods=["GET"])
@login_required
@super_admin_required
def companies(subdomain='www'):
    companies = Company.query.all()
    return render_template("admin/companies.html", subdomain=subdomain, title="Dashboard - Companies", companies=companies)

@bp.route("/edit_company/<company_id>", methods=["GET", "POST"])
@login_required
@super_admin_required
def edit_company(company_id, subdomain='www'):
    company = Company.query.filter_by(id=company_id).first_or_404()
    form = EditCompanyForm(company)
    # form.email(disabled=True)
    if form.validate_on_submit():
        company.name = form.name.data
        company.banned = form.banned.data
        db.session.commit()
        flash("Your changes have been saved.", "success")
        return redirect(url_for("admin.companies", subdomain=subdomain))
    elif request.method == "GET":
        form.name.data = company.name
        form.banned.data = company.banned
    return render_template(
        "admin/edit_company.html", subdomain=subdomain, title="Edit company", form=form
    )

@bp.route("/domains", methods=["GET"])
@login_required
@super_admin_required
def domains(subdomain='www'):
    company_id = request.args.get("company_id")
    if company_id:
        domains = Domains.query.filter_by(company_id=company_id).all()
    else:
        domains = Domains.query.all()
    return render_template("admin/domains.html", subdomain=subdomain, title="Dashboard - Domains", domains=domains)

@bp.route("/edit_domain/<domain_id>", methods=["GET", "POST"])
@login_required
@super_admin_required
def edit_domain(domain_id, subdomain='www'):
    domain = Domains.query.filter_by(id=domain_id).first_or_404()
    form = EditDomainForm(domain)
    # form.email(disabled=True)
    if form.validate_on_submit():
        domain.name = form.name.data
        domain.fully_managed_domain = form.fully_managed_domain.data
        domain.company_id = form.company_id.data
        db.session.commit()
        flash("Your changes have been saved.", "success")
        return redirect(url_for("admin.domains", subdomain=subdomain))
    elif request.method == "GET":
        form.name.data = domain.name
        form.fully_managed_domain.data = domain.fully_managed_domain
        form.company_id.data = domain.company_id
    return render_template(
        "admin/edit_domain.html", subdomain=subdomain, title="Edit domain", form=form
    )

@bp.route("/posts", methods=["GET"])
@login_required
@super_admin_required
def posts(subdomain='www'):
    company_id = request.args.get("company_id")
    if company_id:
        posts = Post.query.filter_by(company_id=company_id).all()
    else:
        posts = Post.query.all()
    return render_template("admin/posts.html", subdomain=subdomain, title="Dashboard - Posts", posts=posts)

@bp.route("/edit_post/<post_id>", methods=["GET", "POST"])
@login_required
@super_admin_required
def edit_post(post_id, subdomain='www'):
    post = Post.query.filter_by(id=post_id).first_or_404()
    form = EditPostForm(post)
    # form.email(disabled=True)
    if form.validate_on_submit():
        post.title = form.title.data
        post.url = form.url.data
        post.url_base = form.url_base.data
        post.text = form.text.data
        post.user_id = form.user_id.data
        post.deleted = form.deleted.data
        post.company_id = form.company_id.data
        db.session.commit()
        flash("Your changes have been saved.", "success")
        return redirect(url_for("admin.posts", subdomain=subdomain))
    elif request.method == "GET":
        form.title.data = post.title
        form.url.data = post.url
        form.url_base.data = post.url_base
        form.text.data = post.text
        form.user_id.data = post.user_id
        form.deleted.data = post.deleted
        form.company_id.data = post.company_id
        
    return render_template(
        "admin/edit_post.html", subdomain=subdomain, title="Edit post", form=form
    )