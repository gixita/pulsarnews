import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY")
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
    SES_EMAIL_SOURCE = os.environ.get("SES_EMAIL_SOURCE")
    SES_REGION_NAME = os.environ.get("SES_REGION")
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    POSTS_PER_PAGE = 7
    TOTAL_POSTS = 100
    USER_POSTS_PER_DAY = 200
    USER_COMMENTS_PER_DAY = 15
    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")
