// v2/app/static/js/auth.js

document.addEventListener('DOMContentLoaded', function () {
    // --- 회원가입 폼 로직 시작 ---
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async function (event) {
            event.preventDefault(); // 기본 폼 제출 방지

            const usernameInput = document.getElementById('regUsername');
            const passwordInput = document.getElementById('regPassword');
            const messageDiv = document.getElementById('registerMessage');

            const username = usernameInput.value;
            const password = passwordInput.value;

            if (!username || !password) {
                messageDiv.textContent = '사용자 이름과 비밀번호를 모두 입력해주세요.';
                messageDiv.style.color = 'red';
                return;
            }
            if (password.length < 4) {
                messageDiv.textContent = '비밀번호는 4자 이상이어야 합니다.';
                messageDiv.style.color = 'red';
                return;
            }

            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password,
                    }),
                });

                const data = await response.json();

                if (response.ok) {
                    messageDiv.textContent = data.message + ' 로그인 페이지로 이동합니다.';
                    messageDiv.style.color = 'green';
                    usernameInput.value = '';
                    passwordInput.value = '';
                    setTimeout(() => {
                        window.location.href = '/login-page';
                    }, 2000);
                } else {
                    messageDiv.textContent = '오류: ' + (data.message || '알 수 없는 오류가 발생했습니다.');
                    messageDiv.style.color = 'red';
                }
            } catch (error) {
                console.error('Register fetch error:', error);
                messageDiv.textContent = '회원가입 중 오류가 발생했습니다. 네트워크 연결을 확인해주세요.';
                messageDiv.style.color = 'red';
            }
        });
    }
    // --- 회원가입 폼 로직 끝 ---


    // --- 로그인 폼 로직 시작 ---
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function (event) {
            event.preventDefault(); // 기본 폼 제출 방지

            const usernameInput = document.getElementById('username');
            const passwordInput = document.getElementById('password');
            const messageDiv = document.getElementById('loginMessage');

            const username = usernameInput.value;
            const password = passwordInput.value;

            if (!username || !password) {
                messageDiv.textContent = '사용자 이름과 비밀번호를 모두 입력해주세요.';
                messageDiv.style.color = 'red';
                return;
            }

            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password,
                    }),
                });

                const data = await response.json();

                if (response.ok) {
                    messageDiv.textContent = data.message || '로그인 성공! 대시보드로 이동합니다.';
                    messageDiv.style.color = 'green';

                    if (data.token) {
                        localStorage.setItem('jwtToken', data.token);
                        localStorage.setItem('username', username); // 사용자 이름도 저장
                        console.log('Token stored:', data.token);
                    } else {
                        messageDiv.textContent = '로그인 성공했으나 토큰을 받지 못했습니다.';
                        messageDiv.style.color = 'orange';
                        return;
                    }

                    usernameInput.value = '';
                    passwordInput.value = '';

                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1500);

                } else {
                    messageDiv.textContent = '오류: ' + (data.message || '아이디 또는 비밀번호가 잘못되었습니다.');
                    messageDiv.style.color = 'red';
                }
            } catch (error) {
                console.error('Login fetch error:', error);
                messageDiv.textContent = '로그인 중 오류가 발생했습니다. 네트워크 연결을 확인해주세요.';
                messageDiv.style.color = 'red';
            }
        });
    }
    // --- 로그인 폼 로직 끝 ---
});
