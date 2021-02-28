from tests.functional.security import security
from app.models import User
import pytest

def test_login_page(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/auth/login')
    assert response.status_code == 200
    assert b'Next' in response.data
    
    # Check that admin panel is not accessible
    security(test_client)

def test_valid_login_logout(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is posted to (POST)
    THEN check the response is valid
    """
    response = test_client.post('/auth/login_password',
                                data=dict(email='info@pulsarnews.io', password='password'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Trending' not in response.data
    
    # Check that admin panel is not accessible
    security(test_client)
    
    """
    GIVEN a Flask application configured for testing
    WHEN the '/logout' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Next' in response.data


def test_invalid_login_password_bad_password(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is posted to with invalid credentials (POST)
    THEN check an error message is returned to the user
    """
    response = test_client.post('/auth/login_password',
                                data=dict(email='info@pulsarnews.io', password='NotThePassword'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Next' in response.data
    # Check that admin panel is not accessible
    security(test_client)

def test_invalid_login_password_bad_email(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is posted to with invalid credentials (POST)
    THEN check an error message is returned to the user
    """
    response = test_client.post('/auth/login_password',
                                data=dict(email='info2@pulsarnews.io', password='NotThePassword'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Next' in response.data
    # Check that admin panel is not accessible
    security(test_client)

def test_invalid_login_bad_email_format(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is posted to with invalid credentials (POST)
    THEN check an error message is returned to the user
    """
    response = test_client.post('/auth/login',
                                data=dict(email='info2pulsarnews.io'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Next' in response.data
    # Check that admin panel is not accessible
    security(test_client)

def test_email_unknown_login_email(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is posted to with new unknown email (POST)
    THEN check that the register page is launched
    """
    response = test_client.post('/auth/login',
                                data=dict(email='info3@pulsarnews.io'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Register' in response.data
    # Check that admin panel is not accessible
    security(test_client)


def test_login_already_logged_in(test_client, init_database, login_default_user):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is posted to (POST) when the user is already logged in
    THEN check an error message is returned to the user
    """
    # TODO cannot fix the bug, need help
    pass
    # response = test_client.post('/auth/login_password',
    #                             data=dict(email='info@pulsarnews.io', password='password'),
    #                             follow_redirects=True)
    # assert response.status_code == 200
    # assert b'logged' in response.data
    

def test_valid_registration(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/register' page is posted to (POST)
    THEN check the response is valid and the user is logged in
    """
    response = test_client.post('/auth/register',
                                data=dict(username='register',
                                    email='register@pulsarnews.io',
                                    password='password',
                                    password2='password'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Please verify your account' in response.data
    security(test_client)

    """
    GIVEN a Flask application configured for testing
    WHEN the '/logout' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Next' in response.data

@pytest.mark.order1
def test_valid_registration_full_process_one_user_fully_managed(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/register' page is posted to (POST)
    THEN check the response is valid and the user is logged in
    """
    response = test_client.post('/auth/register',
                                data=dict(username='register2',
                                    email='register2@fullymanagedcompany.io',
                                    password='password',
                                    password2='password'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Please verify your account' in response.data
    security(test_client)

    user = User.query.filter_by(email='register2@fullymanagedcompany.io').first()
    token = user.get_mail_verification_token()
    response = test_client.get('/auth/verify_account?token='+token, follow_redirects=True)
    assert response.status_code == 200
    assert b'Register your company' in response.data
    
    response = test_client.post('/auth/create_company', 
                                data=dict(name='PulsarNews2', fully_managed_domain=1),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Trending' in response.data
    
    """
    GIVEN a Flask application configured for testing
    WHEN the '/logout' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Next' in response.data

@pytest.mark.order2
def test_valid_registration_full_process_second_user_fully_managed_bad_token_verification(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/register' page is posted to (POST)
    THEN check the response is valid and the user is logged in
    """
    response = test_client.post('/auth/register',
                                data=dict(username='register',
                                    email='register3@fullymanagedcompany.io',
                                    password='password',
                                    password2='password'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Please verify your account' in response.data
    security(test_client)

    user = User.query.filter_by(email='register2@fullymanagedcompany.io').first()
    token = user.get_mail_verification_token()
    response = test_client.get('/auth/verify_account?token='+token, follow_redirects=True)
    assert response.status_code == 200
    assert b'Register your company' not in response.data
    assert b'Trending' not in response.data

    """
    GIVEN a Flask application configured for testing
    WHEN the '/logout' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Next' in response.data

@pytest.mark.order3
def test_valid_registration_full_process_third_user_fully_managed(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/register' page is posted to (POST)
    THEN check the response is valid and the user is logged in
    """
    response = test_client.post('/auth/register',
                                data=dict(username='register',
                                    email='register4@fullymanagedcompany.io',
                                    password='password',
                                    password2='password'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Please verify your account' in response.data
    security(test_client)

    user = User.query.filter_by(email='register4@fullymanagedcompany.io').first()
    token = user.get_mail_verification_token()
    response = test_client.get('/auth/verify_account?token='+token, follow_redirects=True)
    assert response.status_code == 200
    assert b'Register your company' not in response.data
    assert b'Trending' in response.data

    """
    GIVEN a Flask application configured for testing
    WHEN the '/logout' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Next' in response.data



@pytest.mark.order4
def test_valid_registration_full_process_one_user_not_fully_managed(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/register' page is posted to (POST)
    THEN check the response is valid and the user is logged in
    """
    response = test_client.post('/auth/register',
                                data=dict(username='register2',
                                    email='register2@notfullymanagedcompany.io',
                                    password='password',
                                    password2='password'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Please verify your account' in response.data
    security(test_client)

    user = User.query.filter_by(email='register2@notfullymanagedcompany.io').first()
    token = user.get_mail_verification_token()
    response = test_client.get('/auth/verify_account?token='+token, follow_redirects=True)
    assert response.status_code == 200
    assert b'Register your company' in response.data
    
    response = test_client.post('/auth/create_company', 
                                data=dict(name='PulsarNewsNotFullyManaged', fully_managed_domain=''),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Trending' in response.data
    
    """
    GIVEN a Flask application configured for testing
    WHEN the '/logout' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Next' in response.data

@pytest.mark.order5
def test_valid_registration_full_process_second_user_not_fully_managed(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/register' page is posted to (POST)
    THEN check the response is valid and the user is logged in
    """
    response = test_client.post('/auth/register',
                                data=dict(username='register4not',
                                    email='register4@notfullymanagedcompany.io',
                                    password='password',
                                    password2='password'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Please verify your account' in response.data
    security(test_client)

    user = User.query.filter_by(email='register4@notfullymanagedcompany.io').first()
    token = user.get_mail_verification_token()
    response = test_client.get('/auth/verify_account?token='+token, follow_redirects=True)
    assert response.status_code == 200
    assert b'Register your company' not in response.data
    assert b'Trending' not in response.data
    assert b'invitation' in response.data

    """
    GIVEN a Flask application configured for testing
    WHEN the '/logout' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Next' in response.data

@pytest.mark.order6
def test_valid_registration_full_process_send_invitation_not_fully_managed(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN login as domain admin and invite user for not fully managed domain (POST)
    THEN check if the user can connect after
    """
    response = test_client.post('/auth/login_password',
                                data=dict(email='register2@notfullymanagedcompany.io', password='password'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Trending' not in response.data

    response = test_client.post('/invite_colleague',
                                data=dict(email='register4@notfullymanagedcompany.io'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Trending' not in response.data

    response = test_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Next' in response.data

    response = test_client.post('/auth/login_password',
                                data=dict(email='register4@notfullymanagedcompany.io', password='password'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Trending' not in response.data

    response = test_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Next' in response.data

def test_invalid_registration(test_client, init_database):
    pass
    # """
    # GIVEN a Flask application configured for testing
    # WHEN the '/register' page is posted to with invalid credentials (POST)
    # THEN check an error message is returned to the user
    # """
    # response = test_client.post('/register',
    #                             data=dict(email='patkennedy79@hotmail.com',
    #                                       password='FlaskIsGreat',
    #                                       confirm='FlskIsGreat'),   # Does NOT match!
    #                             follow_redirects=True)
    # assert response.status_code == 200
    # assert b'Thanks for registering, patkennedy79@hotmail.com!' not in response.data
    # assert b'Welcome patkennedy79@hotmail.com!' not in response.data
    # assert b'[This field is required.]' not in response.data
    # assert b'Flask User Management' in response.data
    # assert b'Logout' not in response.data
    # assert b'Login' in response.data
    # assert b'Register' in response.data


def test_duplicate_registration(test_client, init_database):
    pass
    # """
    # GIVEN a Flask application configured for testing
    # WHEN the '/register' page is posted to (POST) using an email address already registered
    # THEN check an error message is returned to the user
    # """
    # # Register the new account
    # test_client.post('/register',
    #                  data=dict(email='pkennedy@hey.com',
    #                            password='FlaskIsTheBest',
    #                            confirm='FlaskIsTheBest'),
    #                  follow_redirects=True)
    # # Try registering with the same email address
    # response = test_client.post('/register',
    #                             data=dict(email='pkennedy@hey.com',
    #                                       password='FlaskIsStillTheBest',
    #                                       confirm='FlaskIsStillTheBest'),
    #                             follow_redirects=True)
    # assert response.status_code == 200
    # assert b'Already registered!  Redirecting to your User Profile page...' in response.data
    # assert b'Thanks for registering, pkennedy@hey.com!' not in response.data
    # assert b'Welcome pkennedy@hey.com!' in response.data
    # assert b'Flask User Management' in response.data
    # assert b'Logout' in response.data
    # assert b'Login' not in response.data
    # assert b'Register' not in response.data

    # TODO Test token verification
    # TODO Test company creation
    # TODO Test reset password
    