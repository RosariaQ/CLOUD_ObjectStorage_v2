# app/__init__.py
from flask import Flask, jsonify
import os
import logging
from config import DevelopmentConfig

def create_app(config_object=DevelopmentConfig):
    app = Flask(__name__, instance_relative_config=True)
    # Flask(__name__)는 app 패키지를 기준으로 templates 및 static 폴더를 찾습니다.
    # 즉, 기본적으로 app/templates 와 app/static 을 사용합니다.
    app.config.from_object(config_object)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        app.logger.info(f"Created UPLOAD_FOLDER at {app.config['UPLOAD_FOLDER']}")

    from .core import database
    database.init_app(app)

    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .files.routes import files_bp
    app.register_blueprint(files_bp, url_prefix='/api')

    # 👇 새로운 main_bp 블루프린트를 등록합니다. (웹 페이지용)
    from .main.routes import main_bp # from .main import main_bp 로 해도 됩니다.
    app.register_blueprint(main_bp) # 웹 페이지는 보통 prefix 없이 최상위 URL 사용

    # @app.route('/') # 이 기본 라우트는 main_bp의 '/'로 대체되거나 삭제될 수 있습니다.
    # def hello_world():
    #     return jsonify({"message": "Welcome to the Simple Object Storage API!"}), 200
    # 위 라우트를 주석 처리하거나 삭제하고, main_bp의 home_page가 / 를 처리하도록 합니다.

    if not app.debug:
        file_handler = logging.FileHandler(os.path.join(app.instance_path, 'app.log'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')

    return app