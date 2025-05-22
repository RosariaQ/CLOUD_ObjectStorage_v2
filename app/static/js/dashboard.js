// v2/app/static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function () {
    // ... (이전 코드: fileListBody, fileListMessage, token, 모달 관련 변수 선언 등) ...
    const fileListBody = document.getElementById('fileListBody');
    const fileListMessage = document.getElementById('fileListMessage');
    const token = localStorage.getItem('jwtToken');

    const passwordModal = document.getElementById('passwordModal');
    const closePasswordModalBtn = document.getElementById('closePasswordModal');
    const filePasswordInput = document.getElementById('filePasswordInput');
    const submitPasswordBtn = document.getElementById('submitPasswordBtn');
    const passwordModalMessage = document.getElementById('passwordModalMessage');
    const passwordPromptFile = document.getElementById('passwordPromptFile');
    let currentDownloadLink = null;

    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const uploadMessage = document.getElementById('uploadMessage');
    const uploadProgressDiv = document.getElementById('uploadProgress');
    const uploadProgressBar = document.getElementById('uploadProgressBar');


    if (!token) {
        if (fileListMessage) fileListMessage.textContent = '로그인이 필요합니다. 로그인 페이지로 이동합니다.';
        if (fileListMessage) fileListMessage.style.color = 'red';
        setTimeout(() => {
            window.location.href = '/login-page';
        }, 2000);
        return;
    }

    async function fetchAndDisplayFiles() {
        // ... (fetchAndDisplayFiles 함수 내용은 이전과 동일) ...
        if (!fileListBody) return;
        fileListBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">파일을 불러오는 중...</td></tr>';

        try {
            const response = await fetch('/api/files', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.status === 401) {
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
                fileListBody.innerHTML = '';
                data.files.forEach(file => {
                    const row = fileListBody.insertRow();
                    row.insertCell().textContent = file.filename;
                    row.insertCell().textContent = formatFileSize(file.filesize);
                    row.insertCell().textContent = new Date(file.upload_time).toLocaleString('ko-KR');
                    row.insertCell().textContent = getPermissionText(file.permission);

                    const actionsCell = row.insertCell();
                    actionsCell.className = 'actions';

                    const downloadLink = document.createElement('a');
                    downloadLink.href = `/api/download/${file.download_link_id}`;
                    downloadLink.textContent = '다운로드';
                    downloadLink.setAttribute('data-filename', file.filename);
                    downloadLink.setAttribute('data-permission', file.permission);
                    downloadLink.setAttribute('data-linkid', file.download_link_id);

                    if (file.permission === 'password') {
                        downloadLink.addEventListener('click', function(event) {
                            event.preventDefault();
                            currentDownloadLink = {
                                linkId: file.download_link_id,
                                filename: file.filename
                            };
                            passwordPromptFile.textContent = `'${file.filename}' 파일의 비밀번호를 입력하세요.`;
                            passwordModalMessage.textContent = '';
                            filePasswordInput.value = '';
                            passwordModal.style.display = 'block';
                        });
                    }
                    actionsCell.appendChild(downloadLink);

                    const permissionButton = document.createElement('button');
                    permissionButton.textContent = '권한 변경';
                    permissionButton.className = 'permission-btn';
                    permissionButton.onclick = () => alert(`'${file.filename}' 파일 권한 변경 기능 (구현 예정)`);
                    actionsCell.appendChild(permissionButton);

                    const deleteButton = document.createElement('button');
                    deleteButton.textContent = '삭제';
                    deleteButton.className = 'delete-btn';
                    deleteButton.onclick = () => alert(`'${file.filename}' 파일 삭제 기능 (구현 예정)`);
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

    function formatFileSize(bytes) {
        // ... (formatFileSize 함수 내용은 이전과 동일) ...
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function getPermissionText(permission) {
        // ... (getPermissionText 함수 내용은 이전과 동일) ...
        switch (permission) {
            case 'public': return '공개';
            case 'private': return '비공개';
            case 'password': return '비밀번호';
            default: return permission;
        }
    }

    if (closePasswordModalBtn) {
        // ... (모달 닫기 로직 이전과 동일) ...
        closePasswordModalBtn.onclick = function() {
            passwordModal.style.display = 'none';
            currentDownloadLink = null;
        }
    }

    window.onclick = function(event) {
        // ... (모달 외부 클릭 닫기 로직 이전과 동일) ...
        if (event.target == passwordModal) {
            passwordModal.style.display = 'none';
            currentDownloadLink = null;
        }
    }

    if (submitPasswordBtn) {
        // ... (비밀번호 제출 로직 이전과 동일) ...
        submitPasswordBtn.onclick = function() {
            if (!currentDownloadLink) return;
            const password = filePasswordInput.value;
            if (!password) {
                passwordModalMessage.textContent = '비밀번호를 입력해주세요.';
                return;
            }
            passwordModalMessage.textContent = '';
            const downloadUrl = `/api/download/${currentDownloadLink.linkId}?password=${encodeURIComponent(password)}`;
            window.location.href = downloadUrl;
            setTimeout(() => {
                 passwordModal.style.display = 'none';
                 currentDownloadLink = null;
            }, 1000);
        }
    }
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(event) {
            event.preventDefault(); 

            if (!fileInput.files || fileInput.files.length === 0) {
                if (uploadMessage) {
                    uploadMessage.textContent = '업로드할 파일을 선택해주세요.';
                    uploadMessage.style.color = 'red';
                }
                return;
            }

            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file); 

            if (uploadMessage) uploadMessage.textContent = '파일 업로드 중...';
            if (uploadMessage) uploadMessage.style.color = 'blue';
            if (uploadProgressDiv) uploadProgressDiv.style.display = 'block';
            if (uploadProgressBar) {
                uploadProgressBar.style.width = '0%';
                uploadProgressBar.textContent = '0%';
            }

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/upload', true); 
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            
            xhr.upload.onprogress = function(event) {
                if (event.lengthComputable) {
                    const percentComplete = Math.round((event.loaded / event.total) * 100);
                    if (uploadProgressBar) {
                        uploadProgressBar.style.width = percentComplete + '%';
                        uploadProgressBar.textContent = percentComplete + '%';
                    }
                }
            };

            // 👇 여기가 수정된 xhr.onload 함수입니다.
            xhr.onload = function() {
                if (uploadProgressDiv) uploadProgressDiv.style.display = 'none';
                if (fileInput) fileInput.value = ''; // 파일 입력 필드 초기화

                if (xhr.status >= 200 && xhr.status < 300) { // 성공 케이스
                    try {
                        const data = JSON.parse(xhr.responseText);
                        if (uploadMessage) {
                            uploadMessage.textContent = data.message || '파일이 성공적으로 업로드되었습니다.';
                            uploadMessage.style.color = 'green';
                        }
                        if (window.refreshFileList) {
                            window.refreshFileList();
                        }
                    } catch (e) {
                        console.error("Error parsing success response:", e);
                        if (uploadMessage) {
                            uploadMessage.textContent = '업로드 응답 처리 중 오류가 발생했습니다. (서버 응답이 JSON이 아님)';
                            uploadMessage.style.color = 'red';
                        }
                    }
                } else { // 오류 케이스 (4xx, 5xx 등)
                    let errorMessage = `서버 오류 (${xhr.status})`; // 기본 오류 메시지
                    
                    if (xhr.status === 413) {
                        // config.py에 설정된 MAX_CONTENT_LENGTH 값 (예: 256MB)
                        errorMessage = '업로드 실패: 파일이 너무 큽니다. 최대 허용 크기는 256MB 입니다.';
                    } else {
                        // API가 JSON 형태의 오류 메시지를 반환하는 경우를 먼저 시도
                        try {
                            if (xhr.responseText && xhr.getResponseHeader('Content-Type')?.includes('application/json')) {
                                const errorData = JSON.parse(xhr.responseText);
                                errorMessage = '업로드 실패: ' + (errorData.message || `서버 오류 (${xhr.status})`);
                            } else if (xhr.responseText) {
                                // JSON이 아니지만 응답 텍스트가 있는 경우 (예: HTML 오류 페이지)
                                // 전체 HTML을 보여주기보다는 상태 텍스트나 일반 메시지 사용
                                errorMessage = `업로드 실패: ${xhr.statusText || '서버에서 오류가 발생했습니다.'} (코드: ${xhr.status})`;
                                console.warn("Server returned non-JSON error response:", xhr.responseText);
                            }
                        } catch (e) {
                            // JSON 파싱 실패 시, 더 일반적인 오류 메시지 사용
                            console.error("Error parsing error response:", e);
                            errorMessage = `업로드 실패: ${xhr.statusText || '알 수 없는 서버 오류가 발생했습니다.'} (코드: ${xhr.status})`;
                        }
                    }
                    if (uploadMessage) {
                        uploadMessage.textContent = errorMessage;
                        uploadMessage.style.color = 'red';
                    }
                }
            };
            // 👆 수정된 xhr.onload 함수 끝

            xhr.onerror = function() {
                if (uploadProgressDiv) uploadProgressDiv.style.display = 'none';
                if (uploadMessage) {
                    uploadMessage.textContent = '업로드 중 네트워크 오류가 발생했습니다.';
                    uploadMessage.style.color = 'red';
                }
            };

            xhr.send(formData);
        });
    }

    fetchAndDisplayFiles();
    window.refreshFileList = fetchAndDisplayFiles;
});
