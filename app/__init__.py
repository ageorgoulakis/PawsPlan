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
    
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Ensure the pet pictures directory exists
    from app.utils import ensure_directory_exists
    ensure_directory_exists(os.path.join(app.root_path, 'static/pet_pics'))

    from app import routes
    app.register_blueprint(routes.bp)

    if not scheduler.running:
        scheduler.start()

    return app

app = create_app()
