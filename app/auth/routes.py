# app/auth/routes.py
from flask import Blueprint, request, jsonify, current_app, g
import bcrypt
import jwt
import datetime
import sqlite3
from app.core.database import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "Username and password are required"}), 400
    username = data['username']
    password = data['password']
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return jsonify({"message": "Username already exists"}), 409
        
        hashed_password_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_password_str = hashed_password_bytes.decode('utf-8') # Store as string

        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                       (username, hashed_password_str))
        db.commit()
    except sqlite3.Error as e:
        db.rollback()
        current_app.logger.error(f"Database error during registration for {username}: {e}")
        return jsonify({"message": "Database error registering user"}), 500
    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "Username and password are required"}), 400
    username = data['username']
    password = data['password']
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
    except sqlite3.Error as e:
        current_app.logger.error(f"Database error fetching user {username}: {e}")
        return jsonify({"message": "Database error during login"}), 500

    if not user:
        return jsonify({"message": "Invalid credentials"}), 401

    # Ensure stored hash is bytes for bcrypt.checkpw
    stored_password_hash_bytes = user['password_hash'].encode('utf-8')

    if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash_bytes):
        token_payload = {
            'user_id': user['id'],
            'username': user['username'],
            'exp': datetime.datetime.utcnow() + current_app.config['JWT_EXPIRATION_DELTA']
        }
        try:
            token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')
            return jsonify({"message": "Login successful", "token": token}), 200
        except Exception as e:
            current_app.logger.error(f"Error generating token for {username}: {e}")
            return jsonify({"message": "Error generating token"}), 500
    else:
        return jsonify({"message": "Invalid credentials"}), 401