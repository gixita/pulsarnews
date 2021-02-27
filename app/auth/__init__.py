from flask import Blueprint
from app import is_subdomain_enable

if is_subdomain_enable:
    bp = Blueprint("auth", __name__, subdomain="<subdomain>")
else:
    bp = Blueprint("auth", __name__)
    
from app.auth import routes

