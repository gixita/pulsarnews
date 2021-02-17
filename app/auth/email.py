from flask import render_template, current_app
import boto3

# TODO manage hard bounces
# https://aws.amazon.com/blogs/messaging-and-targeting/handling-bounces-and-complaints/

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
    recipients=[user.email]
    subject="Password reset - PulsarNews"
    html = render_template('email/reset_password.html', user=user, token=token)
    send_email(current_app,
        recipients=recipients,
        subject=subject,
        html=html
        )

def send_verification_email(user):
    token = user.get_mail_verification_token()
    # # link = 'http://localhost:5000/auth/verify_account?token='+ token 
    # print(link)
    recipients=[user.email]
    subject="Email verification - PulsarNews"
    html = render_template('email/email_verification.html', user=user, token=token)
    send_email(current_app,
        recipients=recipients,
        subject=subject,
        html=html
        )