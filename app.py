from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import config as config_module
config = config_module.config
import os

db = SQLAlchemy()

def create_app(config_name='default'):
    app = Flask(__name__)

    app.config.from_object(config[config_name])

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])



    db.init_app(app)

    # Register blueprints
    from controllers.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from controllers.student import student as student_blueprint
    app.register_blueprint(student_blueprint, url_prefix='/student')

    from controllers.teacher import teacher as teacher_blueprint
    app.register_blueprint(teacher_blueprint, url_prefix='/teacher')

    from controllers.blockchain import blockchain as blockchain_blueprint
    app.register_blueprint(blockchain_blueprint, url_prefix='/blockchain')

    # Register error handlers
    from controllers.errors import errors as errors_blueprint
    app.register_blueprint(errors_blueprint)

    return app