// v2/app/static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function () {
    const fileListBody = document.getElementById('fileListBody');
    const fileListMessage = document.getElementById('fileListMessage');
    const token = localStorage.getItem('jwtToken');

    // 비밀번호 모달 (다운로드용)
    const passwordModal = document.getElementById('passwordModal');
    const closePasswordModalBtn = document.getElementById('closePasswordModal');
    const filePasswordInput = document.getElementById('filePasswordInput');
    const submitPasswordBtn = document.getElementById('submitPasswordBtn');
    const passwordModalMessage = document.getElementById('passwordModalMessage');
    const passwordPromptFile = document.getElementById('passwordPromptFile');
    let currentDownloadInfo = null; // 다운로드 관련 정보 저장

    // 업로드 폼
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const uploadMessage = document.getElementById('uploadMessage');
    const uploadProgressDiv = document.getElementById('uploadProgress');
    const uploadProgressBar = document.getElementById('uploadProgressBar');

    // --- 권한 변경 모달 관련 요소 ---
    const permissionModal = document.getElementById('permissionModal');
    const closePermissionModalBtn = document.getElementById('closePermissionModal');
    const permissionFileNameP = document.getElementById('permissionFileName');
    const permissionForm = document.getElementById('permissionForm');
    const permissionFileIdInput = document.getElementById('permissionFileId');
    const permissionSelect = document.getElementById('permissionSelect');
    const newPasswordSection = document.getElementById('newPasswordSection');
    const newFilePasswordInput = document.getElementById('newFilePassword');
    const permissionModalMessageP = document.getElementById('permissionModalMessage');
    const cancelPermissionChangeBtn = document.getElementById('cancelPermissionChangeBtn');
    // --- 권한 변경 모달 관련 요소 끝 ---

    if (!token) {
        if (fileListMessage) fileListMessage.textContent = '로그인이 필요합니다. 로그인 페이지로 이동합니다.';
        if (fileListMessage) fileListMessage.style.color = 'red';
        setTimeout(() => { window.location.href = '/login-page'; }, 2000);
        return;
    }

    async function fetchAndDisplayFiles() {
        if (!fileListBody) return;
        fileListBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">파일을 불러오는 중...</td></tr>';

        try {
            const response = await fetch('/api/files', {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
            });

            if (response.status === 401) {
                localStorage.removeItem('jwtToken'); localStorage.removeItem('username');
                if (fileListMessage) fileListMessage.textContent = '세션 만료. 다시 로그인해주세요.';
                setTimeout(() => { window.location.href = '/login-page'; }, 2000);
                return;
            }
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: '파일 목록 로드 실패.' }));
                throw new Error(errorData.message || `HTTP 오류! 상태: ${response.status}`);
            }
            const data = await response.json();

            if (data.files && data.files.length > 0) {
                fileListBody.innerHTML = '';
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
                    downloadLink.href = `/api/download/${file.download_link_id}`;
                    downloadLink.textContent = '다운로드';
                    downloadLink.className = 'download-btn'; // 스타일 적용
                    if (file.permission === 'password') {
                        downloadLink.addEventListener('click', function(event) {
                            event.preventDefault();
                            currentDownloadInfo = { linkId: file.download_link_id, filename: file.filename };
                            passwordPromptFile.textContent = `'${file.filename}' 파일의 비밀번호를 입력하세요.`;
                            passwordModalMessage.textContent = ''; filePasswordInput.value = '';
                            passwordModal.style.display = 'block';
                        });
                    }
                    actionsCell.appendChild(downloadLink);

                    // --- 권한 변경 버튼 로직 수정 ---
                    const permissionButton = document.createElement('button');
                    permissionButton.textContent = '권한'; // 텍스트 간결하게
                    permissionButton.className = 'permission-btn';
                    permissionButton.onclick = () => openPermissionModal(file.id, file.filename, file.permission);
                    actionsCell.appendChild(permissionButton);

                    // --- 삭제 버튼 로직 수정 ---
                    const deleteButton = document.createElement('button');
                    deleteButton.textContent = '삭제';
                    deleteButton.className = 'delete-btn';
                    deleteButton.onclick = () => confirmAndDeleteFile(file.id, file.filename);
                    actionsCell.appendChild(deleteButton);
                });
                if (fileListMessage) fileListMessage.textContent = '';
            } else {
                fileListBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">업로드된 파일이 없습니다.</td></tr>';
            }
        } catch (error) {
            console.error('파일 가져오기 오류:', error);
            if (fileListBody) fileListBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">파일 목록 로드 실패.</td></tr>';
            if (fileListMessage) fileListMessage.textContent = error.message || '오류 발생.';
        }
    }

    function formatFileSize(bytes) { /* ... (이전과 동일) ... */ 
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    function getPermissionText(permission) { /* ... (이전과 동일) ... */
        switch (permission) {
            case 'public': return '공개';
            case 'private': return '비공개';
            case 'password': return '비밀번호';
            default: return permission;
        }
    }

    // 다운로드용 비밀번호 모달 닫기 및 제출 (이전과 동일)
    if (closePasswordModalBtn) { closePasswordModalBtn.onclick = () => { passwordModal.style.display = 'none'; currentDownloadInfo = null; }}
    if (submitPasswordBtn) {
        submitPasswordBtn.onclick = () => {
            if (!currentDownloadInfo) return;
            const pass = filePasswordInput.value;
            if (!pass) { passwordModalMessage.textContent = '비밀번호를 입력하세요.'; return; }
            passwordModalMessage.textContent = '';
            window.location.href = `/api/download/${currentDownloadInfo.linkId}?password=${encodeURIComponent(pass)}`;
            setTimeout(() => { passwordModal.style.display = 'none'; currentDownloadInfo = null; }, 1000);
        }
    }
     // 업로드 폼 로직 (이전과 동일)
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            if (!fileInput.files || fileInput.files.length === 0) {
                if (uploadMessage) { uploadMessage.textContent = '업로드할 파일을 선택해주세요.'; uploadMessage.style.color = 'red';}
                return;
            }
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);

            if (uploadMessage) { uploadMessage.textContent = '파일 업로드 중...'; uploadMessage.style.color = 'blue';}
            if (uploadProgressDiv) uploadProgressDiv.style.display = 'block';
            if (uploadProgressBar) { uploadProgressBar.style.width = '0%'; uploadProgressBar.textContent = '0%';}

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/upload', true);
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            xhr.upload.onprogress = function(e) {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    if (uploadProgressBar) { uploadProgressBar.style.width = percentComplete + '%'; uploadProgressBar.textContent = percentComplete + '%';}
                }
            };
            xhr.onload = function() {
                if (uploadProgressDiv) uploadProgressDiv.style.display = 'none';
                if (fileInput) fileInput.value = '';
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const data = JSON.parse(xhr.responseText);
                        if (uploadMessage) { uploadMessage.textContent = data.message || '성공적으로 업로드되었습니다.'; uploadMessage.style.color = 'green';}
                        if (window.refreshFileList) window.refreshFileList();
                    } catch (e) { if (uploadMessage) {uploadMessage.textContent = '응답 처리 오류.'; uploadMessage.style.color = 'red';}}
                } else {
                    let errMsg = `서버 오류 (${xhr.status})`;
                    if (xhr.status === 413) errMsg = '업로드 실패: 파일이 너무 큽니다. (최대 256MB)';
                    else { try { if (xhr.responseText && xhr.getResponseHeader('Content-Type')?.includes('application/json')) { const errData = JSON.parse(xhr.responseText); errMsg = '업로드 실패: ' + (errData.message || `서버 오류 (${xhr.status})`);} else if (xhr.responseText) {errMsg = `업로드 실패: ${xhr.statusText || '서버 오류'} (코드: ${xhr.status})`;}} catch (e) {errMsg = `업로드 실패: ${xhr.statusText || '알 수 없는 서버 오류'} (코드: ${xhr.status})`;}}
                    if (uploadMessage) {uploadMessage.textContent = errMsg; uploadMessage.style.color = 'red';}
                }
            };
            xhr.onerror = function() { if (uploadProgressDiv) uploadProgressDiv.style.display = 'none'; if (uploadMessage) {uploadMessage.textContent = '네트워크 오류.'; uploadMessage.style.color = 'red';}};
            xhr.send(formData);
        });
    }


    // --- 권한 변경 로직 ---
    function openPermissionModal(fileId, filename, currentPermission) {
        if (!permissionModal || !permissionFileIdInput || !permissionFileNameP || !permissionSelect || !newPasswordSection || !permissionModalMessageP) return;
        permissionFileIdInput.value = fileId;
        permissionFileNameP.textContent = `파일: ${filename}`;
        permissionSelect.value = currentPermission;
        newPasswordSection.style.display = (currentPermission === 'password') ? 'block' : 'none';
        newFilePasswordInput.value = ''; // 새 비밀번호 필드 초기화
        permissionModalMessageP.textContent = '';
        permissionModal.style.display = 'block';
    }

    if (permissionSelect) {
        permissionSelect.addEventListener('change', function() {
            if (newPasswordSection) {
                newPasswordSection.style.display = (this.value === 'password') ? 'block' : 'none';
            }
        });
    }

    if (closePermissionModalBtn) {
        closePermissionModalBtn.onclick = () => { permissionModal.style.display = 'none'; };
    }
    if (cancelPermissionChangeBtn) {
        cancelPermissionChangeBtn.onclick = () => { permissionModal.style.display = 'none'; };
    }


    if (permissionForm) {
        permissionForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            if (!permissionModalMessageP || !permissionFileIdInput || !permissionSelect) return;

            const fileId = permissionFileIdInput.value;
            const newPermission = permissionSelect.value;
            let newPassword = null;

            if (newPermission === 'password') {
                if (!newFilePasswordInput || newFilePasswordInput.value.trim() === '') {
                    permissionModalMessageP.textContent = "'비밀번호' 권한을 선택한 경우 새 비밀번호를 입력해야 합니다.";
                    permissionModalMessageP.style.color = 'red';
                    return;
                }
                newPassword = newFilePasswordInput.value;
            }
            permissionModalMessageP.textContent = '변경 중...';
            permissionModalMessageP.style.color = 'blue';

            try {
                const payload = { permission: newPermission };
                if (newPermission === 'password' && newPassword) {
                    payload.password = newPassword;
                }

                const response = await fetch(`/api/files/${fileId}/permission`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok) {
                    permissionModalMessageP.textContent = data.message || '권한이 성공적으로 변경되었습니다.';
                    permissionModalMessageP.style.color = 'green';
                    if (window.refreshFileList) window.refreshFileList();
                    setTimeout(() => {
                        permissionModal.style.display = 'none';
                    }, 1500);
                } else {
                    permissionModalMessageP.textContent = '오류: ' + (data.message || '권한 변경에 실패했습니다.');
                    permissionModalMessageP.style.color = 'red';
                }
            } catch (error) {
                console.error('Permission change error:', error);
                permissionModalMessageP.textContent = '권한 변경 중 오류 발생: ' + error.message;
                permissionModalMessageP.style.color = 'red';
            }
        });
    }

    // --- 파일 삭제 로직 ---
    async function confirmAndDeleteFile(fileId, filename) {
        if (!confirm(`정말로 '${filename}' 파일을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`)) {
            return;
        }

        // 사용자에게 삭제 중임을 알리는 피드백 (선택 사항)
        if (fileListMessage) {
            fileListMessage.textContent = `'${filename}' 파일 삭제 중...`;
            fileListMessage.style.color = 'blue';
        }

        try {
            const response = await fetch(`/api/files/${fileId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const data = await response.json().catch(() => ({})); // 응답 본문이 없을 수도 있음

            if (response.ok) {
                if (fileListMessage) {
                    fileListMessage.textContent = data.message || `'${filename}' 파일이 성공적으로 삭제되었습니다.`;
                    fileListMessage.style.color = 'green';
                }
                if (window.refreshFileList) {
                    window.refreshFileList();
                }
            } else {
                if (fileListMessage) {
                    fileListMessage.textContent = '삭제 실패: ' + (data.message || `서버 오류 (${response.status})`);
                    fileListMessage.style.color = 'red';
                }
            }
        } catch (error) {
            console.error('Delete file error:', error);
            if (fileListMessage) {
                fileListMessage.textContent = '파일 삭제 중 오류 발생: ' + error.message;
                fileListMessage.style.color = 'red';
            }
        }
    }

    // 모달 외부 클릭 시 닫기 (공통 로직)
    window.addEventListener('click', function(event) {
        if (event.target === passwordModal) {
            passwordModal.style.display = 'none';
            currentDownloadInfo = null;
        }
        if (event.target === permissionModal) {
            permissionModal.style.display = 'none';
        }
    });

    fetchAndDisplayFiles();
    window.refreshFileList = fetchAndDisplayFiles;
});
