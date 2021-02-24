from flask import Blueprint

bp = Blueprint("auth", __name__)#, subdomain="<subdomain>")

from app.auth import routes

