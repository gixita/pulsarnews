from flask import render_template
from app import db
from app.errors import bp


@bp.app_errorhandler(404)
def not_found_error(error, subdomain='www'):
    return render_template("errors/404.html", subdomain=subdomain), 404


@bp.app_errorhandler(500)
def internal_error(error, subdomain='www'):
    db.session.rollback()
    return render_template("errors/500.html", subdomain=subdomain), 500
