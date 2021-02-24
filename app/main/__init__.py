from flask import Blueprint

bp_nosubdomain = Blueprint("main_nosubdomain", __name__)
bp = Blueprint("main", __name__, subdomain="<subdomain>")

from app.main import routes

