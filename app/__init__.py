import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
import os

# Set up logging for APScheduler
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'
migrate = Migrate()
mail = Mail()
scheduler = BackgroundScheduler()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Initialize Flask extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Ensure the pet pictures directory exists
    from app.utils import ensure_directory_exists
    ensure_directory_exists(os.path.join(app.root_path, 'static/pet_pics'))

    # Register the main blueprint
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Start the scheduler if it's not already running
    if not scheduler.running:
        scheduler.start()
    
    # Remove existing job with the same ID if it exists
    existing_job = scheduler.get_job('check_vaccine_due_dates')
    if existing_job:
        scheduler.remove_job('check_vaccine_due_dates')
    
    # Schedule the task to check vaccine due dates every minute
    from app.tasks import check_vaccine_due_dates
    scheduler.add_job(id='check_vaccine_due_dates', func=check_vaccine_due_dates, trigger='interval', minutes=1)

    return app

app = create_app()
