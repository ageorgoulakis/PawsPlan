from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.forms import RegistrationForm, LoginForm
from app.models import User
from app.utils import send_verification_email, confirm_verification_token

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
    return render_template('dashboard.html', title='Dashboard')

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
        db.session.delete(user)
    db.session.commit()
    return "All users have been deleted.", 200
