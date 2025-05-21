// v2/app/static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function () {
    const fileListBody = document.getElementById('fileListBody');
    const fileListMessage = document.getElementById('fileListMessage');
    const token = localStorage.getItem('jwtToken');

    // 비밀번호 모달 관련 요소
    const passwordModal = document.getElementById('passwordModal');
    const closePasswordModalBtn = document.getElementById('closePasswordModal');
    const filePasswordInput = document.getElementById('filePasswordInput');
    const submitPasswordBtn = document.getElementById('submitPasswordBtn');
    const passwordModalMessage = document.getElementById('passwordModalMessage');
    const passwordPromptFile = document.getElementById('passwordPromptFile');
    let currentDownloadLink = null; // 현재 비밀번호를 입력받는 다운로드 링크 정보 저장

    if (!token) {
        // 토큰이 없으면 로그인 페이지로 리디렉션
        if (fileListMessage) fileListMessage.textContent = '로그인이 필요합니다. 로그인 페이지로 이동합니다.';
        if (fileListMessage) fileListMessage.style.color = 'red';
        setTimeout(() => {
            window.location.href = '/login-page';
        }, 2000);
        return;
    }

    async function fetchAndDisplayFiles() {
        if (!fileListBody) return;
        fileListBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">파일을 불러오는 중...</td></tr>'; // 로딩 메시지

        try {
            const response = await fetch('/api/files', { // 0단계에서 prefix 적용됨
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.status === 401) { // 토큰 만료 또는 유효하지 않은 경우
                localStorage.removeItem('jwtToken');
                localStorage.removeItem('username');
                if (fileListMessage) fileListMessage.textContent = '세션이 만료되었거나 유효하지 않습니다. 다시 로그인해주세요.';
                if (fileListMessage) fileListMessage.style.color = 'red';
                setTimeout(() => {
                    window.location.href = '/login-page';
                }, 2000);
                return;
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: '파일 목록을 가져오는데 실패했습니다.' }));
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.files && data.files.length > 0) {
                fileListBody.innerHTML = ''; // 기존 내용 지우기
                data.files.forEach(file => {
                    const row = fileListBody.insertRow();
                    row.insertCell().textContent = file.filename;
                    row.insertCell().textContent = formatFileSize(file.filesize);
                    row.insertCell().textContent = new Date(file.upload_time).toLocaleString('ko-KR');
                    row.insertCell().textContent = getPermissionText(file.permission);

                    const actionsCell = row.insertCell();
                    actionsCell.className = 'actions';

                    // 다운로드 링크
                    const downloadLink = document.createElement('a');
                    // API의 다운로드 경로는 /api/download/<link_id>
                    downloadLink.href = `/api/download/${file.download_link_id}`;
                    downloadLink.textContent = '다운로드';
                    downloadLink.setAttribute('data-filename', file.filename);
                    downloadLink.setAttribute('data-permission', file.permission);
                    downloadLink.setAttribute('data-linkid', file.download_link_id);

                    if (file.permission === 'password') {
                        downloadLink.addEventListener('click', function(event) {
                            event.preventDefault(); // 기본 링크 동작 방지
                            currentDownloadLink = {
                                linkId: file.download_link_id,
                                filename: file.filename
                            };
                            passwordPromptFile.textContent = `'${file.filename}' 파일의 비밀번호를 입력하세요.`;
                            passwordModalMessage.textContent = '';
                            filePasswordInput.value = '';
                            passwordModal.style.display = 'block';
                        });
                    } else if (file.permission === 'public') {
                        // public 파일은 바로 다운로드 (브라우저가 처리)
                        // downloadLink.setAttribute('download', file.filename); // 브라우저가 파일명으로 저장하도록 함
                    } else { // private
                        // private 파일은 현재 사용자가 소유자일 때만 다운로드 가능 (API에서 처리)
                        // 여기서는 일단 링크만 제공하고, API에서 권한 확인
                    }
                    actionsCell.appendChild(downloadLink);

                    // 권한 변경 버튼 (5단계에서 구현)
                    const permissionButton = document.createElement('button');
                    permissionButton.textContent = '권한 변경';
                    permissionButton.className = 'permission-btn';
                    permissionButton.onclick = () => alert(`'${file.filename}' 파일 권한 변경 기능 (구현 예정)`); // 알림창 대신 실제 기능 구현 필요
                    actionsCell.appendChild(permissionButton);

                    // 삭제 버튼 (5단계에서 구현)
                    const deleteButton = document.createElement('button');
                    deleteButton.textContent = '삭제';
                    deleteButton.className = 'delete-btn';
                    deleteButton.onclick = () => alert(`'${file.filename}' 파일 삭제 기능 (구현 예정)`); // 알림창 대신 실제 기능 구현 필요
                    actionsCell.appendChild(deleteButton);
                });
                if (fileListMessage) fileListMessage.textContent = '';
            } else {
                fileListBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">업로드된 파일이 없습니다.</td></tr>';
                if (fileListMessage) fileListMessage.textContent = '';
            }

        } catch (error) {
            console.error('Error fetching files:', error);
            if (fileListBody) fileListBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">파일 목록을 불러오는데 실패했습니다.</td></tr>';
            if (fileListMessage) fileListMessage.textContent = error.message || '오류가 발생했습니다.';
            if (fileListMessage) fileListMessage.style.color = 'red';
        }
    }

    // 파일 크기 포맷 함수
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 접근 권한 텍스트 변환 함수
    function getPermissionText(permission) {
        switch (permission) {
            case 'public': return '공개';
            case 'private': return '비공개';
            case 'password': return '비밀번호';
            default: return permission;
        }
    }

    // 비밀번호 모달 닫기 버튼
    if (closePasswordModalBtn) {
        closePasswordModalBtn.onclick = function() {
            passwordModal.style.display = 'none';
            currentDownloadLink = null;
        }
    }

    // 모달 외부 클릭 시 닫기
    window.onclick = function(event) {
        if (event.target == passwordModal) {
            passwordModal.style.display = 'none';
            currentDownloadLink = null;
        }
    }

    // 비밀번호 제출 버튼
    if (submitPasswordBtn) {
        submitPasswordBtn.onclick = function() {
            if (!currentDownloadLink) return;

            const password = filePasswordInput.value;
            if (!password) {
                passwordModalMessage.textContent = '비밀번호를 입력해주세요.';
                return;
            }
            passwordModalMessage.textContent = '';

            // 비밀번호와 함께 다운로드 URL 생성 및 이동
            const downloadUrl = `/api/download/${currentDownloadLink.linkId}?password=${encodeURIComponent(password)}`;
            
            window.location.href = downloadUrl; 

            // 다운로드 시도 후 모달 닫기 (성공 여부와 관계없이)
            // 실제로는 서버 응답을 확인하고 처리하는 것이 더 좋음
            setTimeout(() => {
                 passwordModal.style.display = 'none';
                 currentDownloadLink = null;
            }, 1000); // 약간의 딜레이 후 모달 닫기
        }
    }

    // 페이지 로드 시 파일 목록 가져오기
    fetchAndDisplayFiles();

    // 전역적으로 접근 가능한 파일 목록 새로고침 함수 (업로드, 삭제, 권한 변경 후 호출용)
    window.refreshFileList = fetchAndDisplayFiles;
});
