# app/models.py
import sqlite3
import bcrypt
import uuid
import datetime
from flask import current_app, g
from .core.database import get_db # Assuming get_db is in core.database

# --- User Model Functions ---
def get_user_by_username(username: str) -> sqlite3.Row | None:
    """Fetches a user by their username."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    return cursor.fetchone()

def create_user(username: str, password: str) -> int:
    """Creates a new user and returns their ID."""
    db = get_db()
    cursor = db.cursor()
    hashed_password_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    hashed_password_str = hashed_password_bytes.decode('utf-8')
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                       (username, hashed_password_str))
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError: # e.g., username already exists
        db.rollback()
        raise # Or handle more gracefully
    except sqlite3.Error as e:
        db.rollback()
        current_app.logger.error(f"Database error creating user {username}: {e}")
        raise

# --- File Model Functions ---
def create_file_record(user_id: int, filename: str, filepath: str, filesize: int, permission: str = 'private') -> dict:
    """Creates a new file record in the database."""
    db = get_db()
    cursor = db.cursor()
    download_link_id = str(uuid.uuid4())
    try:
        cursor.execute("""
            INSERT INTO files (user_id, filename, filepath, filesize, download_link_id, permission)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, filename, filepath, filesize, download_link_id, permission))
        db.commit()
        file_id = cursor.lastrowid
        return {
            "id": file_id,
            "filename": filename,
            "filepath": filepath,
            "filesize": filesize,
            "download_link_id": download_link_id,
            "permission": permission,
            "user_id": user_id
        }
    except sqlite3.Error as e:
        db.rollback()
        current_app.logger.error(f"Database error creating file record for user {user_id}, filename {filename}: {e}")
        raise

def get_file_by_id(file_id: int) -> sqlite3.Row | None:
    """Fetches a file by its ID."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT f.id, f.filename, f.filepath, f.filesize, f.upload_time, 
               f.permission, f.download_link_id, f.access_password_hash, 
               f.user_id, u.username as owner_username
        FROM files f
        JOIN users u ON f.user_id = u.id
        WHERE f.id = ?
    """, (file_id,))
    return cursor.fetchone()

def get_file_by_download_link(link_id: str) -> sqlite3.Row | None:
    """Fetches a file by its download link ID."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, filename, filepath, permission, access_password_hash, user_id
        FROM files WHERE download_link_id = ?
    """, (link_id,))
    return cursor.fetchone()

def get_files_by_user_id(user_id: int) -> list[sqlite3.Row]:
    """Fetches all files for a given user ID."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, filename, filesize, upload_time, permission, download_link_id
        FROM files
        WHERE user_id = ?
        ORDER BY upload_time DESC
    """, (user_id,))
    return cursor.fetchall()

def update_file_permission(file_id: int, user_id: int, new_permission: str, new_access_password_hash: str | None) -> bool:
    """Updates the permission and password hash for a file owned by the user."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            UPDATE files SET permission = ?, access_password_hash = ? 
            WHERE id = ? AND user_id = ?
        """, (new_permission, new_access_password_hash, file_id, user_id))
        db.commit()
        return cursor.rowcount > 0 # Returns True if a row was updated
    except sqlite3.Error as e:
        db.rollback()
        current_app.logger.error(f"Database error updating permission for file {file_id}: {e}")
        raise

def delete_file_record(file_id: int, user_id: int) -> bool:
    """Deletes a file record from the database owned by the user."""
    db = get_db()
    cursor = db.cursor()
    try:
        # Ensure to also delete the physical file in the route handler or a service layer
        cursor.execute("DELETE FROM files WHERE id = ? AND user_id = ?", (file_id, user_id))
        db.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        db.rollback()
        current_app.logger.error(f"Database error deleting file record {file_id}: {e}")
        raise

# Add other data-related functions as needed...