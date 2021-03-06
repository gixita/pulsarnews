from datetime import datetime

from flask import (
    flash,
    redirect,
    render_template,
    request,
    url_for,
    current_app,
    jsonify,
)
from flask_jwt import JWT
import json
from flask_login import current_user, login_required

from app import db
from app.main.forms import CommentForm, EditProfileForm, PostForm, AddDomainForm
from app.auth.forms import LoginEmailForm
from app.models import Comment, Post, User, Vote, Comment_Vote, Domains, MailProviders, Company
from app.main import bp
from app.main.invitation import send_invitation

from app.main.controller import Controller

@login_required
def redirect_url(default="main.index"):
    return request.args.get("next") or request.referrer or url_for(default, subdomain=subdomain)

def company_required(f):
    def wrapper(*args, **kwargs):
        if 'subdomain' in kwargs:
            subdomain = kwargs['subdomain']
        else:
            subdomain = 'www'
        if current_user.verified == 0 or current_user.verified is None:
            return redirect(url_for('auth.verify_account', subdomain=subdomain))
        if (current_user.company_id == 0 or current_user.company_id == None):
            domain = Domains.query.filter_by(name=current_user.email.split('@')[1]).first()
            if domain is not None:
                if domain.fully_managed_domain == 1:
                    current_user.company_id = domain.company_id
                    db.session.add(current_user)
                    db.session.commit()
                else:
                    return redirect(url_for("main.invitation_required", subdomain=subdomain))
            return redirect(url_for("auth.create_company", subdomain=subdomain))
        else:
            return f(*args, **kwargs)
    wrapper.__doc__ = f.__doc__
    wrapper.__name__ = f.__name__
    return wrapper


@bp.route("/", methods=["GET"])
@bp.route("/search", methods=["GET"])
@bp.route("/index", methods=["GET"])
@login_required
@company_required
def index(subdomain='www'):
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", subdomain=subdomain))
    search_terms = request.args.get("q")
    if search_terms:
        title = "Search for \""+search_terms+"\""
    else:
        title="Trending"
    items = Controller.index(search_terms=search_terms, subdomain=subdomain)
    if len(items[0])==0 and not search_terms:
        flash("Welcome, there is no article yet in your company. Submit the first one by clicking the submit button", "success")
    if len(items[0])==0 and search_terms:
        flash("We did not find any matching result", "warning")
    
    return render_template(
        "index.html",
        subdomain=subdomain,
        title=title,
        posts=items[0],
        next_url=items[1],
        start_rank_num=items[2],
    )

@bp.route("/newest", methods=["GET"])
@login_required
@company_required
def new(subdomain='www'):
    items = Controller.new(subdomain=subdomain)
    return render_template(
        "index.html", 
        subdomain=subdomain,
        title="Newest",
        posts=items[0],
        next_url=items[1],
        start_rank_num=items[2],
    )

@bp.route("/invitation_required", methods=["GET"])
@login_required
def invitation_required(subdomain='www'):
    return render_template("invitation_required.html", subdomain=subdomain)


@bp.route("/user", methods=["GET"])
@login_required
@company_required
def user(subdomain='www'):
    company = Company.query.filter_by(id=current_user.company_id).first()
    return render_template(
        "user.html", subdomain=subdomain, user=current_user, company=company, title=f"Profile: {current_user.username}"
    )

@bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
@company_required
def edit_profile(subdomain='www'):
    form = EditProfileForm(current_user.username)
    # form.email(disabled=True)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved.", "success")
        return redirect(url_for("main.user", subdomain=subdomain))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        # form.email.data = current_user.email
    return render_template(
        "edit_profile.html", subdomain=subdomain, title="Edit profile", form=form
    )

@bp.route("/add_domain", methods=["GET", "POST"])
@login_required
@company_required
def add_domain(subdomain='www'):
    if not current_user.admin:
        flash("You are not admin of your company account, you cannot modify the authenication settings", "danger")
        return redirect(url_for('main.index', subdomain=subdomain))
    else:
        form = AddDomainForm(fully_managed_domain=True)
        if form.validate_on_submit():
            # TODO verify that the domain is not in a blacklisted list
            checkDomain = Domains.query.filter_by(name=form.name.data).first()
            if checkDomain is None:
                domain = Domains(name=form.name.data, fully_managed_domain=form.fully_managed_domain.data, company_id=current_user.company_id)
                db.session.add(domain)
                db.session.commit()
                flash("You add a new domain to your company", "success")
                return redirect(url_for("main.index", subdomain=subdomain))
            else:
                flash("The domain is already in your list", "warning")
        return render_template("add_domain.html", subdomain=subdomain, title="Add your company mail domain", form=form)

@bp.route("/manage_domain", methods=["GET", "POST"])
@login_required
@company_required
def manage_domain(subdomain='www'):
    domains = Domains.query.filter_by(company_id=current_user.company_id).all()
    return render_template(
        "manage_domain.html", subdomain=subdomain, title="Manage domain", domains=domains
    )

#TODO Should think about if a user A is invited by a user B, if user A is not in the same company, should it work ?
# Should user B only be able to invite user A if user A have an email in a domain approved in user B company ?
# It makes no sense for user B to invite user A if they would not share the same link list !
@bp.route("/invite_colleague", methods=["GET", "POST"])
@login_required
@company_required
def invite_colleague(subdomain='www'):
    form = LoginEmailForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        domain = Domains.query.filter_by(name=form.email.data.split('@')[1]).first()
        if domain is not None:
            if user is not None:
                if (user.company_id == 0 or user.company_id is None):
                    user.company_id = current_user.company_id
                    db.session.add(user)
                    db.session.commit()
                    flash("The user is added to your company", "success")
                else:
                    flash("The user have already an account and is assigned to a company", "warning")
            else:
                send_invitation(current_user, form.email.data)
                flash("You invited a colleague", "success")
                return redirect(url_for("main.index", subdomain=subdomain))
        else:
            flash('You cannot add a user with a email that is not registered as your company', 'warning')
        
    return render_template(
        "invite_colleague.html", subdomain=subdomain, title="Invite a colleague", form=form
    )

@bp.route("/submit", methods=["GET", "POST"])
@login_required
@company_required
def submit(subdomain='www'):
    form = PostForm()
    if form.validate_on_submit():
        if current_user.can_post():
            post = Post(
                title=form.title.data,
                url=form.url.data,
                text=form.text.data,
                author=current_user,
                company_id=current_user.company_id,
            )
            post.format_post(form.url.data)
            db.session.add(post)
            db.session.commit()
            flash("Congratulations, your post was published!", "success")
            return redirect(url_for("main.new", subdomain=subdomain))
        else:
            flash(
                f"Sorry, you can only post {current_app.config['USER_POSTS_PER_DAY']} times a day", "warning"
            )
            return redirect(url_for("main.index", subdomain=subdomain))

    return render_template("submit.html", subdomain=subdomain, title="Submit", form=form)

@bp.route("/edit_post/<post_id>", methods=["GET", "POST"])
@login_required
@company_required
def edit_post(post_id,subdomain='www'):
    
    post = Post.query.filter_by(company_id=current_user.company_id, id=post_id).first_or_404()
    form = PostForm(title=post.title, url=post.url, text=post.text)
    if current_user != post.author:
        flash("Sorry, you can only modify your own posts", "warning")
        return redirect(url_for('main.index', subdomain=subdomain))
    if form.validate_on_submit():
        if current_user == post.author:
            post.title=form.title.data
            post.url=form.url.data
            post.text=form.text.data
            post.format_post(form.url.data)
            db.session.add(post)
            db.session.commit()
            flash("Congratulations, your post was edited!", "success")
            return redirect(url_for("main.post_page", subdomain=subdomain, post_id=post.id))
        else:
            flash(
                f"Sorry, you can only modify your own posts", "warning"
            )
            return redirect(url_for("main.index", subdomain=subdomain))

    return render_template("submit.html", subdomain=subdomain, title="Edit post", form=form)

@bp.route("/post/<post_id>", methods=["GET", "POST"])
@login_required
@company_required
def post_page(post_id,subdomain='www'):
    post = Post.query.filter_by(company_id=current_user.company_id, deleted=0, id=post_id).first_or_404()

    comments = (
        Comment.query.filter_by(company_id=current_user.company_id, post_id=post.id)
        .order_by(Comment.thread_score.desc(), Comment.path.asc()).all()
    )
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            if current_user.can_comment():
                comment = Comment(
                    text=form.text.data,
                    author=current_user,
                    post_id=post.id,
                    timestamp=datetime.utcnow(),
                    thread_timestamp=datetime.utcnow(),
                    company_id=current_user.company_id,
                )
                comment.save()
                flash("Your comment is published", "success")
                return redirect(url_for("main.post_page", subdomain=subdomain, post_id=post.id))
            else:
                flash(
                    f"You can only commment {current_app.config['USER_COMMENTS_PER_DAY']} times a day.", "warning"
                )
        else:
            return redirect(url_for("auth.login", subdomain=subdomain))

    return render_template(
        "post.html", subdomain=subdomain, post=post, form=form, comments=comments, title=post.title
    )
    
@bp.route("/upvote/<post_id>", methods=["GET"])
@login_required
@company_required
def upvote(post_id,subdomain='www'):
    post_to_upvote = Post.query.filter_by(company_id=current_user.company_id, id=post_id).first_or_404()
    vote_query = Vote.query.filter_by(
        user_id=current_user.id, post_id=post_to_upvote.id
    ).first()
    if vote_query is not None:
        post_to_upvote.update_unvotes()
        db.session.delete(vote_query)
        db.session.commit()
        flash("You cancel your vote.", "success")
    else:
        post_to_upvote.update_votes()
        vote = Vote(user_id=current_user.id, post_id=post_to_upvote.id)
        db.session.add(vote)
        db.session.commit()
        flash("You upvoted the post.", "success")
    return redirect(redirect_url())

@bp.route("/delete/post/<post_id>", methods=["GET"])
@login_required
@company_required
def delete_post(post_id,subdomain='www'):
    post = Post.query.filter_by(company_id=current_user.company_id, id=post_id).first_or_404()
    if current_user == post.author or current_user.admin == 1:
        post.delete_post()
        db.session.commit()
        return redirect(redirect_url())
    else:
        return render_template("404.html", subdomain=subdomain), 404


@bp.route("/delete/comment/<comment_id>", methods=["GET"])
@login_required
@company_required
def delete_comment(comment_id,subdomain='www'):
    comment = Comment.query.filter_by(company_id=current_user.company_id, id=comment_id).first_or_404()
    if current_user == comment.author or current_user.admin == 1:
        comment.text = "[Deleted]"
        db.session.commit()
        return redirect(redirect_url())
    else:
        return render_template("404.html", subdomain=subdomain), 404


@bp.route("/submissions", methods=["GET"])
@login_required
@company_required
def user_submissions(subdomain='www'):
    posts = Post.query.filter_by(company_id=current_user.company_id, author=current_user, deleted=0).order_by(
        Post.timestamp.desc()
    )
    if (len(posts.all())==0):
        flash("You have not post any article yet, submit the first one by clicking on the submit button", "warning")
    return render_template("index.html", subdomain=subdomain, title="My posts", posts=posts)


@bp.route("/reply/<comment_id>", methods=["GET", "POST"])
@login_required
@company_required
def reply(comment_id,subdomain='www'):
    parent = Comment.query.filter_by(company_id=current_user.company_id, id=comment_id).first_or_404()
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            text=form.text.data,
            author=current_user,
            post_id=parent.post_id,
            parent_id=parent.id,
            timestamp=datetime.utcnow(),
            thread_timestamp=parent.thread_timestamp,
            company_id=current_user.company_id,
        )
        comment.save()
        return redirect(url_for("main.post_page", subdomain=subdomain, post_id=parent.post_id))
    return render_template("reply.html", subdomain=subdomain, comment=parent, form=form)


@bp.route("/upvote_comment/<comment_id>", methods=["GET"])
@login_required
@company_required
def upvote_comment(comment_id,subdomain='www'):
    # TODO unvote comment and check if comment is already upvoted
    comment_to_upvote = Comment.query.filter_by(company_id=current_user.company_id, id=comment_id).first_or_404()
    vote_query = Comment_Vote.query.filter_by(
        user_id=current_user.id, comment_id=comment_to_upvote.id
    ).first()
    if vote_query is not None:
        flash("You already voted in this comment.", "warning")
    else:
        comment_to_upvote.update_votes()
        vote = Comment_Vote(
            user_id=current_user.id, comment_id=comment_to_upvote.id
        )
        db.session.add(vote)
        db.session.commit()

    return redirect(redirect_url())
import os

@bp.route("/settings", methods=["GET"])
@login_required
@company_required
def settings(subdomain='www'):
    return render_template("settings.html", subdomain=subdomain, title="Settings")

@bp.route("/config")
def config(subdomain='www'):
    return render_template(
        "config.html", 
        subdomain=subdomain
    )

@bp.route("/privacy")
def privacy(subdomain='www'):
    return render_template(
        "privacy.html", 
        subdomain=subdomain,
        title="Privacy policy"
    )

@bp.route("/terms")
def terms(subdomain='www'):
    return render_template(
        "terms.html", 
        subdomain=subdomain,
        title="Terms of use"
    )

@bp.route("/static_file/<filename>", methods=["GET"])
def static_file(filename='', subdomain='www'):
    return current_app.send_static_file(filename)

    
# @bp.route("/init_mail_providers", methods=["GET"])
# def init_mail_providers():
#     print(os.getcwd())
#     csv_file_path = os.getcwd()+'/app/static/mail_providers.csv'
#     with open(csv_file_path, 'r') as f:    
#         lines = f.readlines()
#         for line in lines:
#             provider_exist = MailProviders.query.filter_by(domain=line.strip()).first()
#             if not provider_exist:
#                 new_mail_provider = MailProviders(domain=line.strip())
#                 db.session.add(new_mail_provider)
#                 db.session.commit()
#                 print(line.strip(), " - added")
#     return redirect(url_for("main.index", subdomain=subdomain))

# @bp.route("/load_new_data", methods=["GET"])
# def load_new_data():
#     csv_file_path = os.getcwd()+'/app/static/articles.csv'
#     i = 0
#     with open(csv_file_path, 'r') as f:    
#         lines = f.readlines()
#         for line in lines:
#             i = i + 1
#             print(i)
#             post_exist = Post.query.filter_by(title=line.split(';')[0]).first()
#             if not post_exist:
#                 post = Post(
#                     title=line.split(';')[0],
#                     url=line.split(';')[1],
#                     text='',
#                     author=current_user,
#                     company_id=current_user.company_id,
#                 )
#                 post.format_post(line.split(';')[1])
#                 db.session.add(post)
#                 db.session.commit()
#     return redirect(url_for("main.index", subdomain=subdomain))

