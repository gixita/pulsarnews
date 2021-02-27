from flask import Blueprint
from app import is_subdomain_enable

if is_subdomain_enable:
    bp = Blueprint("admin", __name__, subdomain="<subdomain>")
else:
    bp = Blueprint("admin", __name__)

from app.admin import routes
