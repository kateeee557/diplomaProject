from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import config as config_module

# Initialize extensions
db = SQLAlchemy()
migrate = None

def create_app(config_name='default'):
    global migrate

    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config_module.config[config_name])

    # Ensure upload folder exists
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # Initialize database
    db.init_app(app)
    migrate = Migrate(app, db)

    # Import models here to avoid circular imports
    from models.integrity_violation import IntegrityViolation

    # Context processor for violation count
    @app.context_processor
    def inject_violation_count():
        # Only inject violation count if a user is logged in and is a teacher
        if 'user_id' in session and session.get('role') == 'teacher':
            with app.app_context():
                violation_count = IntegrityViolation.query.filter(
                    IntegrityViolation.reviewed == False
                ).count()
                return dict(violation_count=violation_count)
        return dict(violation_count=0)

    # Import and register blueprints
    from controllers.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from controllers.student import student as student_blueprint
    app.register_blueprint(student_blueprint, url_prefix='/student')

    from controllers.teacher import teacher as teacher_blueprint
    app.register_blueprint(teacher_blueprint, url_prefix='/teacher')

    from controllers.blockchain import blockchain as blockchain_blueprint
    app.register_blueprint(blockchain_blueprint, url_prefix='/blockchain')

    # Import error handlers
    from controllers.errors import errors as errors_blueprint
    app.register_blueprint(errors_blueprint)

    return app