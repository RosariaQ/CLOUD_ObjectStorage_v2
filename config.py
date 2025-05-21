# config.py
import os
import datetime
from dotenv import load_dotenv

# .env 파일이 있다면 환경 변수를 로드합니다.
# .env 파일이 현재 config.py 파일과 같은 디렉토리(프로젝트 루트)에 있다고 가정합니다.
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    # .env 파일이 없는 경우, 개발 환경에서는 경고를 출력할 수 있습니다.
    # print("Warning: .env file not found. Using default configurations or system environment variables.")
    pass


# 현재 config.py 파일이 위치한 디렉토리를 프로젝트의 기본 디렉토리(BASE_DIR)로 설정합니다.
# os.path.abspath를 사용하여 항상 절대 경로를 갖도록 합니다.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """기본 설정 클래스"""
    # SECRET_KEY: Flask 애플리케이션의 보안을 위해 사용되는 키입니다.
    # 환경 변수 'SECRET_KEY'가 있으면 그 값을 사용하고, 없으면 기본값을 사용합니다.
    # 운영 환경에서는 반드시 강력하고 예측 불가능한 키로 변경해야 합니다.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_default_secret_key_for_development_change_me')

    # UPLOAD_FOLDER: 업로드된 파일이 저장될 폴더입니다.
    # 환경 변수 'UPLOAD_FOLDER'가 있으면 그 값을 사용하고, 없으면 BASE_DIR 아래 'uploads' 폴더를 기본값으로 사용합니다.
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))

    ALLOWED_EXTENSIONS = {
        'txt', 'log', 'md', 'json', 'xml', 'csv',
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'hwp',
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'ico',
        'mp4', 'mov', 'avi', 'wmv', 'mkv', 'webm',
        'mp3', 'wav', 'ogg', 'flac',
        'zip', 'tar', 'gz', '7z'
    }
    MAX_CONTENT_LENGTH = 256 * 1024 * 1024  # 256 MB

    # DATABASE: SQLite 데이터베이스 파일의 경로입니다.
    # 환경 변수 'DATABASE_PATH'가 있으면 그 값을 사용하고,
    # 없으면 BASE_DIR 아래 'instance' 폴더 내 'object_storage.db'를 기본값으로 사용합니다.
    # 'instance' 폴더는 Flask 앱의 instance_path와 일치시키는 것이 좋습니다.
    DATABASE_FILENAME = 'object_storage.db'
    DATABASE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'instance', DATABASE_FILENAME))


    # JWT_EXPIRATION_DELTA: JWT 토큰의 만료 시간을 설정합니다.
    # 환경 변수 'JWT_EXPIRATION_HOURS' (시간 단위)가 있으면 그 값을 사용하고, 없으면 24시간을 기본값으로 합니다.
    JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))
    JWT_EXPIRATION_DELTA = datetime.timedelta(hours=JWT_EXPIRATION_HOURS)

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    # SQLALCHEMY_ECHO = True # SQLAlchemy 사용 시 SQL 쿼리 로깅 (필요시 활성화)
    # 개발 중에는 SECRET_KEY가 기본값이더라도 괜찮지만, 실제 배포 시에는 반드시 변경해야 합니다.
    # print("Using Development Configuration")

class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False
    # 운영 환경에서는 SECRET_KEY, DATABASE 경로 등을 .env 또는 시스템 환경 변수를 통해
    # 반드시 안전하게 설정해야 합니다.
    # 예: LOG_LEVEL = 'INFO'
    # print("Using Production Configuration")

    # 운영 환경에서는 SECRET_KEY가 기본값이면 경고 또는 에러를 발생시킬 수 있습니다.
    if Config.SECRET_KEY == 'your_default_secret_key_for_development_change_me':
        # 실제 운영에서는 raise Exception(...) 등으로 처리하여 실행을 중단시키는 것이 좋습니다.
        print("CRITICAL WARNING: SECRET_KEY is not set for production environment!")


# 사용할 설정을 선택합니다. (예: 환경 변수 FLASK_ENV에 따라 동적으로 선택)
# 이 부분은 run.py 또는 app/__init__.py 에서 처리하는 것이 더 일반적입니다.
# 여기서는 예시로 남겨둡니다.
# active_config = DevelopmentConfig
# if os.environ.get('FLASK_ENV') == 'production':
# active_config = ProductionConfig
