from flask import flash, redirect, render_template, request, url_for, jsonify
from flask_login import current_user, login_required
from app.models import Administrator

from app.admin import bp

def super_admin_required(f):
    def wrapper(*args, **kwargs):
        if current_user.verified == 0 or current_user.verified is None:
            return redirect(url_for('auth.verify_account'))
        if (current_user.company_id == 0 or current_user.company_id == None):
            return redirect(url_for("auth.create_company"))
        super_admin = Administrator.query.filter_by(user_id=current_user.id).first()
        if super_admin:
            if super_admin.is_admin:
                return f(*args, **kwargs)
        else:
            flash("You cannot access this section, please move on", "danger")
            return redirect(url_for("main.index"))
    wrapper.__doc__ = f.__doc__
    wrapper.__name__ = f.__name__
    return wrapper


@bp.route("/", methods=["GET"])
@bp.route("/index", methods=["GET"])
@login_required
@super_admin_required
def index():
    return render_template("admin/base.html", title="Invite a colleague")