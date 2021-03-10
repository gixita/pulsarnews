import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY")
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_ADMIN_ADDRESS = os.environ.get("MAIL_ADMIN_ADDRESS")
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    POSTS_PER_PAGE = 50
    TOTAL_POSTS = 100
    USER_POSTS_PER_DAY = 20000000
    USER_COMMENTS_PER_DAY = 15
    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")
    WTF_CSRF_ENABLED = (os.environ.get("PRODUCTION") == 'True')
    SERVER_NAME = os.environ.get("SERVER_NAME")
    SESSION_COOKIE_SECURE = os.environ.get("PRODUCTION")
    REMEMBER_COOKIE_SECURE = os.environ.get("PRODUCTION")
    SESSION_COOKIE_HTTPONLY = os.environ.get("PRODUCTION")
    REMEMBER_COOKIE_HTTPONLY = os.environ.get("PRODUCTION")
    
    #Azure auth
    SESSION_TYPE = "filesystem" 
