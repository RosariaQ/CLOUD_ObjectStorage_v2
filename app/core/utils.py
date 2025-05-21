# app/core/utils.py
from flask import current_app # Required to access app.config

def allowed_file(filename: str) -> bool:
    """
    Checks if the given filename has an allowed extension.
    Relies on 'ALLOWED_EXTENSIONS' in the Flask app configuration.
    """
    if not filename:
        return False
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# You can add other utility functions here as your application grows.
# For example:
# - Functions for generating unique identifiers (though uuid is often used directly)
# - Data sanitization helpers (beyond what secure_filename offers)
# - Complex string manipulation functions
# - etc.