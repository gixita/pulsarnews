from app.models import User, Post, Vote, Comment, Comment_Vote, RefreshToken


def test_new_user(new_user):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the email, hashed_password, and role fields are defined correctly
    """
    assert new_user.email == 'kris@pulsarnews.io'
    assert new_user.username == 'kris'