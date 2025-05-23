// v2/app/static/js/auth.js

document.addEventListener('DOMContentLoaded', function () {
    // --- 회원가입 폼 로직 시작 ---
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        const submitButton = registerForm.querySelector('button[type="submit"]'); // 회원가입 버튼
        const usernameInput = document.getElementById('regUsername');
        const passwordInput = document.getElementById('regPassword');
        const messageDiv = document.getElementById('registerMessage');

        registerForm.addEventListener('submit', async function (event) {
            event.preventDefault(); // 기본 폼 제출 방지

            const username = usernameInput.value;
            const password = passwordInput.value;

            // 간단한 클라이언트 측 유효성 검사
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
            if (username.length < 3) {
                messageDiv.textContent = '사용자 이름은 3자 이상이어야 합니다.';
                messageDiv.style.color = 'red';
                return;
            }

            // 요청 시작 시 버튼 비활성화 및 메시지 업데이트
            if (submitButton) submitButton.disabled = true;
            messageDiv.textContent = '처리 중...';
            messageDiv.style.color = 'blue';

            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: username, // 서버에서 .lower() 처리 예정
                        password: password,
                    }),
                });

                const data = await response.json(); // 어떤 경우든 JSON 응답을 기대

                if (response.ok) { // HTTP 상태 코드가 200-299인 경우 (성공)
                    messageDiv.textContent = data.message + ' 로그인 페이지로 이동합니다.';
                    messageDiv.style.color = 'green';
                    usernameInput.value = '';
                    passwordInput.value = '';
                    setTimeout(() => {
                        window.location.href = '/login-page';
                    }, 2000);
                } else {
                    // 서버에서 오류 메시지를 보낸 경우 (4xx, 5xx)
                    messageDiv.textContent = '오류: ' + (data.message || `서버 응답 ${response.status}`);
                    messageDiv.style.color = 'red';
                }
            } catch (error) {
                // 네트워크 오류 또는 JSON 파싱 오류 등
                console.error('Register fetch error:', error);
                messageDiv.textContent = '회원가입 중 오류가 발생했습니다. 네트워크 연결을 확인하거나 잠시 후 다시 시도해주세요.';
                messageDiv.style.color = 'red';
            } finally {
                // 요청 완료 후 (성공/실패 모두) 버튼 다시 활성화
                if (submitButton) submitButton.disabled = false;
            }
        });
    }
    // --- 회원가입 폼 로직 끝 ---


    // --- 로그인 폼 로직 시작 (기존과 동일하게 유지) ---
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        const loginSubmitButton = loginForm.querySelector('button[type="submit"]'); // 로그인 버튼
        const usernameLoginInput = document.getElementById('username');
        const passwordLoginInput = document.getElementById('password');
        const messageLoginDiv = document.getElementById('loginMessage');

        loginForm.addEventListener('submit', async function (event) {
            event.preventDefault();

            const username = usernameLoginInput.value;
            const password = passwordLoginInput.value;

            if (!username || !password) {
                messageLoginDiv.textContent = '사용자 이름과 비밀번호를 모두 입력해주세요.';
                messageLoginDiv.style.color = 'red';
                return;
            }

            if (loginSubmitButton) loginSubmitButton.disabled = true;
            messageLoginDiv.textContent = '로그인 중...';
            messageLoginDiv.style.color = 'blue';

            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: username, // 서버에서 .lower() 처리 예정
                        password: password,
                    }),
                });

                const data = await response.json();

                if (response.ok) {
                    messageLoginDiv.textContent = data.message || '로그인 성공! 대시보드로 이동합니다.';
                    messageLoginDiv.style.color = 'green';

                    if (data.token) {
                        localStorage.setItem('jwtToken', data.token);
                        localStorage.setItem('username', data.username || username.toLowerCase()); // 서버에서 반환된 username 사용
                        console.log('Token stored:', data.token);
                    } else {
                        messageLoginDiv.textContent = '로그인 성공했으나 토큰을 받지 못했습니다.';
                        messageLoginDiv.style.color = 'orange';
                        if (loginSubmitButton) loginSubmitButton.disabled = false; // 토큰 없으면 버튼 다시 활성화
                        return;
                    }

                    usernameLoginInput.value = '';
                    passwordLoginInput.value = '';

                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1500);
                } else {
                    messageLoginDiv.textContent = '오류: ' + (data.message || `아이디 또는 비밀번호가 잘못되었습니다. (응답 ${response.status})`);
                    messageLoginDiv.style.color = 'red';
                }
            } catch (error) {
                console.error('Login fetch error:', error);
                messageLoginDiv.textContent = '로그인 중 오류가 발생했습니다. 네트워크 연결을 확인해주세요.';
                messageLoginDiv.style.color = 'red';
            } finally {
                 // 로그인 시도는 리디렉션되므로, 여기서 항상 활성화할 필요는 없을 수 있으나, 오류 시에는 필요.
                if (loginSubmitButton && !localStorage.getItem('jwtToken')) { // 로그인 실패 시에만 버튼 활성화
                    loginSubmitButton.disabled = false;
                }
            }
        });
    }
    // --- 로그인 폼 로직 끝 ---
});
