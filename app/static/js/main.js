    // v2/app/static/js/main.js

    document.addEventListener('DOMContentLoaded', function () {
        const navDashboard = document.getElementById('navDashboard');
        const navMyPage = document.getElementById('navMyPage'); // 마이페이지 링크 요소 가져오기
        const navLogin = document.getElementById('navLogin');
        const navRegister = document.getElementById('navRegister');
        const navLogout = document.getElementById('navLogout');
        const logoutButton = document.getElementById('logoutButton');
        const userInfoDiv = document.getElementById('userInfo');

        function updateNavUI() {
            const token = localStorage.getItem('jwtToken');
            const username = localStorage.getItem('username');

            if (token && username) { // 로그인 상태
                if (navDashboard) navDashboard.style.display = 'list-item';
                if (navMyPage) navMyPage.style.display = 'list-item'; // 마이페이지 링크 표시
                if (navLogin) navLogin.style.display = 'none';
                if (navRegister) navRegister.style.display = 'none';
                if (navLogout) navLogout.style.display = 'list-item';
                if (userInfoDiv) userInfoDiv.textContent = `${username}님, 환영합니다!`;
            } else { // 로그아웃 상태
                if (navDashboard) navDashboard.style.display = 'none';
                if (navMyPage) navMyPage.style.display = 'none'; // 마이페이지 링크 숨김
                if (navLogin) navLogin.style.display = 'list-item';
                if (navRegister) navRegister.style.display = 'list-item';
                if (navLogout) navLogout.style.display = 'none';
                if (userInfoDiv) userInfoDiv.textContent = '';
            }
        }

        updateNavUI();

        if (logoutButton) {
            logoutButton.addEventListener('click', function (event) {
                event.preventDefault(); 
                localStorage.removeItem('jwtToken');
                localStorage.removeItem('username');
                updateNavUI();
                alert('로그아웃 되었습니다.'); 
                window.location.href = '/login-page';
            });
        }
    });
    