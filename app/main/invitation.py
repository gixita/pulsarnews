from flask import render_template, current_app
from app.email import send_email
import jwt


def send_invitation(user, invitation_email):
    token = user.get_invitation_token()
    link = 'http://localhost:5000/auth/register?token='+token
    print(token)
    # send_email(
    #     subject="Flasknews password recovery",
    #     sender=current_app.config["MAIL_ADMIN_ADDRESS"],
    #     recipients=[invitation_email],
    #     text_body=render_template(
    #         "email/reset_password.txt", user=invitation_email, token=token
    #     ),
    #     html_body=render_template(
    #         "email/reset_password.html", user=invitation_email, token=token
    #     ),
    # )

def verify_invitation_token(token):
    try:
        company_id = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
        )["company_id"]
    except Exception:
        return
    return company_id