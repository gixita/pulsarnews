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
import json


from app import db
from app.main.forms import CommentForm, EditProfileForm, PostForm
from app.models import Comment, Post, User, Vote, Comment_Vote
from app.main import bp

from app.main.controller import Controller

user_ns = Namespace('user')

from ..utils import token_required

@user_ns.route('/edit_profile')
class EditProfile(Resource):
    @token_required
    def post(self, current_user):
        return Controller.edit_profile(request.form['username'], request.form['about_me'], request.form['email'], current_user)
    

@user_ns.route('/username/<string:username>')
class GetUsername(Resource):
    @token_required
    def get(self, username, current_user):
        return jsonify(json.loads(Controller.user(username)[0].to_json(max_nesting=0)))
