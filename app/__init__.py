from flask import Flask

from config import Config
from flask_sqlalchemy import SQLAlchemy
from sqlathanor import FlaskBaseModel, initialize_flask_sqlathanor
from flask_migrate import Migrate
from flask_moment import Moment
from flask_login import LoginManager
import os
from logging.handlers import RotatingFileHandler
import logging
from flaskext.markdown import Markdown
from flask_mail import Mail

is_subdomain_enable = True

db = SQLAlchemy(model_class=FlaskBaseModel)
migrate = Migrate(compare_type=True)
login = LoginManager()
login.blueprint_login_views = {
    'auth': '/auth/login',
    'main': '/auth/login',
    'errors': '/auth/login',
    'admin': '/auth/login',
}
login.login_message = ""
mail = Mail()
moment = Moment()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config.update(SESSION_TYPE = 'filesystem')
    app.static_folder = 'static'

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    markdown = Markdown(app)

    # TODO manage themes (dark, ...)
    
    from app.errors import bp as errors_bp

    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.admin import bp as admin_bp

    app.register_blueprint(admin_bp, url_prefix="/admin")

    from app.api.v1 import v1_blueprint as api_bp

    app.register_blueprint(api_bp, url_prefix="/api/v1")

    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    if not app.debug:
        if app.config["LOG_TO_STDOUT"]:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:

            if not os.path.exists("logs"):
                os.mkdir("logs")
            file_handler = RotatingFileHandler(
                "logs/devpt.log", maxBytes=10240, backupCount=10
            )
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            app.logger.setLevel(logging.INFO)
            app.logger.info("Flasknews startup")

    return app


from app import models
