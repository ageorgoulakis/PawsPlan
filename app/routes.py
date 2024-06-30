from flask import render_template, url_for, flash, redirect, request, Blueprint, current_app, abort
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt, scheduler
from app.forms import RegistrationForm, LoginForm, AddPetForm, PetHistoryForm, VetAppointmentForm
from app.models import User, Pet, PetHistory, VetAppointment
from app.utils import send_verification_email, confirm_verification_token, send_appointment_email, send_reminder_email
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta

bp = Blueprint('main', __name__)

@bp.route("/")
@bp.route("/home")
def home():
    return render_template('index.html')

@bp.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        send_verification_email(user)
        flash('An email has been sent to verify your account.', 'info')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if user.is_verified:
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
            else:
                flash('Your account is not verified. Please check your email.', 'warning')
                return redirect(url_for('main.login'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@bp.route("/dashboard")
@login_required
def dashboard():
    # Check for due appointments and move them to history
    now = datetime.now()
    due_appointments = VetAppointment.query.filter(
        (VetAppointment.date < now.date()) | 
        ((VetAppointment.date == now.date()) & (VetAppointment.time <= now.time()))
    ).all()
    for appointment in due_appointments:
        history_event = PetHistory(
            event_type='Vet Appointment',
            event_date=appointment.date,
            event_time=appointment.time,
            description=appointment.description,
            pet_id=appointment.pet_id
        )
        db.session.add(history_event)
        db.session.delete(appointment)
    db.session.commit()

    # Fetch the updated list of pets and appointments
    pets = Pet.query.filter_by(user_id=current_user.id).all()
    appointments = VetAppointment.query.join(Pet).filter(Pet.user_id == current_user.id).all()
    return render_template('dashboard.html', title='Dashboard', pets=pets, appointments=appointments)

@bp.route("/confirm_email/<token>")
def confirm_email(token):
    email = confirm_verification_token(token)
    if email:
        user = User.query.filter_by(email=email).first_or_404()
        if user.is_verified:
            flash('Account already verified. Please log in.', 'success')
        else:
            user.is_verified = True
            db.session.commit()
            flash('Your account has been verified!', 'success')
    else:
        flash('The confirmation link is invalid or has expired.', 'danger')
    return redirect(url_for('main.login'))

@bp.route("/delete_all_users")
def delete_all_users():
    users = User.query.all()
    for user in users:
        # Delete pets associated with the user
        pets = Pet.query.filter_by(user_id=user.id).all()
        for pet in pets:
            # Delete history associated with the pet
            PetHistory.query.filter_by(pet_id=pet.id).delete(synchronize_session=False)
            # Delete appointments associated with the pet
            VetAppointment.query.filter_by(pet_id=pet.id).delete(synchronize_session=False)
            db.session.delete(pet)
        # Delete the user
        db.session.delete(user)
    db.session.commit()
    return "All users, their pets, and their histories have been deleted.", 200

# Route for managing pets
@bp.route("/manage_pets")
@login_required
def manage_pets():
    pets = Pet.query.filter_by(user_id=current_user.id).all()
    return render_template('manage_pets.html', title='Pet Management', pets=pets)

# Route for adding a pet
@bp.route("/add_pet", methods=['GET', 'POST'])
@login_required
def add_pet():
    form = AddPetForm()
    if form.validate_on_submit():
        picture_file = secure_filename(form.picture.data.filename)
        picture_path = os.path.join(current_app.root_path, 'static/pet_pics', picture_file)
        form.picture.data.save(picture_path)  # Save the file to the static/pet_pics directory
        pet = Pet(name=form.name.data, age=form.age.data, breed=form.breed.data, picture=picture_file, user_id=current_user.id)
        db.session.add(pet)
        db.session.commit()
        flash('Your pet has been added!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_pet.html', title='Add Pet', form=form)

# Route to edit a pet
@bp.route("/edit_pet/<int:pet_id>", methods=['GET', 'POST'])
@login_required
def edit_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    if pet.owner != current_user:
        flash('You do not have permission to edit this pet.', 'danger')
        return redirect(url_for('main.manage_pets'))
    form = AddPetForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = secure_filename(form.picture.data.filename)
            picture_path = os.path.join(current_app.root_path, 'static/pet_pics', picture_file)
            form.picture.data.save(picture_path)
            pet.picture = picture_file
        pet.name = form.name.data
        pet.age = form.age.data
        pet.breed = form.breed.data
        db.session.commit()
        flash('Your pet has been updated!', 'success')
        return redirect(url_for('main.manage_pets'))
    elif request.method == 'GET':
        form.name.data = pet.name
        form.age.data = pet.age
        form.breed.data = pet.breed
    return render_template('edit_pet.html', title='Edit Pet', form=form, pet=pet)

# Route to delete a pet
@bp.route("/delete_pet/<int:pet_id>", methods=['POST'])
@login_required
def delete_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    if pet.owner != current_user:
        flash('You do not have permission to delete this pet.', 'danger')
        return redirect(url_for('main.manage_pets'))

    # Delete all history associated with the pet
    PetHistory.query.filter_by(pet_id=pet.id).delete(synchronize_session=False)
    # Delete all appointments associated with the pet
    VetAppointment.query.filter_by(pet_id=pet.id).delete(synchronize_session=False)

    # Now delete the pet
    db.session.delete(pet)
    db.session.commit()
    flash('The pet and its history have been deleted!', 'success')
    return redirect(url_for('main.manage_pets'))

# Route for viewing and adding pet history
@bp.route("/pet/<int:pet_id>/history", methods=['GET', 'POST'])
@login_required
def pet_history(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    if pet.owner != current_user:
        abort(403)

    form = PetHistoryForm()
    if form.validate_on_submit():
        history_event = PetHistory(
            event_type=form.event_type.data,
            event_date=form.event_date.data,
            event_time=form.event_time.data,
            description=form.description.data,
            pet_id=pet.id
        )
        db.session.add(history_event)
        db.session.commit()
        flash('History event added!', 'success')
        return redirect(url_for('main.pet_history', pet_id=pet.id))
    
    history_events = PetHistory.query.filter_by(pet_id=pet.id).all()
    # Format date and time
    for event in history_events:
        event.formatted_date = event.event_date.strftime('%A, %B %d, %Y')
        event.formatted_time = event.event_time.strftime('%I:%M %p')
    
    return render_template('history.html', pet=pet, form=form, history_events=history_events)

# New route for editing pet history
@bp.route("/pet/<int:pet_id>/history/<int:history_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_pet_history(pet_id, history_id):
    pet = Pet.query.get_or_404(pet_id)
    history_event = PetHistory.query.get_or_404(history_id)
    if pet.owner != current_user or history_event.pet_id != pet.id:
        abort(403)
    
    form = PetHistoryForm()
    if form.validate_on_submit():
        history_event.event_type = form.event_type.data
        history_event.event_date = form.event_date.data
        history_event.event_time = form.event_time.data
        history_event.description = form.description.data
        db.session.commit()
        flash('History event updated!', 'success')
        return redirect(url_for('main.pet_history', pet_id=pet.id))
    elif request.method == 'GET':
        form.event_type.data = history_event.event_type
        form.event_date.data = history_event.event_date
        form.event_time.data = history_event.event_time
        form.description.data = history_event.description
    
    return render_template('edit_history.html', pet=pet, form=form, history_event=history_event)

@bp.route("/history_page", methods=['GET', 'POST'])
@login_required
def history_page():
    pets = Pet.query.filter_by(user_id=current_user.id).all()
    selected_pet = None
    history_events = []

    if request.method == 'POST' or (request.method == 'GET' and request.args.get('pet_id')):
        pet_id = request.form.get('pet') if request.method == 'POST' else request.args.get('pet_id')
        if pet_id:
            selected_pet = Pet.query.get(int(pet_id))
            if selected_pet and selected_pet.owner == current_user:
                history_events = PetHistory.query.filter_by(pet_id=selected_pet.id).all()
                # Format date and time
                for event in history_events:
                    event.formatted_date = event.event_date.strftime('%A, %B %d, %Y')
                    event.formatted_time = event.event_time.strftime('%I:%M %p')

    return render_template('history_page.html', pets=pets, selected_pet=selected_pet, history_events=history_events)

@bp.route("/appointments", methods=['GET', 'POST'])
@login_required
def appointments():
    form = VetAppointmentForm()
    form.pet.choices = [(pet.id, pet.name) for pet in Pet.query.filter_by(user_id=current_user.id).all()]
    if form.validate_on_submit():
        appointment = VetAppointment(
            pet_id=form.pet.data,
            date=form.date.data,
            time=form.time.data,
            vet_name=form.vet_name.data,
            description=form.description.data
        )
        db.session.add(appointment)
        db.session.commit()
        send_appointment_email(current_user, appointment)

        # Schedule reminder email 24 hours before the appointment
        reminder_time = datetime.combine(appointment.date, appointment.time) - timedelta(hours=24)
        print(f"Scheduling reminder for {reminder_time}")  # Add logging
        scheduler.add_job(
            func=send_reminder_email,
            args=[current_user.id, appointment.id],
            trigger='date',
            run_date=reminder_time,
            id=f'reminder_{appointment.id}',
            replace_existing=True
        )

        flash('Appointment saved!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('appointments.html', form=form)

