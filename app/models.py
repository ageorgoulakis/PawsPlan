from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    pets = db.relationship('Pet', backref='owner', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(6), nullable=False)
    breed = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    picture = db.Column(db.String(100), nullable=False)  # storing filename
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    histories = db.relationship('PetHistory', backref='pet', lazy=True)
    appointments = db.relationship('VetAppointment', backref='pet', lazy=True)
    vaccine_records = db.relationship('VaccineRecord', backref='pet', lazy=True)
    feeding_schedules = db.relationship('FeedingSchedule', backref='pet', lazy=True)

    def __repr__(self):
        return f"Pet('{self.name}', '{self.breed}', '{self.age}')"

class PetHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time, nullable=False)
    description = db.Column(db.Text, nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)

class VetAppointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    vet_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)

    def __repr__(self):
        return f"VetAppointment('{self.date}', '{self.time}', '{self.vet_name}')"

class VaccineRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vaccine_type = db.Column(db.String(100), nullable=False)
    date_administered = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date, nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    notification_sent = db.Column(db.Boolean, nullable=False, default=False)  # Add this line

    def __repr__(self):
        return f"VaccineRecord('{self.vaccine_type}', '{self.date_administered}', '{self.next_due_date}')"

class FeedingSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    food_type = db.Column(db.String(100), nullable=False)
    feedings_per_day = db.Column(db.Integer, nullable=False)
    food_amount = db.Column(db.String(5), nullable=False)
    feeding_times = db.Column(db.PickleType, nullable=False)  # Store times as a list of strings

    def __repr__(self):
        return f"FeedingSchedule('{self.pet_id}', '{self.food_type}', '{self.feedings_per_day}', '{self.feeding_times}')"

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    expense_type = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False)

    pet = db.relationship('Pet', backref='expenses', lazy=True)

    def __repr__(self):
        return f"Expense('{self.expense_type}', '{self.amount}', '{self.date}')"
