// Export & Annotation panel (v2) – replaces version history panel
(function () {
    let currentPanelId = null;
    let fileType = null;

    // Restore user from localStorage
    window.ANNO_USER = localStorage.getItem('doceditor_user') || 'anonymous';

    window.initVersionPanel = function (panelElementId) {
        currentPanelId = panelElementId;
        // Fetch file type, then render panel
        fetch(API_BASE + `/api/files/${FILE_ID}`)
            .then(r => r.json())
            .then(info => {
                fileType = info.file_type;
                refreshPanel();
            });
    };

    function refreshPanel() {
        const panel = document.getElementById(currentPanelId);
        if (!panel || !FILE_ID) return;

        const isPdf = fileType === 'pdf';

        let html = '';

        // --- User selector (PDF only) ---
        if (isPdf) {
            html += `
<div class="card mb-2">
  <div class="card-body py-2">
    <h6 class="card-title mb-1">Benutzer</h6>
    <div class="input-group input-group-sm">
      <input type="text" id="anno-user-input" class="form-control" value="${escHtml(window.ANNO_USER)}" placeholder="Benutzername">
      <button class="btn btn-outline-secondary" id="set-user-btn">Setzen</button>
    </div>
  </div>
</div>`;
        }

        // --- Annotation layers (PDF only) ---
        if (isPdf) {
            html += `
<div class="card mb-2">
  <div class="card-body py-2">
    <h6 class="card-title mb-1">Annotation-Layer</h6>
    <div id="anno-layer-list"><small class="text-muted">Lade…</small></div>
  </div>
</div>`;
        }

        // --- Download buttons ---
        html += `
<div class="card mb-2">
  <div class="card-body py-2">
    <h6 class="card-title mb-1">Download</h6>
    <a href="${API_BASE}/api/files/${FILE_ID}/download?mode=original"
       class="btn btn-outline-secondary btn-sm w-100 mb-1" download>
      <i class="bi bi-download"></i> Original
    </a>
    <a href="${API_BASE}/api/files/${FILE_ID}/download?mode=current"
       class="btn btn-outline-primary btn-sm w-100 mb-1" download>
      <i class="bi bi-download"></i> Aktuell (ohne Annotationen)
    </a>`;

        if (isPdf) {
            html += `
    <button id="export-annotated-btn" class="btn btn-success btn-sm w-100 mb-1">
      <i class="bi bi-download"></i> Mit Annotationen exportieren
    </button>`;
        }

        html += `
    <button id="reset-original-btn" class="btn btn-outline-danger btn-sm w-100">
      <i class="bi bi-arrow-counterclockwise"></i> Auf Original zurücksetzen
    </button>
  </div>
</div>`;

        // --- Audit log ---
        html += `
<div class="card">
  <div class="card-body py-2">
    <h6 class="card-title mb-1">Audit-Log</h6>
    <div id="audit-entries" class="small" style="max-height:200px;overflow-y:auto;"></div>
  </div>
</div>`;

        panel.innerHTML = html;

        // Bind: set user
        const setUserBtn = panel.querySelector('#set-user-btn');
        if (setUserBtn) {
            setUserBtn.addEventListener('click', () => {
                const val = panel.querySelector('#anno-user-input').value.trim() || 'anonymous';
                window.ANNO_USER = val;
                localStorage.setItem('doceditor_user', val);
                if (window.reloadAnnotations) window.reloadAnnotations();
                refreshPanel();
            });
        }

        // Bind: reset
        panel.querySelector('#reset-original-btn').addEventListener('click', () => {
            if (!confirm('Strukturelle Änderungen und alle Annotationen zurücksetzen?')) return;
            fetch(API_BASE + `/api/files/${FILE_ID}/reset`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user: window.ANNO_USER }),
            }).then(r => r.json()).then(data => {
                if (data.error) { alert(data.error); return; }
                if (window.reloadPdf) window.reloadPdf();
                else if (window.initImageEditor) window.initImageEditor();
                refreshPanel();
            });
        });

        if (isPdf) {
            loadAnnotationLayers(panel);

            // Bind: export with annotations
            panel.querySelector('#export-annotated-btn').addEventListener('click', () => {
                exportAnnotated(panel);
            });
        }

        loadAudit();
    }

    function loadAnnotationLayers(panel) {
        fetch(API_BASE + `/api/files/${FILE_ID}/annotations`)
            .then(r => r.json())
            .then(allAnnotations => {
                const container = panel.querySelector('#anno-layer-list');
                if (!container) return;
                if (allAnnotations.length === 0) {
                    container.innerHTML = '<small class="text-muted">Keine Annotationen vorhanden</small>';
                    return;
                }
                container.innerHTML = allAnnotations.map(anno => {
                    const date = anno.updated_at ? new Date(anno.updated_at).toLocaleString('de-DE') : '–';
                    const isCurrentUser = anno.user === window.ANNO_USER;
                    return `<div class="form-check">
                        <input class="form-check-input anno-user-check" type="checkbox"
                            id="check-${escHtml(anno.user)}" value="${escHtml(anno.user)}" checked>
                        <label class="form-check-label" for="check-${escHtml(anno.user)}">
                            <strong>${escHtml(anno.user)}</strong>${isCurrentUser ? ' <span class="badge bg-primary">Du</span>' : ''}
                            <br><small class="text-muted">${date}</small>
                        </label>
                        <button class="btn btn-outline-danger btn-sm py-0 ms-1 delete-layer-btn" data-user="${escHtml(anno.user)}" title="Layer löschen">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>`;
                }).join('');

                container.querySelectorAll('.delete-layer-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const user = btn.dataset.user;
                        if (!confirm(`Annotations-Layer von "${user}" löschen?`)) return;
                        fetch(API_BASE + `/api/files/${FILE_ID}/annotations/${user}`, { method: 'DELETE' })
                            .then(() => {
                                if (window.reloadAnnotations) window.reloadAnnotations();
                                refreshPanel();
                            });
                    });
                });
            });
    }

    async function exportAnnotated(panel) {
        const checkedUsers = [...panel.querySelectorAll('.anno-user-check:checked')].map(el => el.value);
        if (checkedUsers.length === 0) {
            alert('Bitte mindestens einen Annotations-Layer auswählen.');
            return;
        }

        const btn = panel.querySelector('#export-annotated-btn');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Exportiere…';

        try {
            // Fetch annotations for selected users to get fabric_pages
            const allAnnotations = await fetch(API_BASE + `/api/files/${FILE_ID}/annotations`).then(r => r.json());
            const selected = allAnnotations.filter(a => checkedUsers.includes(a.user));

            // Render Fabric.js pages to PNG for each selected user
            const fabricOverlays = [];
            const pdfCanvas = document.getElementById('pdf-canvas');
            const w = pdfCanvas ? pdfCanvas.width : 794;
            const h = pdfCanvas ? pdfCanvas.height : 1123;

            for (const anno of selected) {
                for (const [pageStr, fabricJson] of Object.entries(anno.fabric_pages || {})) {
                    const png = await renderFabricToPng(fabricJson, w, h);
                    fabricOverlays.push({ page: parseInt(pageStr), user: anno.user, png });
                }
            }

            const response = await fetch(API_BASE + `/api/files/${FILE_ID}/export-annotated`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ users: checkedUsers, fabric_overlays: fabricOverlays }),
            });

            if (!response.ok) {
                const err = await response.json();
                alert(err.error || 'Export fehlgeschlagen');
                return;
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'annotated.pdf';
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        } catch (err) {
            alert('Export fehlgeschlagen: ' + err.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-download"></i> Mit Annotationen exportieren';
        }
    }

    function renderFabricToPng(fabricJson, width, height) {
        return new Promise((resolve) => {
            const el = document.createElement('canvas');
            el.width = width;
            el.height = height;
            // Temporarily attach to DOM (required by some browsers for toDataURL)
            el.style.cssText = 'position:fixed;left:-9999px;top:-9999px;';
            document.body.appendChild(el);
            const tmp = new fabric.Canvas(el, { width, height });
            tmp.loadFromJSON(fabricJson, () => {
                const png = tmp.toDataURL({ format: 'png' });
                tmp.dispose();
                el.remove();
                resolve(png);
            });
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
                    return `<div class="border-bottom py-1">
                        <strong>${escHtml(e.action)}</strong>
                        <span class="text-muted"> ${date}</span><br>
                        <small>${escHtml(e.user)}</small>
                    </div>`;
                }).join('');
            });
    }

    function escHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    window.refreshVersions = refreshPanel;          // keep old name working
    window.refreshAnnotationPanel = refreshPanel;
})();
