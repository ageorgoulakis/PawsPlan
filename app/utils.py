import os
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for
from app import mail, db
from app.models import User, VetAppointment

def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

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

def send_appointment_email(user, appointment):
    msg = Message('Appointment Created',
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    msg.body = f'Your appointment for {appointment.pet.name} has been created.\n\n' \
               f'Date: {appointment.date.strftime("%A, %B %d, %Y")}\n' \
               f'Time: {appointment.time.strftime("%I:%M %p")}\n' \
               f'Veterinarian: {appointment.vet_name}\n' \
               f'Description: {appointment.description}'
    mail.send(msg)

def send_reminder_email(user_id, appointment_id):
    from app import create_app  # Import inside the function to avoid circular imports
    app = create_app()
    with app.app_context():
        user = User.query.get(user_id)
        appointment = VetAppointment.query.get(appointment_id)
        print(f"Sending reminder to {user.email} for appointment {appointment_id}")  # Add logging
        msg = Message('Appointment Reminder',
                      sender=current_app.config['MAIL_DEFAULT_SENDER'],
                      recipients=[user.email])
        msg.body = f'Reminder: Your appointment for {appointment.pet.name} is scheduled for tomorrow.\n\n' \
                   f'Date: {appointment.date.strftime("%A, %B %d, %Y")}\n' \
                   f'Time: {appointment.time.strftime("%I:%M %p")}\n' \
                   f'Veterinarian: {appointment.vet_name}\n' \
                   f'Description: {appointment.description}'
        mail.send(msg)

