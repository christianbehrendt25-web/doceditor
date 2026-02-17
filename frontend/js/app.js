// Central config and hash router for DocEditor SPA
window.API_BASE = "";  // e.g. "/doceditor" or "http://other-server:8000"
window.FILE_ID = null;

(function () {
    function showSection(id) {
        document.querySelectorAll('.page-section').forEach(s => s.style.display = 'none');
        const el = document.getElementById(id);
        if (el) el.style.display = '';
    }

    function route() {
        const hash = location.hash || '#/';

        // #/pdf/{fileId}
        const pdfMatch = hash.match(/^#\/pdf\/(.+)$/);
        if (pdfMatch) {
            window.FILE_ID = pdfMatch[1];
            showSection('page-pdf');
            // Load file info for title
            fetch(API_BASE + '/api/files/' + FILE_ID)
                .then(r => r.json())
                .then(info => {
                    document.getElementById('pdf-filename').textContent = info.original_name || '';
                    document.title = 'DocEditor - ' + (info.original_name || '');
                });
            if (window.initPdfViewer) window.initPdfViewer();
            if (window.initPdfAnnotator) window.initPdfAnnotator();
            if (window.initVersionPanel) window.initVersionPanel('version-panel');
            return;
        }

        // #/image/{fileId}
        const imgMatch = hash.match(/^#\/image\/(.+)$/);
        if (imgMatch) {
            window.FILE_ID = imgMatch[1];
            showSection('page-image');
            fetch(API_BASE + '/api/files/' + FILE_ID)
                .then(r => r.json())
                .then(info => {
                    document.getElementById('image-filename').textContent = info.original_name || '';
                    document.title = 'DocEditor - ' + (info.original_name || '');
                });
            if (window.initImageEditor) window.initImageEditor();
            if (window.initVersionPanel) window.initVersionPanel('image-version-panel');
            return;
        }

        // Default: file list
        window.FILE_ID = null;
        document.title = 'DocEditor - Dateien';
        showSection('page-files');
        if (window.initFileBrowser) window.initFileBrowser();
    }

    window.addEventListener('hashchange', route);
    document.addEventListener('DOMContentLoaded', route);
})();
