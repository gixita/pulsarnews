import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app-test.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_ADMIN_ADDRESS = 'mail@mail.com' 
    MAIL_SERVER = 'smtp.mail98998989898.com' 
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = 'mail@mail.com'
    MAIL_PASSWORD = 'PasswordMail'
    POSTS_PER_PAGE = 50
    TOTAL_POSTS = 100
    USER_POSTS_PER_DAY = 20000000
    USER_COMMENTS_PER_DAY = 15
    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")
    WTF_CSRF_ENABLED = False
    SERVER_NAME = os.environ.get("SERVER_NAME")
    
    #Azure auth
    TENANT = os.environ.get('TENANT')
    RESOURCE = os.environ.get('RESOURCE')
    CLIENT_ID = os.environ.get('CLIENT_ID')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
    CALLBACK_PATH = '/auth/signin-oidc'
    AUTHORITY = os.environ.get('AUTHORITY')
    REDIRECT_PATH = os.environ.get('REDIRECT_PATH')
    ENDPOINT = os.environ.get('ENDPOINT')
    SCOPE = [os.environ.get('SCOPE')]
    SESSION_TYPE = "filesystem" 
    IS_SUBDOMAIN_ENABLE = (os.environ.get("IS_SUBDOMAIN_ENABLE") == 'True')