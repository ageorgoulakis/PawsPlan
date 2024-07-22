from flask import render_template, url_for, flash, redirect, request, Blueprint, current_app, abort, send_file
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt, scheduler
from app.forms import RegistrationForm, LoginForm, AddPetForm, PetHistoryForm, VetAppointmentForm, VaccineTrackingForm, EditVaccineForm, FeedingScheduleForm, ExpenseForm
from app.models import User, Pet, PetHistory, VetAppointment, VaccineRecord, FeedingSchedule, Expense
from app.utils import send_verification_email, confirm_verification_token, send_appointment_email, send_reminder_email
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta, date
from weasyprint import HTML
import io

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

    # Fetch the closest upcoming vaccination record
    closest_vaccine_record = VaccineRecord.query.join(Pet).filter(
        Pet.user_id == current_user.id,
        VaccineRecord.next_due_date >= date.today()
    ).order_by(VaccineRecord.next_due_date).first()

    # Calculate the total expenses
    total_expenses = db.session.query(db.func.sum(Expense.amount)).join(Pet).filter(Pet.user_id == current_user.id).scalar() or 0.0

    return render_template(
        'dashboard.html', 
        title='Dashboard', 
        pets=pets, 
        appointments=appointments,
        closest_vaccine_record=closest_vaccine_record,
        total_expenses=total_expenses
    )


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
        # Delete feeding schedules associated with the user's pets
        pets = Pet.query.filter_by(user_id=user.id).all()
        for pet in pets:
            FeedingSchedule.query.filter_by(pet_id=pet.id).delete(synchronize_session=False)
            Expense.query.filter_by(pet_id=pet.id).delete(synchronize_session=False)
            VaccineRecord.query.filter_by(pet_id=pet.id).delete(synchronize_session=False)
            PetHistory.query.filter_by(pet_id=pet.id).delete(synchronize_session=False)
            VetAppointment.query.filter_by(pet_id=pet.id).delete(synchronize_session=False)
            db.session.delete(pet)
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
        pet = Pet(
            name=form.name.data, 
            age=form.age.data, 
            breed=form.breed.data, 
            gender=form.gender.data,  # Handle the gender field
            picture=picture_file, 
            user_id=current_user.id
        )
        db.session.add(pet)
        db.session.commit()
        flash('Your pet has been added!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_pet.html', title='Add Pet', form=form)

# Route for editing a pet
@bp.route("/edit_pet/<int:pet_id>", methods=['GET', 'POST'])
@login_required
def edit_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    if pet.owner != current_user:
        flash('You do not have permission to edit this pet.', 'danger')
        return redirect(url_for('main.manage_pets'))
    
    form = AddPetForm(obj=pet)
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = secure_filename(form.picture.data.filename)
            picture_path = os.path.join(current_app.root_path, 'static/pet_pics', picture_file)
            form.picture.data.save(picture_path)  # Save the file to the static/pet_pics directory
            pet.picture = picture_file

        pet.name = form.name.data
        pet.age = form.age.data
        pet.breed = form.breed.data
        pet.gender = form.gender.data

        db.session.commit()
        flash('Your pet has been updated!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('edit_pet.html', title='Edit Pet', form=form)


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
    # Delete vaccine records associated with the pet
    VaccineRecord.query.filter_by(pet_id=pet.id).delete(synchronize_session=False)
    # Delete feeding schedules associated with the pet
    FeedingSchedule.query.filter_by(pet_id=pet.id).delete(synchronize_session=False)
    # Delete expenses associated with the pet
    Expense.query.filter_by(pet_id=pet.id).delete(synchronize_session=False)

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

@bp.route('/vaccine_tracking', methods=['GET', 'POST'])
@login_required
def vaccine_tracking():
    form = VaccineTrackingForm()
    pets = Pet.query.filter_by(user_id=current_user.id).all()

    pet_id = request.args.get('pet')
    
    records_query = VaccineRecord.query.join(Pet).filter(Pet.user_id == current_user.id)

    if pet_id:
        records_query = records_query.filter(VaccineRecord.pet_id == pet_id)

    records = records_query.all()

    if form.validate_on_submit():
        vaccine_record = VaccineRecord(
            pet_id=form.pet.data,
            vaccine_type=form.vaccine_type.data,
            date_administered=form.date_administered.data,
            next_due_date=form.next_due_date.data,
            notification_sent=False  # Set default to False
        )
        db.session.add(vaccine_record)
        db.session.commit()
        flash('Vaccine record added successfully!', 'success')
        return redirect(url_for('main.vaccine_tracking'))

    return render_template('vaccine_tracking.html', form=form, records=records, pets=pets)


@bp.route("/edit_vaccine/<int:vaccine_id>", methods=['GET', 'POST'])
@login_required
def edit_vaccine(vaccine_id):
    vaccine_record = VaccineRecord.query.get_or_404(vaccine_id)
    form = EditVaccineForm()
    if form.validate_on_submit():
        vaccine_record.vaccine_type = form.vaccine_type.data if form.vaccine_type.data != 'other' else form.other_vaccine.data
        vaccine_record.date_administered = form.date_administered.data
        vaccine_record.next_due_date = form.next_due_date.data
        db.session.commit()
        flash('Vaccine record updated successfully.', 'success')
        return redirect(url_for('main.vaccine_tracking'))
    elif request.method == 'GET':
        form.vaccine_type.data = vaccine_record.vaccine_type
        form.other_vaccine.data = vaccine_record.vaccine_type if vaccine_record.vaccine_type not in form.vaccine_type.choices else ''
        form.date_administered.data = vaccine_record.date_administered
        form.next_due_date.data = vaccine_record.next_due_date
    return render_template('edit_vaccine.html', form=form)

@bp.route("/delete_vaccine/<int:vaccine_id>", methods=['POST'])
@login_required
def delete_vaccine(vaccine_id):
    vaccine_record = VaccineRecord.query.get_or_404(vaccine_id)
    db.session.delete(vaccine_record)
    db.session.commit()
    flash('Vaccine record deleted successfully.', 'success')
    return redirect(url_for('main.vaccine_tracking'))

# Feeding Schedule Routes
@bp.route('/feeding_schedule', methods=['GET', 'POST'])
@login_required
def feeding_schedule():
    form = FeedingScheduleForm()
    if form.validate_on_submit():
        feeding_times = [form.feeding_time_1.data, form.feeding_time_2.data, form.feeding_time_3.data, form.feeding_time_4.data, form.feeding_time_5.data]
        feeding_times = [time for time in feeding_times if time]
        feeding_schedule = FeedingSchedule(
            pet_id=form.pet.data,
            food_type=form.food_type.data,
            feedings_per_day=form.feedings_per_day.data,
            food_amount=form.food_amount.data,
            feeding_times=feeding_times
        )
        db.session.add(feeding_schedule)
        db.session.commit()
        flash('Feeding schedule added successfully!', 'success')
        return redirect(url_for('main.feeding_schedule'))

    feedings = FeedingSchedule.query.join(Pet).filter(Pet.user_id == current_user.id).all()
    return render_template('feeding_schedule.html', form=form, feedings=feedings)

@bp.route('/edit_feeding_schedule/<int:feeding_id>', methods=['GET', 'POST'])
@login_required
def edit_feeding_schedule(feeding_id):
    feeding_schedule = FeedingSchedule.query.get_or_404(feeding_id)
    form = FeedingScheduleForm()
    if form.validate_on_submit():
        feeding_schedule.pet_id = form.pet.data
        feeding_schedule.food_type = form.food_type.data
        feeding_schedule.feedings_per_day = form.feedings_per_day.data
        feeding_schedule.food_amount = form.food_amount.data
        feeding_times = [form.feeding_time_1.data, form.feeding_time_2.data, form.feeding_time_3.data, form.feeding_time_4.data, form.feeding_time_5.data]
        feeding_times = [time for time in feeding_times if time]
        feeding_schedule.feeding_times = feeding_times
        db.session.commit()
        flash('Feeding schedule updated successfully.', 'success')
        return redirect(url_for('main.feeding_schedule'))
    elif request.method == 'GET':
        form.pet.data = feeding_schedule.pet_id
        form.food_type.data = feeding_schedule.food_type
        form.feedings_per_day.data = feeding_schedule.feedings_per_day
        form.food_amount.data = feeding_schedule.food_amount
        feeding_times = feeding_schedule.feeding_times
        if len(feeding_times) > 0:
            form.feeding_time_1.data = feeding_times[0]
        if len(feeding_times) > 1:
            form.feeding_time_2.data = feeding_times[1]
        if len(feeding_times) > 2:
            form.feeding_time_3.data = feeding_times[2]
        if len(feeding_times) > 3:
            form.feeding_time_4.data = feeding_times[3]
        if len(feeding_times) > 4:
            form.feeding_time_5.data = feeding_times[4]
    return render_template('edit_feeding_schedule.html', form=form, feeding_id=feeding_id)

@bp.route('/delete_feeding_schedule/<int:feeding_id>', methods=['POST'])
@login_required
def delete_feeding_schedule(feeding_id):
    feeding_schedule = FeedingSchedule.query.get_or_404(feeding_id)
    db.session.delete(feeding_schedule)
    db.session.commit()
    flash('Feeding schedule deleted successfully.', 'success')
    return redirect(url_for('main.feeding_schedule'))

@bp.route('/feeding_schedule_pdf')
@login_required
def feeding_schedule_pdf():
    feedings = FeedingSchedule.query.join(Pet).filter(Pet.user_id == current_user.id).all()

    # Render the HTML template with feeding schedule data
    html = render_template('feeding_schedule_pdf.html', feedings=feedings)

    # Convert the HTML to a PDF
    pdf = HTML(string=html).write_pdf()

    # Send the PDF as a file download
    return send_file(
        io.BytesIO(pdf),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='feeding_schedule.pdf'
    )

@bp.route('/expense_management', methods=['GET', 'POST'])
@login_required
def expense_management():
    form = ExpenseForm()
    pets = Pet.query.filter_by(user_id=current_user.id).all()
    expense_types = ['Appointments','Vaccination','Food', 'Vet', 'Toy and Entertainment','Training','Insurance','Pet Sitting','Travel','Registration','Accessories','Miscellaneous Supplies','Dietary Supplements','Subscriptions','Events','Other']

    if form.validate_on_submit():
        expense = Expense(
            pet_id=form.pet.data,
            expense_type=form.expense_type.data,
            amount=form.amount.data,
            date=form.date.data
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('main.expense_management'))

    sort_pet = request.args.get('sort_pet')
    sort_expense_type = request.args.get('sort_expense_type')
    sort_amount = request.args.get('sort_amount')
    sort_date = request.args.get('sort_date')

    expenses_query = Expense.query.join(Pet).filter(Pet.user_id == current_user.id)

    if sort_pet:
        expenses_query = expenses_query.filter(Expense.pet_id == sort_pet)
    if sort_expense_type:
        expenses_query = expenses_query.filter(Expense.expense_type == sort_expense_type)
    if sort_amount:
        if sort_amount == 'asc':
            expenses_query = expenses_query.order_by(Expense.amount.asc())
        else:
            expenses_query = expenses_query.order_by(Expense.amount.desc())
    if sort_date:
        if sort_date == 'asc':
            expenses_query = expenses_query.order_by(Expense.date.asc())
        else:
            expenses_query = expenses_query.order_by(Expense.date.desc())

    expenses = expenses_query.all()
    total_expenses = sum(expense.amount for expense in expenses)

    # Calculate the summary of expenses by type
    expense_summary = {expense_type: 0 for expense_type in expense_types}
    for expense in expenses:
        if expense.expense_type in expense_summary:
            expense_summary[expense.expense_type] += expense.amount
        else:
            expense_summary['Other'] += expense.amount

    return render_template(
        'expense_management.html', 
        form=form, 
        expenses=expenses, 
        pets=pets, 
        expense_types=expense_types, 
        total_expenses=total_expenses,
        expense_summary=expense_summary,
        sort_pet=sort_pet,
        sort_expense_type=sort_expense_type,
        sort_amount=sort_amount,
        sort_date=sort_date
    )




@bp.route("/expense_management/edit/<int:expense_id>", methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    form = ExpenseForm()

    if form.validate_on_submit():
        expense.pet_id = form.pet.data
        expense.expense_type = form.expense_type.data
        expense.amount = form.amount.data
        expense.date = form.date.data
        db.session.commit()
        flash('Expense has been updated!', 'success')
        return redirect(url_for('main.expense_management'))

    elif request.method == 'GET':
        form.pet.data = expense.pet_id
        form.expense_type.data = expense.expense_type
        form.amount.data = expense.amount
        form.date.data = expense.date

    return render_template('edit_expense.html', title='Edit Expense', form=form, expense=expense)

@bp.route("/expense_management/delete/<int:expense_id>", methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense has been deleted!', 'success')
    return redirect(url_for('main.expense_management'))

