from flask_restplus import Resource, Namespace

from app import db
from app.v1 import v1_api
from .auth import token_required

todo_ns = Namespace('todo')


@todo_ns.route('/')
class TodoList(Resource):
    @todo_ns.marshal_with(TodoModel.todo_resource_model)
    @token_required
    def get(self, current_user):
        """Get todos list"""
        tasks = TodoModel.query.filter_by(user=current_user).all()
        return tasks

    @todo_ns.expect(TodoModel.todo_resource_model, validate=True)
    @todo_ns.marshal_with(TodoModel.todo_resource_model)
    @token_required
    def post(self, current_user):
        """Create a new task"""
        task = v1_api.payload['task']
        try:
            done = v1_api.payload['done']
        except KeyError:
            done = False

        todo = TodoModel(task=task, done=done, user=current_user)
        db.session.add(todo)
        db.session.commit()
        return todo
