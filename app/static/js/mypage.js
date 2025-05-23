    // v2/app/static/js/mypage.js

    document.addEventListener('DOMContentLoaded', function () {
        const token = localStorage.getItem('jwtToken');
        const username = localStorage.getItem('username');
        const mypageUsernameSpan = document.getElementById('mypageUsername');
        const deleteAccountBtn = document.getElementById('deleteAccountBtn');
        const mypageMessageP = document.getElementById('mypageMessage');

        // 1. 로그인 상태 확인 및 사용자 이름 표시
        if (!token || !username) {
            if (mypageMessageP) {
                mypageMessageP.textContent = '로그인이 필요합니다. 로그인 페이지로 이동합니다.';
                mypageMessageP.style.color = 'red';
            }
            setTimeout(() => {
                window.location.href = '/login-page';
            }, 2000);
            return;
        }

        if (mypageUsernameSpan) {
            mypageUsernameSpan.textContent = username;
        }

        // 2. 회원 탈퇴 버튼 이벤트 리스너
        if (deleteAccountBtn) {
            deleteAccountBtn.addEventListener('click', async function() {
                if (!confirm(`정말로 계정을 탈퇴하시겠습니까?\n이 작업은 되돌릴 수 없으며, 모든 파일이 함께 삭제됩니다.`)) {
                    return;
                }

                if (mypageMessageP) {
                    mypageMessageP.textContent = '계정 삭제 처리 중...';
                    mypageMessageP.style.color = 'blue';
                }
                deleteAccountBtn.disabled = true; // 버튼 비활성화

                try {
                    const response = await fetch('/api/auth/user', { // 백엔드에서 만든 API 엔드포인트
                        method: 'DELETE',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    // 응답 본문이 있을 수도 있고 없을 수도 있으므로, 먼저 상태 코드로 판단
                    if (response.ok) {
                        const data = await response.json().catch(() => ({})); // JSON 파싱 시도, 실패 시 빈 객체
                        if (mypageMessageP) {
                            mypageMessageP.textContent = data.message || '계정이 성공적으로 삭제되었습니다. 홈페이지로 이동합니다.';
                            mypageMessageP.style.color = 'green';
                        }
                        // 로그아웃 처리 (localStorage 클리어)
                        localStorage.removeItem('jwtToken');
                        localStorage.removeItem('username');
                        
                        // 네비게이션 UI 업데이트 (main.js의 함수를 호출하거나, 여기서 직접 간단히 처리)
                        // 여기서는 main.js의 updateNavUI가 페이지 이동 후 처리할 것으로 기대
                        
                        setTimeout(() => {
                            window.location.href = '/'; // 홈페이지로 리디렉션
                        }, 2500);

                    } else {
                        const errorData = await response.json().catch(() => ({ message: '알 수 없는 오류 발생' }));
                        if (mypageMessageP) {
                            mypageMessageP.textContent = '계정 삭제 실패: ' + (errorData.message || `서버 오류 (${response.status})`);
                            mypageMessageP.style.color = 'red';
                        }
                        deleteAccountBtn.disabled = false; // 오류 시 버튼 다시 활성화
                    }

                } catch (error) {
                    console.error('Delete account error:', error);
                    if (mypageMessageP) {
                        mypageMessageP.textContent = '계정 삭제 중 오류가 발생했습니다: ' + error.message;
                        mypageMessageP.style.color = 'red';
                    }
                    deleteAccountBtn.disabled = false; // 오류 시 버튼 다시 활성화
                }
            });
        }
    });
    