import datetime
from app.utils import send_notification_email

def check_vaccine_due_dates():
    from app import db, create_app
    from app.models import User, VaccineRecord

    app = create_app()
    with app.app_context():
        today = datetime.date.today()
        reminder_date = today + datetime.timedelta(days=14)
        
        # Find all vaccine records with a next due date within the next 14 days and notification not sent
        due_vaccines = VaccineRecord.query.filter(
            VaccineRecord.next_due_date <= reminder_date,
            VaccineRecord.notification_sent == False  # Add this condition
        ).all()

        for record in due_vaccines:
            user = User.query.get(record.pet.user_id)
            if user:
                print(f"Sending reminder to {user.email} for vaccine {record.vaccine_type}")  # Add logging
                send_notification_email(user, record)
                # Mark the notification as sent
                record.notification_sent = True
                db.session.commit()