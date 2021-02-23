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
from app.main.forms import CommentForm, EditProfileForm, PostForm
from app.models import Comment, Post, User, Vote, Comment_Vote
from app.main import bp

class Controller:
    def redirect_url(default="main.index"):
        return request.args.get("next") or request.referrer or url_for(default)


    def index(search_terms='', current_page = 1, subdomain='www'):
        if search_terms is None:
            posts_to_update = ( Post.query.filter_by(company_id=current_user.company_id, deleted=0)
                                .order_by(Post.timestamp.desc())
                                .limit(current_app.config["TOTAL_POSTS"])
            )
        else:
            search_terms_contains = '%'+search_terms+'%'
            posts_to_update = ( Post.query.filter_by(company_id=current_user.company_id, deleted=0)
                                .filter(Post.title.ilike(search_terms_contains) | Post.text.ilike(search_terms_contains))
                                .order_by(Post.timestamp.desc())
                                .limit(current_app.config["TOTAL_POSTS"])
            )
        for post in posts_to_update.all():
            post.update()
        db.session.commit()

        if (request.args.get("page")==None):
            page = current_page
        else:
            page = request.args.get("page", 1, type=int)
        posts = (
            posts_to_update
            .from_self()
            .order_by(Post.pop_score.desc())
            .paginate(page, current_app.config["POSTS_PER_PAGE"], True)
        )
        
        start_rank_num = current_app.config["POSTS_PER_PAGE"] * (page - 1) + 1
        if search_terms is None:
            next_url = (
                url_for("main.index", subdomain=subdomain, page=posts.next_num) if posts.has_next else None
            )
        else:
            next_url = (
                url_for("main.index", subdomain=subdomain, page=posts.next_num, q=search_terms) if posts.has_next else None
            )
        return [posts.items,
            next_url,
            start_rank_num,
        ]

    def new():
        page = request.args.get("page", 1, type=int)
        posts = (
            Post.query.filter_by(company_id=current_user.company_id, deleted=0)
            .order_by(Post.timestamp.desc())
            .paginate(page, current_app.config["POSTS_PER_PAGE"], True)
        )

        start_rank_num = current_app.config["POSTS_PER_PAGE"] * (page - 1) + 1
        next_url = (
            url_for("main.new", page=posts.next_num) if posts.has_next else None
        )

        return [posts.items,
            next_url,
            start_rank_num,
        ]


    def user(username):
        user = User.query.filter_by(username=username).first_or_404()
        return [user, username]

    def edit_profile(username, about_me, email, current_user):
        current_user.username = username
        current_user.about_me = about_me
        current_user.email = email
        db.session.commit()
        return True


    def submit(title, url, text, current_user):
        if current_user.can_post():
            post = Post(
                title=title,
                url=url,
                text=text,
                author=current_user,
                company_id=current_user.company_id,
            )
            post.format_post(url)
            db.session.add(post)
            db.session.commit()
            return True
        else:
            return False


    def post_page(post_id):
        post = Post.query.filter_by(company_id=current_user.company_id, id=post_id).first_or_404()

        comments = (
            Comment.query.filter_by(company_id=current_user.company_id, post_id=post.id)
            # .order_by(Comment.thread_timestamp.desc(), Comment.path.asc())
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
                    return redirect(url_for("main.post_page", post_id=post.id))
                else:
                    flash(
                        f"You can only commment {current_app.config['USER_COMMENTS_PER_DAY']} times a day."
                    )
            else:
                return redirect(url_for("auth.login"))

        return [post, form, comments]

    def reply_post(post_id, text, current_user):
        if current_user.is_authenticated:
            if current_user.can_comment():
                comment = Comment(
                    text=text,
                    author=current_user,
                    post_id=post_id,
                    timestamp=datetime.utcnow(),
                    thread_timestamp=datetime.utcnow(),
                    company_id=current_user.company_id,
                )
                comment.save()
                return True
            else:
                return False
    
    def reply_comment(comment_id, text, current_user):
        if current_user.is_authenticated:
            if current_user.can_comment():
                parent = Comment.query.filter_by(company_id=current_user.company_id, id=comment_id).first_or_404()
    
                comment = Comment(
                text=text,
                author=current_user,
                post_id=parent.post_id,
                parent_id=parent.id,
                timestamp=datetime.utcnow(),
                thread_timestamp=parent.thread_timestamp,
                company_id=current_user.company_id,
                )
                comment.save()
                return True 
        return False

    def comment_page(comment_id):
        comment = Comment.query.filter_by(company_id=current_user.company_id, id=comment_id).first_or_404()
        return comment
        

    def post_by_id(post_id):
        post = Post.query.filter_by(company_id=current_user.company_id, deleted=0, id=post_id).first_or_404()
        return post

    def upvote(post_id, current_user):
        post_to_upvote = Post.query.filter_by(company_id=current_user.company_id, deleted=0, id=post_id).first_or_404()
        vote_query = Vote.query.filter_by(
            user_id=current_user.id, post_id=post_to_upvote.id
        ).first()
        if vote_query is not None:
            return False
        else:
            post_to_upvote.update_votes()
            vote = Vote(user_id=current_user.id, post_id=post_to_upvote.id)
            db.session.add(vote)
            db.session.commit()

        return True

    def delete_post(post_id, current_user):
        post = Post.query.filter_by(company_id=current_user.company_id, id=post_id).first_or_404()
        if current_user == post.author:
            post.delete_post()
            db.session.commit()
            return True # should redirect
        return False # should throw an error message


    def delete_comment(comment_id, current_user):
        comment = Comment.query.filter_by(company_id=current_user.company_id, id=comment_id).first_or_404()
        if current_user == comment.author:
            comment.text = "[Deleted]"
            db.session.commit()
            return True
        return False



    def user_submissions(current_user):
        user = User.query.filter_by(username=current_user.username).first_or_404()
        posts = Post.query.filter_by(author=user, deleted=0).order_by(
            Post.timestamp.desc()
        )
        return posts


    def reply(comment_id):
        parent = Comment.query.filter_by(id=comment_id).first_or_404()
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
            return parent.post_id
        return [parent, form]


    def upvote_comment(comment_id, current_user):
        comment_to_upvote = Comment.query.filter_by(id=comment_id).first_or_404()
        vote_query = Comment_Vote.query.filter_by(
            user_id=current_user.id, comment_id=comment_to_upvote.id
        ).first()
        if vote_query is None:
            comment_to_upvote.update_votes()
            vote = Comment_Vote(
                user_id=current_user.id, comment_id=comment_to_upvote.id
            )
            db.session.add(vote)
            db.session.commit()
            return True
        return False
