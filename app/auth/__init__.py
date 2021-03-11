from flask import Blueprint
from app import subdomain_config

if subdomain_config.is_subdomain_enable:
    bp = Blueprint("auth", __name__, subdomain="<subdomain>")
else:
    bp = Blueprint("auth", __name__)
    
from app.auth import routes

