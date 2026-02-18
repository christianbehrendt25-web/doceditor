// File browser: upload, list, merge
(function () {
    let initialized = false;

    window.initFileBrowser = function () {
        const fileList = document.getElementById('file-list');
        const uploadForm = document.getElementById('upload-form');
        const uploadStatus = document.getElementById('upload-status');
        const mergeBtn = document.getElementById('merge-btn');
        const mergeSelection = document.getElementById('merge-selection');
        const photoPdfBtn = document.getElementById('photo-pdf-btn');
        const photoPdfSelection = document.getElementById('photo-pdf-selection');
        let mergeIds = [];
        let photoPdfIds = [];

        if (!initialized) {
            initialized = true;

            uploadForm.addEventListener('submit', e => {
                e.preventDefault();
                const fileInput = document.getElementById('file-input');
                if (!fileInput.files.length) return;
                const fd = new FormData();
                fd.append('file', fileInput.files[0]);
                uploadStatus.innerHTML = '<span class="text-info">Uploading...</span>';
                fetch(API_BASE + '/api/files/upload', { method: 'POST', body: fd })
                    .then(r => r.json())
                    .then(data => {
                        if (data.error) {
                            uploadStatus.innerHTML = `<span class="text-danger">${data.error}</span>`;
                        } else {
                            uploadStatus.innerHTML = '<span class="text-success">Erfolgreich!</span>';
                            fileInput.value = '';
                            loadFiles();
                        }
                    })
                    .catch(() => { uploadStatus.innerHTML = '<span class="text-danger">Fehler beim Upload</span>'; });
            });

            mergeBtn.addEventListener('click', () => {
                fetch(API_BASE + '/api/pdf/merge', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_ids: mergeIds }),
                })
                .then(r => r.json())
                .then(data => {
                    if (data.error) alert(data.error);
                    else loadFiles();
                });
            });

            photoPdfBtn.addEventListener('click', () => {
                photoPdfBtn.disabled = true;
                photoPdfBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Konvertiere...';
                const enhance = {
                    deskew: document.getElementById('enhance-deskew').checked,
                    sharpen: document.getElementById('enhance-sharpen').checked,
                    contrast: document.getElementById('enhance-contrast').checked,
                    threshold: document.getElementById('enhance-threshold').checked,
                };
                fetch(API_BASE + '/api/photo-to-pdf', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_ids: photoPdfIds, enhance }),
                })
                .then(r => r.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        loadFiles();
                        window.location.hash = '#/pdf/' + data.file_id;
                    }
                })
                .catch(() => alert('Fehler bei der Konvertierung'))
                .finally(() => {
                    photoPdfBtn.disabled = false;
                    photoPdfBtn.innerHTML = '<i class="bi bi-file-earmark-pdf"></i> Foto → PDF';
                });
            });
        }

        loadFiles();

        function loadFiles() {
            fetch(API_BASE + '/api/files')
                .then(r => r.json())
                .then(files => {
                    fileList.innerHTML = '';
                    mergeSelection.innerHTML = '';
                    photoPdfSelection.innerHTML = '';
                    files.forEach(f => {
                        const icon = f.file_type === 'pdf' ? 'bi-file-earmark-pdf text-danger' : 'bi-file-earmark-image text-success';
                        const viewHash = f.file_type === 'pdf' ? `#/pdf/${f.file_id}` : `#/image/${f.file_id}`;
                        const item = document.createElement('div');
                        item.className = 'list-group-item file-item d-flex justify-content-between align-items-center';
                        item.innerHTML = `
                            <div>
                                <i class="bi ${icon} me-2"></i>
                                <a href="${viewHash}">${f.original_name}</a>
                                <small class="text-muted ms-2">v${f.current_version}</small>
                            </div>
                            <div>
                                <a href="${API_BASE}/api/files/${f.file_id}/download" class="btn btn-sm btn-outline-primary me-1" title="Download"><i class="bi bi-download"></i></a>
                                <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${f.file_id}" title="Loeschen"><i class="bi bi-trash"></i></button>
                            </div>
                        `;
                        fileList.appendChild(item);

                        if (f.file_type === 'pdf') {
                            const cb = document.createElement('div');
                            cb.className = 'form-check';
                            cb.innerHTML = `<input class="form-check-input merge-cb" type="checkbox" value="${f.file_id}" id="merge-${f.file_id}">
                                <label class="form-check-label" for="merge-${f.file_id}">${f.original_name}</label>`;
                            mergeSelection.appendChild(cb);
                        }
                        if (f.file_type === 'image') {
                            const cb = document.createElement('div');
                            cb.className = 'form-check';
                            cb.innerHTML = `<input class="form-check-input photo-pdf-cb" type="checkbox" value="${f.file_id}" id="photo-${f.file_id}">
                                <label class="form-check-label" for="photo-${f.file_id}">${f.original_name}</label>`;
                            photoPdfSelection.appendChild(cb);
                        }
                    });

                    document.querySelectorAll('.delete-btn').forEach(btn => {
                        btn.addEventListener('click', e => {
                            e.stopPropagation();
                            const id = btn.dataset.id;
                            if (confirm('Datei wirklich loeschen?')) {
                                fetch(API_BASE + `/api/files/${id}`, { method: 'DELETE' }).then(() => loadFiles());
                            }
                        });
                    });

                    document.querySelectorAll('.merge-cb').forEach(cb => {
                        cb.addEventListener('change', () => {
                            mergeIds = [...document.querySelectorAll('.merge-cb:checked')].map(c => c.value);
                            mergeBtn.disabled = mergeIds.length < 2;
                        });
                    });

                    document.querySelectorAll('.photo-pdf-cb').forEach(cb => {
                        cb.addEventListener('change', () => {
                            photoPdfIds = [...document.querySelectorAll('.photo-pdf-cb:checked')].map(c => c.value);
                            photoPdfBtn.disabled = photoPdfIds.length < 1;
                        });
                    });
                });
        }
    };
})();
