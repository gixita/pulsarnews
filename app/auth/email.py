from flask import render_template, current_app
# from app.email import send_email
import boto3

def send_email(app, recipients, sender=None, subject='', text='', html=''):
    ses = boto3.client(
        'ses',
        region_name=app.config['SES_REGION_NAME'],
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY']
    )
    if not sender:
        sender = app.config['SES_EMAIL_SOURCE']

    ses.send_email(
        Source=sender,
        Destination={'ToAddresses': recipients},
        Message={
            'Subject': {'Data': subject},
            'Body': {
                'Text': {'Data': text},
                'Html': {'Data': html}
            }
        }
    )

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(
        subject="PulsarNews password recovery",
        sender=current_app.config["SES_EMAIL_SOURCE"],
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
    recipients=[user.email]
    subject="PulsarNews email verification"

    # You can render the message using Jinja2
    html = render_template('email/email_verification.html', user=user, token=token)

    send_email(current_app,
        recipients=recipients,
        subject=subject,
        html=html
        )
    
    # send_email(
    #     subject="PulsarNews email verification",
    #     sender=current_app.config["MAIL_ADMIN_ADDRESS"],
    #     recipients=[user.email],
    #     text_body=render_template(
    #         "email/email_verification.txt", user=user, token=token
    #     ),
    #     html_body=render_template(
    #         "email/email_verification.html", user=user, token=token
    #     ),
    # )
