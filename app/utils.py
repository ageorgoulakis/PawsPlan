from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for
from app import mail

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def confirm_verification_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email

def send_verification_email(user):
    token = generate_verification_token(user.email)
    link = url_for('main.confirm_email', token=token, _external=True)
    msg = Message('Email Verification',
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    msg.body = f'Please click the link to verify your email address: {link}'
    mail.send(msg)
