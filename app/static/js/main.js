// v2/app/static/js/main.js

document.addEventListener('DOMContentLoaded', function () {
    const navDashboard = document.getElementById('navDashboard');
    const navLogin = document.getElementById('navLogin');
    const navRegister = document.getElementById('navRegister');
    const navLogout = document.getElementById('navLogout');
    const logoutButton = document.getElementById('logoutButton');
    const userInfoDiv = document.getElementById('userInfo');

    function updateNavUI() {
        const token = localStorage.getItem('jwtToken');
        const username = localStorage.getItem('username');

        if (token && username) { // 로그인 상태
            if (navDashboard) navDashboard.style.display = 'list-item'; // 또는 'block', 'inline' 등 적절한 display 값
            if (navLogin) navLogin.style.display = 'none';
            if (navRegister) navRegister.style.display = 'none';
            if (navLogout) navLogout.style.display = 'list-item';
            if (userInfoDiv) userInfoDiv.textContent = `${username}님, 환영합니다!`;
        } else { // 로그아웃 상태
            if (navDashboard) navDashboard.style.display = 'none';
            if (navLogin) navLogin.style.display = 'list-item';
            if (navRegister) navRegister.style.display = 'list-item';
            if (navLogout) navLogout.style.display = 'none';
            if (userInfoDiv) userInfoDiv.textContent = '';
        }
    }

    // 페이지 로드 시 네비게이션 UI 업데이트
    updateNavUI();

    // 로그아웃 버튼 이벤트 리스너
    if (logoutButton) {
        logoutButton.addEventListener('click', function (event) {
            event.preventDefault(); // 링크 기본 동작 방지

            // localStorage에서 토큰 및 사용자 정보 제거
            localStorage.removeItem('jwtToken');
            localStorage.removeItem('username');

            // 로그아웃 후 UI 업데이트
            updateNavUI();

            // 사용자에게 알림 (선택 사항)
            alert('로그아웃 되었습니다.'); // 실제 서비스에서는 alert 대신 더 나은 UI 사용

            // 로그인 페이지 또는 홈페이지로 리디렉션
            window.location.href = '/login-page'; // 또는 '/' (홈페이지)
        });
    }

    // 로그인/회원가입 성공 후에도 UI를 업데이트하기 위해 이벤트를 사용할 수 있습니다.
    // 예를 들어, auth.js에서 로그인 성공 시 커스텀 이벤트를 발생시키고 main.js에서 수신
    // window.addEventListener('authChange', updateNavUI);
    // auth.js 로그인 성공 시:
    // localStorage.setItem('jwtToken', data.token);
    // window.dispatchEvent(new CustomEvent('authChange'));
    // 여기서는 페이지 새로고침/이동 시 DOMContentLoaded에서 처리되므로 일단 생략.
});
