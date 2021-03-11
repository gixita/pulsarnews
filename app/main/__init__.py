from flask import Blueprint
from app import subdomain_config

if subdomain_config.is_subdomain_enable:
    bp = Blueprint("main", __name__, subdomain="<subdomain>")
else:
    bp = Blueprint("main", __name__)

from app.main import routes

