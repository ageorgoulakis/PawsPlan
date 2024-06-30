from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, FileField, TextAreaField, DateField, TimeField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class AddPetForm(FlaskForm):
    name = StringField('Pet Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    breed = StringField('Breed', validators=[DataRequired()])
    picture = FileField('Upload Picture', validators=[DataRequired()])
    submit = SubmitField('Save Pet')

class PetHistoryForm(FlaskForm):
    event_type = SelectField('Event Type', choices=[('Vet Appointment', 'Vet Appointment'), ('Vaccine', 'Vaccine'), ('Other', 'Other')], validators=[DataRequired()])
    event_date = DateField('Event Date', format='%Y-%m-%d', validators=[DataRequired()])
    event_time = TimeField('Event Time', format='%H:%M', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Save')

class VetAppointmentForm(FlaskForm):
    pet = SelectField('Select Pet', validators=[DataRequired()], coerce=int)
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Time', format='%H:%M', validators=[DataRequired()])
    vet_name = StringField('Veterinarian Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Save')

