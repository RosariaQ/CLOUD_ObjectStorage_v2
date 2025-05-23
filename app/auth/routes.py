# app/auth/routes.py
from flask import Blueprint, request, jsonify, current_app, g
import bcrypt
import jwt
import datetime
import sqlite3
import os # 파일 삭제를 위해 os 모듈 임포트
from app.core.database import get_db
from app.core.decorators import token_required # 기존 토큰 데코레이터 사용

auth_bp = Blueprint('auth', __name__)

# --- 기존 /register, /login 라우트 생략 ---
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "Username and password are required"}), 400
    
    username = data['username'].lower() 
    password = data['password']

    if len(password) < 4:
        return jsonify({"message": "Password must be at least 4 characters long"}), 400
    if len(username) < 3:
        return jsonify({"message": "Username must be at least 3 characters long"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return jsonify({"message": "Username already exists"}), 409
        
        hashed_password_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_password_str = hashed_password_bytes.decode('utf-8') 

        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                       (username, hashed_password_str))
        db.commit()
    except sqlite3.Error as e:
        db.rollback()
        current_app.logger.error(f"Database error during registration for {username}: {e}")
        if "UNIQUE constraint failed" in str(e):
             return jsonify({"message": "Username already taken or database constraint issue."}), 409
        return jsonify({"message": "Database error registering user"}), 500
    
    current_app.logger.info(f"User {username} registered successfully.")
    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "Username and password are required"}), 400
    
    username = data['username'].lower()
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

    stored_password_hash_bytes = user['password_hash'].encode('utf-8')

    if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash_bytes):
        token_payload = {
            'user_id': user['id'],
            'username': user['username'],
            'exp': datetime.datetime.utcnow() + current_app.config['JWT_EXPIRATION_DELTA']
        }
        try:
            token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')
            current_app.logger.info(f"User {username} logged in successfully.")
            # 로그인 성공 시 사용자 이름도 함께 반환 (클라이언트에서 사용 가능)
            return jsonify({"message": "Login successful", "token": token, "username": user['username']}), 200
        except Exception as e:
            current_app.logger.error(f"Error generating token for {username}: {e}")
            return jsonify({"message": "Error generating token"}), 500
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# 👇 회원 탈퇴 API 엔드포인트
@auth_bp.route('/user', methods=['DELETE'])
@token_required # JWT 토큰으로 인증된 사용자만 접근 가능
def delete_user_account():
    user_id_to_delete = g.current_user_id # @token_required 데코레이터가 g 객체에 설정
    username_to_delete = g.current_username

    db = get_db()
    cursor = db.cursor()

    try:
        # 1. 사용자가 업로드한 파일 정보 조회
        cursor.execute("SELECT id, filepath FROM files WHERE user_id = ?", (user_id_to_delete,))
        user_files = cursor.fetchall()

        upload_folder_abs = current_app.config.get('UPLOAD_FOLDER')
        if not upload_folder_abs or not os.path.isabs(upload_folder_abs):
            current_app.logger.error("CRITICAL: UPLOAD_FOLDER is not configured correctly or is not an absolute path for user deletion.")
            # 이 경우 DB는 롤백하고 오류 반환
            db.rollback()
            return jsonify({"message": "Server configuration error preventing file deletion."}), 500

        # 2. 실제 파일 시스템에서 파일 삭제
        for file_record in user_files:
            db_stored_filepath = file_record['filepath'] # 예: 'unique_filename.ext'
            # UPLOAD_FOLDER 기준 상대 경로이므로, 절대 경로로 변환
            server_filepath_to_delete_abs = os.path.join(upload_folder_abs, os.path.basename(db_stored_filepath))
            if os.path.exists(server_filepath_to_delete_abs):
                try:
                    os.remove(server_filepath_to_delete_abs)
                    current_app.logger.info(f"Deleted physical file: {server_filepath_to_delete_abs} for user {username_to_delete}")
                except OSError as e:
                    current_app.logger.error(f"Error deleting physical file {server_filepath_to_delete_abs}: {e}")
                    # 파일 삭제 실패 시 일단 계속 진행하고 DB는 롤백할지, 아니면 이 파일만 남기고 DB는 삭제할지 결정 필요.
                    # 여기서는 DB 롤백을 위해 예외를 다시 발생시키거나, 플래그를 설정할 수 있습니다.
                    # 일단은 로그만 남기고 DB 삭제는 시도합니다. (더 견고하게 하려면 여기서 롤백)
            else:
                current_app.logger.warning(f"Physical file not found for deletion: {server_filepath_to_delete_abs} (DB record ID: {file_record['id']})")

        # 3. `files` 테이블에서 해당 사용자의 파일 레코드 삭제
        # ON DELETE CASCADE가 users 테이블의 user_id 외래키에 설정되어 있다면 이 부분은 자동으로 처리될 수 있습니다.
        # 하지만 명시적으로 삭제하는 것이 더 안전할 수 있습니다. (schema.sql 확인 필요)
        # 현재 schema.sql에는 ON DELETE CASCADE가 없으므로 명시적 삭제 필요 [cite: uploaded:v2/schema.sql]
        cursor.execute("DELETE FROM files WHERE user_id = ?", (user_id_to_delete,))
        current_app.logger.info(f"Deleted file records from DB for user {username_to_delete} (ID: {user_id_to_delete})")

        # 4. `users` 테이블에서 사용자 레코드 삭제
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id_to_delete,))
        current_app.logger.info(f"Deleted user record from DB for user {username_to_delete} (ID: {user_id_to_delete})")

        db.commit()
        current_app.logger.info(f"User account {username_to_delete} (ID: {user_id_to_delete}) and associated files deleted successfully.")
        return jsonify({"message": "Account and all associated files deleted successfully."}), 200

    except sqlite3.Error as e:
        db.rollback()
        current_app.logger.error(f"Database error during account deletion for user {username_to_delete} (ID: {user_id_to_delete}): {e}")
        return jsonify({"message": "Database error during account deletion."}), 500
    except Exception as e:
        db.rollback() # 예상치 못한 오류 발생 시에도 롤백
        current_app.logger.error(f"Unexpected error during account deletion for user {username_to_delete} (ID: {user_id_to_delete}): {e}", exc_info=True)
        return jsonify({"message": "An unexpected error occurred during account deletion."}), 500

