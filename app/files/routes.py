# app/files/routes.py
from flask import (
    Blueprint, request, jsonify, current_app, g, send_from_directory
)
import os
import uuid
import base64
import sqlite3
import bcrypt # For setting password permission
from werkzeug.utils import secure_filename
from app.core.database import get_db
from app.core.decorators import token_required
# from app.core.utils import allowed_file # If you create this file

files_bp = Blueprint('files', __name__) # No prefix here if registered with /api in __init__

def allowed_file(filename): # Kept here for simplicity, can move to utils.py
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def _send_file_helper(server_filepath, original_filename):
    """Helper function to send a file."""
    try:
        directory = os.path.dirname(server_filepath)
        filename_on_server = os.path.basename(server_filepath)
        return send_from_directory(directory, filename_on_server, as_attachment=True, download_name=original_filename)
    except FileNotFoundError:
        current_app.logger.error(f"File not found on server: {server_filepath}")
        return jsonify({"message": "File not found on server."}), 404
    except Exception as e:
        current_app.logger.error(f"Error sending file {original_filename} from {server_filepath}: {e}")
        return jsonify({"message": "Error sending file"}), 500

@files_bp.route('/upload', methods=['POST'])
@token_required
def upload_file_route():
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No file selected for uploading"}), 400

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        # Ensure unique internal filename does not exceed filesystem limits if original_filename is very long
        unique_internal_filename = f"{uuid.uuid4().hex}.{file_extension}" if file_extension else uuid.uuid4().hex
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        filepath_on_server = os.path.join(upload_folder, unique_internal_filename)

        try:
            file.save(filepath_on_server)
            filesize = os.path.getsize(filepath_on_server)
            download_link_id = str(uuid.uuid4())
            
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO files (user_id, filename, filepath, filesize, download_link_id, permission)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (g.current_user_id, original_filename, filepath_on_server, filesize, download_link_id, 'private'))
            db.commit()
            file_id = cursor.lastrowid
            
            current_app.logger.info(f"File {original_filename} (ID: {file_id}) uploaded by user {g.current_username} (ID: {g.current_user_id})")
            return jsonify({
                "message": "File uploaded successfully",
                "file_id": file_id,
                "filename": original_filename,
                "filesize_bytes": filesize,
                "download_link_id": download_link_id,
                "uploaded_by": g.current_username
            }), 201

        except Exception as e:
            current_app.logger.error(f"Failed to upload file {original_filename} by user {g.current_username}: {e}")
            # Attempt to clean up saved file if it exists and an error occurred
            if os.path.exists(filepath_on_server):
                try:
                    os.remove(filepath_on_server)
                except OSError as oe:
                    current_app.logger.error(f"Error deleting partially uploaded file {filepath_on_server}: {oe}")
            # Ensure rollback if commit hasn't happened or partial commit occurred (though sqlite commit is atomic)
            db = get_db() # Re-get db if it was closed or in an error state
            if db.in_transaction: # Check if a transaction is active
                 db.rollback()
            return jsonify({"message": "Failed to upload file"}), 500
    else:
        return jsonify({"message": "File type not allowed"}), 400

@files_bp.route('/files', methods=['GET'])
@token_required
def list_my_files_route():
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT id, filename, filesize, upload_time, permission, download_link_id
            FROM files
            WHERE user_id = ?
            ORDER BY upload_time DESC
        """, (g.current_user_id,))
        files_data = cursor.fetchall()
    except sqlite3.Error as e:
        current_app.logger.error(f"DB error listing files for user {g.current_user_id}: {e}")
        return jsonify({"message": "Database error fetching files"}), 500
    
    my_files = [dict(row) for row in files_data]
    return jsonify({"files": my_files, "count": len(my_files)}), 200


@files_bp.route('/files/<int:file_id>', methods=['GET'])
@token_required
def get_file_metadata_route(file_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT f.id, f.filename, f.filesize, f.upload_time, f.permission, f.download_link_id, f.user_id, u.username as owner_username
            FROM files f
            JOIN users u ON f.user_id = u.id
            WHERE f.id = ?
        """, (file_id,))
        file_data_row = cursor.fetchone()
    except sqlite3.Error as e:
        current_app.logger.error(f"DB error fetching metadata for file {file_id}: {e}")
        return jsonify({"message": "Database error fetching file metadata"}), 500

    if not file_data_row:
        return jsonify({"message": "File not found"}), 404

    file_info = dict(file_data_row)

    # Owner can always see metadata. Public files metadata can be seen by anyone authenticated (as per @token_required).
    # If further restriction is needed for public files by non-owners, add logic here.
    if file_info['user_id'] != g.current_user_id and file_info['permission'] == 'private': # Or check other permissions
         return jsonify({"message": "Access denied to view this file's metadata"}), 403 # More specific than "not found"
    
    return jsonify(file_info), 200


@files_bp.route('/files/<int:file_id>/permission', methods=['PUT'])
@token_required
def set_file_permission_route(file_id):
    data = request.get_json()
    new_permission = data.get('permission')
    file_password = data.get('password') # For 'password' type

    if not new_permission or new_permission not in ['public', 'private', 'password']:
        return jsonify({"message": "Invalid permission value. Must be 'public', 'private', or 'password'."}), 400
    if new_permission == 'password' and not file_password:
        return jsonify({"message": "Password is required for 'password' permission."}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT user_id, permission, access_password_hash FROM files WHERE id = ?", (file_id,))
        file_record = cursor.fetchone()
    except sqlite3.Error as e:
        current_app.logger.error(f"DB error fetching file {file_id} for permission change: {e}")
        return jsonify({"message": "Database error fetching file"}), 500

    if not file_record:
        return jsonify({"message": "File not found"}), 404
    if file_record['user_id'] != g.current_user_id:
        return jsonify({"message": "Access denied. You are not the owner of this file."}), 403

    new_access_password_hash = file_record['access_password_hash'] # Keep old hash if not changing from/to password
    if new_permission == 'password':
        hashed_pw_bytes = bcrypt.hashpw(file_password.encode('utf-8'), bcrypt.gensalt())
        new_access_password_hash = hashed_pw_bytes.decode('utf-8')
    elif file_record['permission'] == 'password' and new_permission != 'password': # Changing from password to public/private
        new_access_password_hash = None # Clear password hash

    try:
        cursor.execute("""
            UPDATE files SET permission = ?, access_password_hash = ? WHERE id = ? AND user_id = ? 
        """, (new_permission, new_access_password_hash, file_id, g.current_user_id)) # Added user_id for safety
        db.commit()
        if cursor.rowcount == 0: # Should not happen if previous checks passed, but good for robustness
             return jsonify({"message": "File not found or permission update failed."}), 404
    except sqlite3.Error as e:
        db.rollback()
        current_app.logger.error(f"DB error updating permission for file {file_id}: {e}")
        return jsonify({"message": "Database error updating permission"}), 500
    
    current_app.logger.info(f"Permission for file {file_id} updated to '{new_permission}' by user {g.current_username}")
    return jsonify({"message": f"File permission updated to '{new_permission}' successfully."}), 200


@files_bp.route('/download/<string:link_id>', methods=['GET'])
def download_file_with_link_route(link_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT id, filename, filepath, permission, access_password_hash, user_id
            FROM files WHERE download_link_id = ?
        """, (link_id,))
        file_record = cursor.fetchone()
    except sqlite3.Error as e:
        current_app.logger.error(f"DB error fetching file by link_id {link_id}: {e}")
        return jsonify({"message": "Database error fetching file by link"}), 500

    if not file_record:
        return jsonify({"message": "Invalid download link or file not found."}), 404

    original_filename = file_record['filename']
    server_filepath = file_record['filepath']
    file_permission = file_record['permission']
    stored_password_hash_str = file_record['access_password_hash']
    
    if not os.path.exists(server_filepath):
        current_app.logger.warning(f"File {server_filepath} (link_id: {link_id}) not found on server but exists in DB.")
        # Consider DB cleanup logic here if desired (e.g., mark as missing or delete)
        return jsonify({"message": "File not found on server. It might have been deleted."}), 404

    if file_permission == 'public':
        current_app.logger.info(f"Public download initiated for {original_filename} via link_id {link_id}")
        return _send_file_helper(server_filepath, original_filename)
    
    elif file_permission == 'password':
        provided_password = request.args.get('password')
        if not provided_password: # Try Basic Auth if query param not present
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.lower().startswith('basic '):
                try:
                    decoded_str = base64.b64decode(auth_header.split(" ")[1]).decode('utf-8')
                    # Basic Auth is typically username:password. Here, we only care about password.
                    provided_password = decoded_str.split(':', 1)[1] if ':' in decoded_str else decoded_str
                except Exception as decode_err:
                    current_app.logger.warning(f"Malformed Basic Auth header for link_id {link_id}: {decode_err}")
                    return jsonify({"message": "Malformed Basic Auth header for password."}), 400
        
        if not provided_password:
             return jsonify({"message": "Password required. Provide as query parameter 'password' or Basic Auth."}), 401

        if stored_password_hash_str and bcrypt.checkpw(provided_password.encode('utf-8'), stored_password_hash_str.encode('utf-8')):
            current_app.logger.info(f"Password-protected download initiated for {original_filename} via link_id {link_id}")
            return _send_file_helper(server_filepath, original_filename)
        else:
            return jsonify({"message": "Incorrect password."}), 401
            
    elif file_permission == 'private':
        # For private files, require JWT token of the owner, even with link.
        # This part needs to be adapted if we want link-based private access for owner.
        # The original code implies a link doesn't bypass private if not owner.
        # To check owner: need to decode JWT if present, or state this link is not for private files.
        # For simplicity, maintaining original logic:
        return jsonify({"message": "This file is private and cannot be downloaded via this link without owner authentication via standard API access."}), 403
    
    else: # Should not happen
        current_app.logger.error(f"File {original_filename} (link_id: {link_id}) has unknown permission type: {file_permission}")
        return jsonify({"message": "File has an unknown permission type."}), 500


@files_bp.route('/files/<int:file_id>', methods=['DELETE'])
@token_required
def delete_file_route(file_id):
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT user_id, filepath FROM files WHERE id = ? AND user_id = ?", (file_id, g.current_user_id))
        file_record = cursor.fetchone()
    except sqlite3.Error as e:
        current_app.logger.error(f"DB error fetching file {file_id} for deletion by user {g.current_user_id}: {e}")
        return jsonify({"message": "Database error fetching file for deletion"}), 500

    if not file_record:
        # This means either file doesn't exist OR user is not the owner.
        # To give a more precise message, you could do a two-step check, but this is safer.
        return jsonify({"message": "File not found or access denied."}), 404 # Or 403 if you confirm existence but not ownership

    server_filepath_to_delete = file_record['filepath']

    try:
        # 1. Delete record from database first (within transaction)
        cursor.execute("DELETE FROM files WHERE id = ? AND user_id = ?", (file_id, g.current_user_id))
        
        # 2. Delete actual file from server
        if os.path.exists(server_filepath_to_delete):
            os.remove(server_filepath_to_delete)
            current_app.logger.info(f"File {server_filepath_to_delete} (ID: {file_id}) deleted from server by user {g.current_username}.")
        else:
            # DB record will be deleted, but file was already missing. Log this.
            current_app.logger.warning(f"File {server_filepath_to_delete} (ID: {file_id}) not found on server during deletion, but DB record removed.")
        
        db.commit()
        return jsonify({"message": "File deleted successfully"}), 200
    
    except sqlite3.Error as e_db:
        db.rollback()
        current_app.logger.error(f"DB error during deletion of file {file_id}: {e_db}")
        return jsonify({"message": "Database error during file deletion"}), 500
    except OSError as e_os:
        db.rollback() # Rollback the DB delete if file system delete fails
        current_app.logger.error(f"OS error deleting file {server_filepath_to_delete} from server for file ID {file_id}: {e_os}")
        return jsonify({"message": "Error deleting file from server, database changes rolled back."}), 500
    except Exception as e: # Catch any other unexpected errors
        db.rollback()
        current_app.logger.error(f"Unexpected error during deletion of file {file_id}: {e}")
        return jsonify({"message": "An unexpected error occurred during file deletion"}), 500