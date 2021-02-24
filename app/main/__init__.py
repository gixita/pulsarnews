from flask import Blueprint

bp = Blueprint("main", __name__, subdomain="<subdomain>")

from app.main import routes

