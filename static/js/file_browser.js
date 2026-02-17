document.addEventListener('DOMContentLoaded', () => {
    const fileList = document.getElementById('file-list');
    const uploadForm = document.getElementById('upload-form');
    const uploadStatus = document.getElementById('upload-status');
    const mergeBtn = document.getElementById('merge-btn');
    const mergeSelection = document.getElementById('merge-selection');
    let mergeIds = [];

    function loadFiles() {
        fetch('/api/files')
            .then(r => r.json())
            .then(files => {
                fileList.innerHTML = '';
                mergeSelection.innerHTML = '';
                files.forEach(f => {
                    const icon = f.file_type === 'pdf' ? 'bi-file-earmark-pdf text-danger' : 'bi-file-earmark-image text-success';
                    const item = document.createElement('div');
                    item.className = 'list-group-item file-item d-flex justify-content-between align-items-center';
                    item.innerHTML = `
                        <div>
                            <i class="bi ${icon} me-2"></i>
                            <a href="/view/${f.file_id}">${f.original_name}</a>
                            <small class="text-muted ms-2">v${f.current_version}</small>
                        </div>
                        <div>
                            <a href="/api/files/${f.file_id}/download" class="btn btn-sm btn-outline-primary me-1" title="Download"><i class="bi bi-download"></i></a>
                            <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${f.file_id}" title="Loeschen"><i class="bi bi-trash"></i></button>
                        </div>
                    `;
                    fileList.appendChild(item);

                    // Merge checkbox for PDFs
                    if (f.file_type === 'pdf') {
                        const cb = document.createElement('div');
                        cb.className = 'form-check';
                        cb.innerHTML = `<input class="form-check-input merge-cb" type="checkbox" value="${f.file_id}" id="merge-${f.file_id}">
                            <label class="form-check-label" for="merge-${f.file_id}">${f.original_name}</label>`;
                        mergeSelection.appendChild(cb);
                    }
                });

                // Delete buttons
                document.querySelectorAll('.delete-btn').forEach(btn => {
                    btn.addEventListener('click', e => {
                        e.stopPropagation();
                        const id = btn.dataset.id;
                        if (confirm('Datei wirklich loeschen?')) {
                            fetch(`/api/files/${id}`, { method: 'DELETE' }).then(() => loadFiles());
                        }
                    });
                });

                // Merge checkboxes
                document.querySelectorAll('.merge-cb').forEach(cb => {
                    cb.addEventListener('change', () => {
                        mergeIds = [...document.querySelectorAll('.merge-cb:checked')].map(c => c.value);
                        mergeBtn.disabled = mergeIds.length < 2;
                    });
                });
            });
    }

    uploadForm.addEventListener('submit', e => {
        e.preventDefault();
        const fileInput = document.getElementById('file-input');
        if (!fileInput.files.length) return;
        const fd = new FormData();
        fd.append('file', fileInput.files[0]);
        uploadStatus.innerHTML = '<span class="text-info">Uploading...</span>';
        fetch('/api/files/upload', { method: 'POST', body: fd })
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
        fetch('/api/pdf/merge', {
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

    loadFiles();
});
