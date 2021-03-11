from flask import Blueprint
from app import subdomain_config

if subdomain_config.is_subdomain_enable:
    bp = Blueprint("admin", __name__, subdomain="<subdomain>")
else:
    bp = Blueprint("admin", __name__)

from app.admin import routes
