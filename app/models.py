from app import db, login_manager
from flask_login import UserMixin

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
    breed = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    picture = db.Column(db.String(100), nullable=False)  # storing filename
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    histories = db.relationship('PetHistory', backref='pet', lazy=True)
    appointments = db.relationship('VetAppointment', backref='pet', lazy=True)

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

