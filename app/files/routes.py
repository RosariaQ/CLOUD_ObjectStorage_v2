# app/files/routes.py
from flask import (
    Blueprint, request, jsonify, current_app, g, send_from_directory
)
import os
import uuid
import base64
import sqlite3
import bcrypt
from werkzeug.utils import secure_filename
from app.core.database import get_db
from app.core.decorators import token_required

files_bp = Blueprint('files', __name__)

def allowed_file(filename):
    """허용된 파일 확장자인지 확인합니다."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def _send_file_helper(db_stored_filepath: str, original_filename: str):
    """
    파일을 전송하는 헬퍼 함수입니다.
    db_stored_filepath: 데이터베이스에 저장된 경로 (예: 'unique_filename.ext').
    original_filename: 다운로드 시 사용할 파일 이름.
    """
    upload_folder_abs = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder_abs or not os.path.isabs(upload_folder_abs):
        current_app.logger.error(f"CRITICAL: UPLOAD_FOLDER ('{upload_folder_abs}') is not configured correctly or is not an absolute path.")
        return jsonify({"message": "Server configuration error."}), 500

    filename_on_server = os.path.basename(db_stored_filepath)
    actual_file_full_path = os.path.join(upload_folder_abs, filename_on_server)

    if not os.path.exists(actual_file_full_path) or not os.path.isfile(actual_file_full_path):
        current_app.logger.warning(f"File not found or not a file at: '{actual_file_full_path}' (requested for '{original_filename}')")
        return jsonify({"message": "File not found on server."}), 404

    try:
        return send_from_directory(
            directory=upload_folder_abs,
            path=filename_on_server,
            as_attachment=True,
            download_name=original_filename
        )
    except Exception as e:
        # 예상치 못한 오류 발생 시 상세 로그를 남깁니다.
        current_app.logger.error(f"Error sending file '{original_filename}' from '{actual_file_full_path}': {e}", exc_info=True)
        return jsonify({"message": "Error sending file."}), 500

@files_bp.route('/upload', methods=['POST'])
@token_required
def upload_file_route():
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No file selected for uploading."}), 400

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        # 서버에 저장될 고유한 파일명 (UPLOAD_FOLDER 기준 상대 경로)
        unique_internal_filename = f"{uuid.uuid4().hex}.{file_extension}" if file_extension else uuid.uuid4().hex
        
        upload_folder_abs_path = current_app.config['UPLOAD_FOLDER']
        if not os.path.isabs(upload_folder_abs_path):
            current_app.logger.error(f"CRITICAL: UPLOAD_FOLDER '{upload_folder_abs_path}' in config is not an absolute path!")
            return jsonify({"message": "Server configuration error."}), 500

        # 실제 파일이 저장될 전체 절대 경로
        filepath_on_server_abs = os.path.join(upload_folder_abs_path, unique_internal_filename)

        try:
            if not os.path.exists(upload_folder_abs_path):
                os.makedirs(upload_folder_abs_path)
            
            file.save(filepath_on_server_abs)
            filesize = os.path.getsize(filepath_on_server_abs)
            download_link_id = str(uuid.uuid4())
            
            db = get_db()
            cursor = db.cursor()
            # DB에는 UPLOAD_FOLDER 기준 상대 경로(unique_internal_filename)를 저장합니다.
            db_filepath_to_store = unique_internal_filename
            
            cursor.execute("""
                INSERT INTO files (user_id, filename, filepath, filesize, download_link_id, permission)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (g.current_user_id, original_filename, db_filepath_to_store, filesize, download_link_id, 'private'))
            db.commit()
            file_id = cursor.lastrowid
            
            current_app.logger.info(f"File '{original_filename}' (ID: {file_id}) uploaded by user '{g.current_username}'. Stored as '{db_filepath_to_store}'.")
            return jsonify({
                "message": "File uploaded successfully.",
                "file_id": file_id,
                "filename": original_filename,
                "filesize_bytes": filesize,
                "download_link_id": download_link_id
            }), 201

        except Exception as e:
            current_app.logger.error(f"Failed to upload file '{original_filename}' by user '{g.current_username}': {e}", exc_info=True)
            if os.path.exists(filepath_on_server_abs): # 부분적으로 저장된 파일 정리 시도
                try:
                    os.remove(filepath_on_server_abs)
                except OSError as oe:
                    current_app.logger.error(f"Error deleting partially uploaded file '{filepath_on_server_abs}': {oe}")
            db = get_db()
            if hasattr(db, 'in_transaction') and db.in_transaction:
                 db.rollback()
            return jsonify({"message": "Failed to upload file."}), 500
    else:
        return jsonify({"message": "File type not allowed."}), 400

@files_bp.route('/files', methods=['GET'])
@token_required
def list_my_files_route():
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT id, filename, filepath, filesize, upload_time, permission, download_link_id
            FROM files
            WHERE user_id = ?
            ORDER BY upload_time DESC
        """, (g.current_user_id,))
        files_data = cursor.fetchall()
    except sqlite3.Error as e:
        current_app.logger.error(f"DB error listing files for user {g.current_user_id}: {e}", exc_info=True)
        return jsonify({"message": "Database error fetching files."}), 500
    
    my_files = [dict(row) for row in files_data]
    return jsonify({"files": my_files, "count": len(my_files)}), 200

@files_bp.route('/files/<int:file_id>', methods=['GET'])
@token_required
def get_file_metadata_route(file_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT f.id, f.filename, f.filepath, f.filesize, f.upload_time, f.permission, f.download_link_id, f.user_id, u.username as owner_username
            FROM files f
            JOIN users u ON f.user_id = u.id
            WHERE f.id = ?
        """, (file_id,))
        file_data_row = cursor.fetchone()
    except sqlite3.Error as e:
        current_app.logger.error(f"DB error fetching metadata for file {file_id}: {e}", exc_info=True)
        return jsonify({"message": "Database error fetching file metadata."}), 500

    if not file_data_row:
        return jsonify({"message": "File not found."}), 404

    file_info = dict(file_data_row)
    if file_info['user_id'] != g.current_user_id and file_info['permission'] == 'private':
         return jsonify({"message": "Access denied to view this file's metadata."}), 403
    
    return jsonify(file_info), 200

@files_bp.route('/files/<int:file_id>/permission', methods=['PUT'])
@token_required
def set_file_permission_route(file_id):
    data = request.get_json()
    new_permission = data.get('permission')
    file_password = data.get('password') 

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
        current_app.logger.error(f"DB error fetching file {file_id} for permission change: {e}", exc_info=True)
        return jsonify({"message": "Database error fetching file."}), 500

    if not file_record:
        return jsonify({"message": "File not found."}), 404
    if file_record['user_id'] != g.current_user_id:
        return jsonify({"message": "Access denied. You are not the owner of this file."}), 403

    new_access_password_hash = file_record['access_password_hash'] 
    if new_permission == 'password':
        hashed_pw_bytes = bcrypt.hashpw(file_password.encode('utf-8'), bcrypt.gensalt())
        new_access_password_hash = hashed_pw_bytes.decode('utf-8')
    elif file_record['permission'] == 'password' and new_permission != 'password': 
        new_access_password_hash = None 

    try:
        cursor.execute("""
            UPDATE files SET permission = ?, access_password_hash = ? WHERE id = ? AND user_id = ? 
        """, (new_permission, new_access_password_hash, file_id, g.current_user_id))
        db.commit()
        if cursor.rowcount == 0: 
             return jsonify({"message": "File not found or permission update failed."}), 404 # Should not happen
    except sqlite3.Error as e:
        db.rollback()
        current_app.logger.error(f"DB error updating permission for file {file_id}: {e}", exc_info=True)
        return jsonify({"message": "Database error updating permission."}), 500
    
    current_app.logger.info(f"Permission for file {file_id} updated to '{new_permission}' by user '{g.current_username}'.")
    return jsonify({"message": f"File permission updated to '{new_permission}' successfully."}), 200

@files_bp.route('/download/<string:link_id>', methods=['GET'])
def download_file_with_link_route(link_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT filename, filepath, permission, access_password_hash
            FROM files WHERE download_link_id = ?
        """, (link_id,))
        file_record = cursor.fetchone()
    except sqlite3.Error as e:
        current_app.logger.error(f"DB error fetching file by link_id '{link_id}': {e}", exc_info=True)
        return jsonify({"message": "Database error."}), 500

    if not file_record:
        return jsonify({"message": "Invalid download link or file not found."}), 404

    original_filename = file_record['filename']
    db_stored_filepath = file_record['filepath'] 
    file_permission = file_record['permission']
    stored_password_hash_str = file_record['access_password_hash']
    
    if file_permission == 'public':
        return _send_file_helper(db_stored_filepath, original_filename)
    
    elif file_permission == 'password':
        provided_password = request.args.get('password')
        auth_header = request.headers.get('Authorization')

        if not provided_password and auth_header and auth_header.lower().startswith('basic '):
            try:
                decoded_str = base64.b64decode(auth_header.split(" ")[1]).decode('utf-8')
                provided_password = decoded_str.split(':', 1)[1] if ':' in decoded_str else decoded_str
            except Exception: # Malformed header, treat as no password provided
                pass 
        
        if not provided_password:
             response = jsonify({"message": "Password required."})
             response.status_code = 401
             # response.headers['WWW-Authenticate'] = 'Basic realm="Password protected file"' # Optional
             return response

        if stored_password_hash_str and bcrypt.checkpw(provided_password.encode('utf-8'), stored_password_hash_str.encode('utf-8')):
            return _send_file_helper(db_stored_filepath, original_filename)
        else:
            return jsonify({"message": "Incorrect password."}), 401
            
    elif file_permission == 'private':
        return jsonify({"message": "This file is private."}), 403
    
    else: 
        current_app.logger.error(f"File '{original_filename}' (link_id: {link_id}) has unknown permission: '{file_permission}'")
        return jsonify({"message": "File access error."}), 500

@files_bp.route('/files/<int:file_id>', methods=['DELETE'])
@token_required
def delete_file_route(file_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT user_id, filepath FROM files WHERE id = ? AND user_id = ?", (file_id, g.current_user_id))
        file_record = cursor.fetchone()
    except sqlite3.Error as e:
        current_app.logger.error(f"DB error fetching file {file_id} for deletion: {e}", exc_info=True)
        return jsonify({"message": "Database error."}), 500

    if not file_record:
        return jsonify({"message": "File not found or access denied."}), 404 

    db_stored_filepath = file_record['filepath']
    upload_folder_abs = current_app.config.get('UPLOAD_FOLDER')
    server_filepath_to_delete_abs = os.path.join(upload_folder_abs, os.path.basename(db_stored_filepath))

    try:
        cursor.execute("DELETE FROM files WHERE id = ? AND user_id = ?", (file_id, g.current_user_id))
        
        if os.path.exists(server_filepath_to_delete_abs):
            if os.path.isfile(server_filepath_to_delete_abs):
                os.remove(server_filepath_to_delete_abs)
            else: # Should not happen if uploads are always files
                current_app.logger.warning(f"Attempted to delete non-file path: {server_filepath_to_delete_abs}")
        else:
            current_app.logger.warning(f"File not found on server for deletion: {server_filepath_to_delete_abs}, but DB record removed.")
        
        db.commit()
        current_app.logger.info(f"File (ID: {file_id}, Path: {db_stored_filepath}) deleted by user '{g.current_username}'.")
        return jsonify({"message": "File deleted successfully."}), 200
    
    except sqlite3.Error as e_db:
        db.rollback()
        current_app.logger.error(f"DB error during deletion of file {file_id}: {e_db}", exc_info=True)
        return jsonify({"message": "Database error during file deletion."}), 500
    except OSError as e_os:
        db.rollback() 
        current_app.logger.error(f"OS error deleting file {server_filepath_to_delete_abs} (ID: {file_id}): {e_os}", exc_info=True)
        return jsonify({"message": "Error deleting file from server."}), 500
    except Exception as e: 
        db.rollback()
        current_app.logger.error(f"Unexpected error during deletion of file {file_id}: {e}", exc_info=True)
        return jsonify({"message": "An unexpected error occurred."}), 500
