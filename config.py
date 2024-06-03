import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///pawsplan.db'
    MAILGUN_API_KEY = 'bf14a30b12192a1023e9ba4bd0d5958c-a4da91cf-b2409e7f'
    MAILGUN_DOMAIN = 'sandboxd9a730d3dd804451878b6d91b0729d31.mailgun.org'
    SECURITY_PASSWORD_SALT = 'your_security_password_salt'
