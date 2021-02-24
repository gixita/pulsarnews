from flask import render_template, current_app
from app.email import send_email

def send_password_reset_email(user, subdomain='www'):
    token = user.get_reset_password_token()
    send_email(subject="Password reset - PulsarNews",
        sender=current_app.config["MAIL_ADMIN_ADDRESS"],
        recipients=[user.email],
        text_body=render_template(
            "email/reset_password.txt", subdomain=subdomain, user=user, token=token
        ),
        html_body=render_template(
            "email/reset_password_bootstrap.html", subdomain=subdomain, user=user, token=token
        )
    )

def send_verification_email(user, subdomain='www'):
    token = user.get_mail_verification_token()
    link = 'http://localhost:5000/auth/verify_account?token='+ token 
    print(link)
    # send_email(subject="Email verification - PulsarNews",
    #     sender=current_app.config["MAIL_ADMIN_ADDRESS"],
    #     recipients=[user.email],
    #     text_body=render_template(
    #         "email/email_verification.txt", subdomain=subdomain, user=user, token=token
    #     ),
    #     html_body=render_template(
    #         "email/email_verif_bootstrap.html", subdomain=subdomain, user=user, token=token
    #     )
    # )