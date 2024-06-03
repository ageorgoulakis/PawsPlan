import requests
from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for

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
    response = requests.post(
        f"https://api.mailgun.net/v3/{current_app.config['MAILGUN_DOMAIN']}/messages",
        auth=("api", current_app.config['MAILGUN_API_KEY']),
        data={"from": f"PawsPlan <postmaster@{current_app.config['MAILGUN_DOMAIN']}>",
              "to": [user.email],
              "subject": "Email Verification",
              "text": f'Please click the link to verify your email address: {link}',
              "html": f'<p>Please click the link to verify your email address: <a href="{link}">Verify Email</a></p>'}
    )
    print(response.status_code)
    print(response.json())
    return response
