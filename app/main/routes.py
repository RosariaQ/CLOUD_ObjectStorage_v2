# v2/app/main/routes.py
from flask import render_template, Blueprint, session  # session은 나중에 사용될 수 있음
from . import main_bp

@main_bp.route('/')
def home_page():
    return render_template('home.html', title="홈")

@main_bp.route('/login-page')
def login_page():
    return render_template('auth/login.html', title="로그인")

@main_bp.route('/register-page')
def register_page():
    return render_template('auth/register.html', title="회원가입")

@main_bp.route('/dashboard')
def list_files_page():
    return render_template('files/dashboard.html', title="내 파일 대시보드")

# 👇 마이페이지 라우트 추가
@main_bp.route('/mypage')
def my_page():
    # 여기서 사용자 정보를 DB에서 가져와 전달할 수도 있지만,
    # 일단은 JavaScript에서 localStorage의 사용자 이름을 사용하도록 합니다.
    return render_template('main_pages/mypage.html', title="마이페이지")
