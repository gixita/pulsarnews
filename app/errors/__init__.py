from flask import Blueprint

bp = Blueprint("errors", __name__, subdomain="<subdomain>")

from app.errors import handlers
