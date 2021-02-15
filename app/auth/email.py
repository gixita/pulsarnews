from flask import render_template, current_app
from app.email import send_email


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(
        subject="Flasknews password recovery",
        sender=current_app.config["MAIL_ADMIN_ADDRESS"],
        recipients=[user.email],
        text_body=render_template(
            "email/reset_password.txt", user=user, token=token
        ),
        html_body=render_template(
            "email/reset_password.html", user=user, token=token
        ),
    )

def send_verification_email(user):
    token = user.get_mail_verification_token()
    # link = 'http://localhost:5000/auth/verify_account?token='+ token 
    # print(link)
    send_email(
        subject="Flasknews password recovery",
        sender=current_app.config["MAIL_ADMIN_ADDRESS"],
        recipients=[user.email],
        text_body=render_template(
            "email/email_verification.txt", user=user, token=token
        ),
        html_body=render_template(
            "email/email_verification.html", user=user, token=token
        ),
    )
