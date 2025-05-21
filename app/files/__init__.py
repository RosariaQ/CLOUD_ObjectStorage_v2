# app/files/__init__.py
from flask import Blueprint

files_bp = Blueprint('files', __name__)

from . import routes # Import routes