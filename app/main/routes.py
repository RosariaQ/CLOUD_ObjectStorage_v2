# v2/app/main/routes.py
from flask import render_template, Blueprint
from . import main_bp # __init__.py 에서 생성한 main_bp를 가져옴

# 또는 직접 Blueprint 생성 후 등록
# main_bp = Blueprint('main', __name__) # 만약 __init__.py에서 임포트하지 않고 여기서 직접 생성한다면

@main_bp.route('/')
def home_page():
    # return "웹사이트 홈페이지에 오신 것을 환영합니다!" # 테스트용 텍스트 응답
    return render_template('home.html', title="홈") # 나중에 만들 home.html을 렌더링

@main_bp.route('/login-page') # API의 /api/auth/login과 구분하기 위해 다른 경로 사용
def login_page():
    # return "여기는 로그인 페이지입니다."
    return render_template('auth/login.html', title="로그인") # 나중에 만들 login.html을 렌더링

@main_bp.route('/register-page') # API의 /api/auth/register와 구분
def register_page():
    # return "여기는 회원가입 페이지입니다."
    return render_template('auth/register.html', title="회원가입") # 나중에 만들 register.html을 렌더링

@main_bp.route('/dashboard')
def list_files_page(): # 파일 목록을 보여주는 대시보드 페이지
    # return "여기는 파일 대시보드입니다."
    return render_template('files/dashboard.html', title="내 파일 대시보드") # 나중에 만들 dashboard.html을 렌더링