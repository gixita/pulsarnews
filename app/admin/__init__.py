from flask import Blueprint

bp = Blueprint("admin", __name__, subdomain="<subdomain>")

from app.admin import routes
