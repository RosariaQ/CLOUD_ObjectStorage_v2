# v2/app/main/__init__.py
from flask import Blueprint

main_bp = Blueprint('main', __name__) # 템플릿 폴더는 app/templates를 기본으로 사용

from . import routes # 라우트들을 임포트