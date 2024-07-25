from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, FileField, TextAreaField, DateField, TimeField, SelectField, DecimalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User, Pet, VaccineRecord

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
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
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

class EditPetForm(FlaskForm):
    name = StringField('Pet Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    breed = StringField('Breed', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    picture = FileField('Upload Picture')

class VetAppointmentForm(FlaskForm):
    pet = SelectField('Select Pet', validators=[DataRequired()], coerce=int)
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Time', format='%H:%M', validators=[DataRequired()])
    vet_name = StringField('Veterinarian Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Save')

class VaccineTrackingForm(FlaskForm):
    pet = SelectField('Choose Pet', coerce=int, validators=[DataRequired()])
    vaccine_type = SelectField('Choose Vaccine Type', choices=[
        ('rabies', 'Rabies'),
        ('distemper', 'Distemper'),
        ('parvovirus', 'Parvovirus'),
        ('hepatitis', 'Hepatitis'),
        ('leptospirosis', 'Leptospirosis'),
        ('bordetella', 'Bordetella'),
        ('lyme', 'Lyme'),
        ('canine_influenza', 'Canine Influenza'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    other_vaccine = StringField('Other Vaccine')
    date_administered = DateField('Date Administered', validators=[DataRequired()])
    next_due_date = DateField('Next Due Date', validators=[DataRequired()])
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(VaccineTrackingForm, self).__init__(*args, **kwargs)
        self.pet.choices = [(pet.id, pet.name) for pet in Pet.query.all()]

class EditVaccineForm(FlaskForm):
    vaccine_type = SelectField('Choose Vaccine Type', choices=[
        ('rabies', 'Rabies'),
        ('distemper', 'Distemper'),
        ('parvovirus', 'Parvovirus'),
        ('hepatitis', 'Hepatitis'),
        ('leptospirosis', 'Leptospirosis'),
        ('bordetella', 'Bordetella'),
        ('lyme', 'Lyme'),
        ('canine_influenza', 'Canine Influenza'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    other_vaccine = StringField('Other Vaccine')
    date_administered = DateField('Date Administered', validators=[DataRequired()])
    next_due_date = DateField('Next Due Date', validators=[DataRequired()])
    submit = SubmitField('Update')

class FeedingScheduleForm(FlaskForm):
    pet = SelectField('Select Pet', coerce=int, validators=[DataRequired()])
    food_type = StringField('Type of Food', validators=[DataRequired()])
    feedings_per_day = IntegerField('Feedings per Day', validators=[DataRequired()])
    food_amount = SelectField('Food Amount (cups)', choices=[(str(i/4), f"{i/4} cups") for i in range(21)], validators=[DataRequired()])
    feeding_time_1 = TimeField('Feeding Time 1', format='%H:%M', validators=[Optional()])
    feeding_time_2 = TimeField('Feeding Time 2', format='%H:%M', validators=[Optional()])
    feeding_time_3 = TimeField('Feeding Time 3', format='%H:%M', validators=[Optional()])
    feeding_time_4 = TimeField('Feeding Time 4', format='%H:%M', validators=[Optional()])
    feeding_time_5 = TimeField('Feeding Time 5', format='%H:%M', validators=[Optional()])
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(FeedingScheduleForm, self).__init__(*args, **kwargs)
        self.pet.choices = [(pet.id, pet.name) for pet in Pet.query.all()]

class EditFeedingScheduleForm(FlaskForm):
    pet = SelectField('Select Pet', coerce=int, validators=[DataRequired()])
    food_type = StringField('Type of Food', validators=[DataRequired()])
    feedings_per_day = IntegerField('Feedings per Day', validators=[DataRequired()])
    feeding_time_1 = TimeField('Feeding Time 1', format='%H:%M', validators=[Optional()])
    feeding_time_2 = TimeField('Feeding Time 2', format='%H:%M', validators=[Optional()])
    feeding_time_3 = TimeField('Feeding Time 3', format='%H:%M', validators=[Optional()])
    feeding_time_4 = TimeField('Feeding Time 4', format='%H:%M', validators=[Optional()])
    feeding_time_5 = TimeField('Feeding Time 5', format='%H:%M', validators=[Optional()])
    submit = SubmitField('Update')

    def __init__(self, *args, **kwargs):
        super(EditFeedingScheduleForm, self).__init__(*args, **kwargs)
        self.pet.choices = [(pet.id, pet.name) for pet in Pet.query.all()]

class ExpenseForm(FlaskForm):
    pet = SelectField('Choose Pet', coerce=int, validators=[DataRequired()])
    expense_type = SelectField('Expense Type', choices=[
        ('Appointments', 'Appointments'),
        ('Vaccination', 'Vaccination'),
        ('Food', 'Food'),
        ('Medication', 'Medication'),
        ('Grooming', 'Grooming'),
        ('Toy and Entertainment', 'Toy and Entertainment'),
        ('Training', 'Training'),
        ('Insurance', 'Insurance'),
        ('Pet Sitting', 'Pet Sitting'),
        ('Travel', 'Travel'),
        ('Registration', 'Registration'),
        ('Accessories', 'Accessories'),
        ('Miscellaneous Supplies', 'Miscellaneous Supplies'),
        ('Dietary Supplements', 'Dietary Supplements'),
        ('Subscriptions', 'Subscriptions'),
        ('Events', 'Events'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired()])
    date = DateField('Date Paid', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(ExpenseForm, self).__init__(*args, **kwargs)
        self.pet.choices = [(pet.id, pet.name) for pet in Pet.query.all()]
