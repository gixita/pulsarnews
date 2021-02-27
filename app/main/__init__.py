from flask import Blueprint
from app import is_subdomain_enable

if is_subdomain_enable:
    bp = Blueprint("main", __name__, subdomain="<subdomain>")
else:
    bp = Blueprint("main", __name__)

from app.main import routes

