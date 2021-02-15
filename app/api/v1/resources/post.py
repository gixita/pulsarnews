from flask_restplus import Resource, Namespace
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
import jwt
import json
from flask_login import current_user, login_required

from app import db
from app.main.forms import CommentForm, EditProfileForm, PostForm
from app.models import Comment, Post, User, Vote, Comment_Vote
from app.main import bp
from app.main.controller import Controller

post_ns = Namespace('post')

from ..utils import token_required

@post_ns.route('/bests')
@post_ns.route('/bests/<int:page>')
class Bests(Resource):
    def get(self, page=1):
        items = Controller.index(page)
        return jsonify([json.loads(i.to_json(max_nesting=1)) for i in items[0]])

@post_ns.route('/bests_getids')
@post_ns.route('/bests_getids/<int:page>')
class Bests_Getids(Resource):
    def get(self, page=1):
        items = Controller.index(page)
        return jsonify([i.id for i in items[0]])

@post_ns.route('/post_byid/<int:post_id>')
class Post_Byid(Resource):
    def get(self, post_id):
        item = Controller.post_by_id(post_id)
        return jsonify(json.loads(item.to_json(max_nesting=1)))

@post_ns.route('/comment/<int:comment_id>')
class Comment_Page(Resource):
    def get(self, comment_id):
        item = Controller.comment_page(comment_id)
        return jsonify(json.loads(item.to_json(max_nesting=1)))

@post_ns.route('/upvote')
class Upvote(Resource):
    @token_required
    def post(self, current_user):
        item = Controller.upvote(int(request.form['id']), current_user)
        if item:
            return {"post_id": int(request.form['id'])}, 200
        post_ns.abort(401, 'You already voted')

# Args : title, url, text, current_user
@post_ns.route('/submit')
class Submit(Resource):
    @token_required
    def post(self, current_user):
        item = Controller.submit(request.form['title'], request.form['url'], request.form['text'], current_user)
        if item:
            return {"message": "You submited a new post"}, 200
        post_ns.abort(401, 'You cannot post')

@post_ns.route('/reply_post')
class ReplyPost(Resource):
    @token_required
    def post(self, current_user):
        item = Controller.reply_post(request.form['post_id'], request.form['text'], current_user)
        if item:
            return {"message": "You submited a new post"}, 200
        post_ns.abort(401, 'You cannot post')

@post_ns.route('/reply_comment')
class ReplyComment(Resource):
    @token_required
    def post(self, current_user):
        item = Controller.reply_comment(request.form['comment_id'], request.form['text'], current_user)
        if item:
            return {"message": "You replied to a comment"}, 200
        post_ns.abort(401, 'You cannot reply to this comment')

@post_ns.route('/upvote_comment')
class UpvoteComment(Resource):
    @token_required
    def post(self, current_user):
        item = Controller.upvote_comment(request.form['comment_id'], current_user)
        if item:
            return {"message": "You upvoted a comment"}, 200
        post_ns.abort(401, 'You cannot upvote this comment')

@post_ns.route('/delete_comment')
class UpvoteComment(Resource):
    @token_required
    def post(self, current_user):
        item = Controller.delete_comment(request.form['comment_id'], current_user)
        if item:
            return {"message": "You deleted your comment"}, 200
        post_ns.abort(401, 'You cannot cannot this comment')

@post_ns.route('/delete_post')
class UpvoteComment(Resource):
    @token_required
    def post(self, current_user):
        item = Controller.delete_post(request.form['post_id'], current_user)
        if item:
            return {"message": "You deleted your post"}, 200
        post_ns.abort(401, 'You cannot cannot this post')

@post_ns.route('/user_submissions')
class UpvoteComment(Resource):
    @token_required
    def get(self, current_user):
        items = Controller.user_submissions(current_user)
        return jsonify([json.loads(i.to_json(max_nesting=1)) for i in items])
