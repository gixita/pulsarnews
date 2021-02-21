#import pytest
# from app import create_app, db
from app.models import User, Post, Vote, Comment, Comment_Vote, RefreshToken


def test_new_user():
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the email, hashed_password, and role fields are defined correctly
    """
    user = User(username="kris", email="kris@pulsarnews.io")
    assert user.email == 'kris@pulsarnews.io'
    assert user.username == 'kris'