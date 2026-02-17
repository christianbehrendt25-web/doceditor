// PDF.js viewer (v3, classic script)
document.addEventListener('DOMContentLoaded', () => {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

    const pdfCanvas = document.getElementById('pdf-canvas');
    const ctx = pdfCanvas.getContext('2d');
    let pdfDoc = null;
    let currentPage = 1;
    let totalPages = 0;
    let currentScale = 1.5;

    async function loadPdf() {
        const url = `/api/pdf/${FILE_ID}/serve?t=${Date.now()}`;
        pdfDoc = await pdfjsLib.getDocument(url).promise;
        totalPages = pdfDoc.numPages;
        await renderPage(currentPage);
    }

    async function renderPage(num) {
        const page = await pdfDoc.getPage(num);
        const viewport = page.getViewport({ scale: currentScale });
        pdfCanvas.width = viewport.width;
        pdfCanvas.height = viewport.height;
        await page.render({ canvasContext: ctx, viewport }).promise;
        document.getElementById('page-info').textContent = `Seite ${num} / ${totalPages}`;

        // Resize annotation canvas to match
        const annoCanvas = document.getElementById('annotation-canvas');
        annoCanvas.width = viewport.width;
        annoCanvas.height = viewport.height;
        annoCanvas.style.width = viewport.width + 'px';
        annoCanvas.style.height = viewport.height + 'px';

        // Notify annotator
        if (window.onPdfPageRendered) {
            window.onPdfPageRendered(viewport.width, viewport.height);
        }
    }

    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) { currentPage--; renderPage(currentPage); }
    });

    document.getElementById('next-page').addEventListener('click', () => {
        if (currentPage < totalPages) { currentPage++; renderPage(currentPage); }
    });

    document.getElementById('rotate-page-btn').addEventListener('click', () => {
        fetch(`/api/pdf/${FILE_ID}/rotate-page`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ page: currentPage - 1, angle: 90 }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) { alert(data.error); return; }
            loadPdf();
            if (window.refreshVersions) window.refreshVersions();
        });
    });

    document.getElementById('delete-page-btn').addEventListener('click', () => {
        if (!confirm('Seite wirklich loeschen?')) return;
        fetch(`/api/pdf/${FILE_ID}/delete-page`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ page: currentPage - 1 }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) { alert(data.error); return; }
            if (currentPage > 1) currentPage--;
            loadPdf();
            if (window.refreshVersions) window.refreshVersions();
        });
    });

    // Text overlay placement
    let placingText = false;
    document.getElementById('place-text-overlay').addEventListener('click', () => {
        const text = document.getElementById('text-overlay-input').value.trim();
        if (!text) { alert('Bitte Text eingeben'); return; }
        placingText = true;
        pdfCanvas.style.cursor = 'crosshair';
    });

    pdfCanvas.addEventListener('click', (e) => {
        if (!placingText) return;
        placingText = false;
        pdfCanvas.style.cursor = 'default';
        const rect = pdfCanvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const text = document.getElementById('text-overlay-input').value.trim();
        const fontSize = parseInt(document.getElementById('text-overlay-size').value) || 14;
        const color = hexToRgb(document.getElementById('anno-color').value);

        fetch(`/api/pdf/${FILE_ID}/text-overlay`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                page: currentPage - 1, text, x, y,
                font_size: fontSize, color: [color.r, color.g, color.b],
            }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) { alert(data.error); return; }
            document.getElementById('text-overlay-input').value = '';
            loadPdf();
            if (window.refreshVersions) window.refreshVersions();
        });
    });

    function hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16), g: parseInt(result[2], 16), b: parseInt(result[3], 16)
        } : { r: 0, g: 0, b: 0 };
    }

    // Expose for annotator
    window.currentPdfPage = () => currentPage;
    window.reloadPdf = () => loadPdf();

    loadPdf();
});
