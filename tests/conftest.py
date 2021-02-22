import pytest
from app import create_app, db
from app.models import User
from configtest import Config


@pytest.fixture(scope='module')
def new_user():
    user = User(username="kris", email="kris@pulsarnews.io")
    return user


@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app(Config)

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            yield testing_client  # this is where the testing happens!


@pytest.fixture(scope='module')
def init_database(test_client):
    # Create the database and the database table
    db.create_all()

    # Insert user data
    user1 = User(username="info", email="info@pulsarnews.io")
    user2 = User(username="support", email="support@pulsarnews.io")
    user1.set_password("password")
    user2.set_password("password")
    db.session.add(user1)
    db.session.add(user2)

    # Commit the changes for the users
    db.session.commit()

    yield  # this is where the testing happens!

    db.drop_all()


@pytest.fixture(scope='function')
def login_default_user(test_client):
    test_client.post('/auth/login_password',
                        data=dict(email='info@pulsarnews.io', password='password'),
                        follow_redirects=True)
    
    yield  # this is where the testing happens!

    test_client.get('/auth/logout', follow_redirects=True)
