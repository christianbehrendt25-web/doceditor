// Shared version sidebar panel
(function () {
    let currentPanelId = null;

    window.initVersionPanel = function (panelElementId) {
        currentPanelId = panelElementId;
        refreshVersions();
    };

    function refreshVersions() {
        const panel = document.getElementById(currentPanelId);
        if (!panel || !FILE_ID) return;

        fetch(API_BASE + `/api/files/${FILE_ID}/versions`)
            .then(r => r.json())
            .then(versions => {
                let html = '<div class="card"><div class="card-body">';
                html += '<h5 class="card-title">Versionen</h5>';
                html += '<div class="list-group list-group-flush">';
                versions.slice().reverse().forEach(v => {
                    const date = new Date(v.created_at).toLocaleString('de-DE');
                    const isCurrent = versions.indexOf(v) === versions.length - 1;
                    html += `<div class="list-group-item version-item ${isCurrent ? 'active' : ''}">
                        <div class="d-flex justify-content-between">
                            <strong>v${v.version}</strong>
                            <small>${date}</small>
                        </div>
                        <small class="text-muted">${v.action}</small>
                        <div class="mt-1">
                            <a href="${API_BASE}/api/files/${FILE_ID}/download/${v.version}" class="btn btn-outline-primary btn-sm" title="Download"><i class="bi bi-download"></i></a>
                            ${!isCurrent ? `<button class="btn btn-outline-warning btn-sm revert-btn" data-version="${v.version}" title="Wiederherstellen"><i class="bi bi-arrow-counterclockwise"></i></button>` : ''}
                        </div>
                    </div>`;
                });
                html += '</div></div></div>';

                html += '<div class="card mt-3"><div class="card-body">';
                html += '<h5 class="card-title">Audit-Log</h5>';
                html += '<div id="audit-entries" class="small" style="max-height:300px;overflow-y:auto;"></div>';
                html += '</div></div>';

                panel.innerHTML = html;

                panel.querySelectorAll('.revert-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const version = parseInt(btn.dataset.version);
                        if (!confirm(`Auf Version ${version} zuruecksetzen?`)) return;
                        fetch(API_BASE + `/api/files/${FILE_ID}/revert/${version}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({}),
                        }).then(r => r.json()).then(data => {
                            if (data.error) { alert(data.error); return; }
                            refreshVersions();
                            if (window.reloadPdf) window.reloadPdf();
                            else if (window.initImageEditor) window.initImageEditor();
                        });
                    });
                });

                loadAudit();
            });
    }

    function loadAudit() {
        fetch(API_BASE + `/api/audit-log?file_id=${FILE_ID}&limit=20`)
            .then(r => r.json())
            .then(entries => {
                const container = document.getElementById('audit-entries');
                if (!container) return;
                container.innerHTML = entries.slice().reverse().map(e => {
                    const date = new Date(e.timestamp).toLocaleString('de-DE');
                    return `<div class="border-bottom py-1"><strong>${e.action}</strong> <span class="text-muted">${date}</span><br><small>${e.user}</small></div>`;
                }).join('');
            });
    }

    window.refreshVersions = refreshVersions;
})();
