# app/__init__.py
from flask import Flask, jsonify
import os
import logging
from config import DevelopmentConfig # Or dynamically choose config

def create_app(config_object=DevelopmentConfig):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # Already exists or other error

    # Ensure UPLOAD_FOLDER exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        app.logger.info(f"Created UPLOAD_FOLDER at {app.config['UPLOAD_FOLDER']}")


    # Initialize extensions and register blueprints
    from .core import database
    database.init_app(app)

    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .files.routes import files_bp
    app.register_blueprint(files_bp) # No prefix, or prefix with /api

    # Basic route for health check or welcome
    @app.route('/')
    def hello_world():
        return jsonify({"message": "Welcome to the Simple Object Storage API!"}), 200

    # Configure logging
    if not app.debug:
        # In production, add log handlers, e.g., to a file
        file_handler = logging.FileHandler(os.path.join(app.instance_path, 'app.log'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')


    return app