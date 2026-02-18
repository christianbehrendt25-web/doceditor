// PDF.js viewer (v3, classic script)
(function () {
    let pdfDoc = null;
    let currentPage = 1;
    let totalPages = 0;
    let currentScale = 1.5;
    let placingText = false;
    let listenersAttached = false;

    window.initPdfViewer = function () {
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

        const pdfCanvas = document.getElementById('pdf-canvas');
        const ctx = pdfCanvas.getContext('2d');
        currentPage = 1;
        pdfDoc = null;

        async function loadPdf() {
            const url = API_BASE + `/api/pdf/${FILE_ID}/serve?t=${Date.now()}`;
            pdfDoc = await pdfjsLib.getDocument(url).promise;
            totalPages = pdfDoc.numPages;
            if (currentPage > totalPages) currentPage = totalPages;
            await renderPage(currentPage);
        }

        async function renderPage(num) {
            const page = await pdfDoc.getPage(num);
            const viewport = page.getViewport({ scale: currentScale });
            pdfCanvas.width = viewport.width;
            pdfCanvas.height = viewport.height;
            await page.render({ canvasContext: ctx, viewport }).promise;
            document.getElementById('page-info').textContent = `Seite ${num} / ${totalPages}`;

            const annoCanvas = document.getElementById('annotation-canvas');
            annoCanvas.width = viewport.width;
            annoCanvas.height = viewport.height;
            annoCanvas.style.width = viewport.width + 'px';
            annoCanvas.style.height = viewport.height + 'px';

            if (window.onPdfPageRendered) {
                window.onPdfPageRendered(viewport.width, viewport.height);
            }
        }

        if (!listenersAttached) {
            listenersAttached = true;

            document.getElementById('prev-page').addEventListener('click', () => {
                if (currentPage > 1) { currentPage--; renderPage(currentPage); }
            });

            document.getElementById('next-page').addEventListener('click', () => {
                if (currentPage < totalPages) { currentPage++; renderPage(currentPage); }
            });

            document.getElementById('rotate-page-btn').addEventListener('click', () => {
                fetch(API_BASE + `/api/pdf/${FILE_ID}/rotate-page`, {
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
                fetch(API_BASE + `/api/pdf/${FILE_ID}/delete-page`, {
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

            // Floating text preview element
            let textGhost = null;

            function createTextGhost(text, fontSize, color) {
                if (textGhost) textGhost.remove();
                textGhost = document.createElement('div');
                textGhost.textContent = text;
                textGhost.style.cssText = `position:fixed;pointer-events:none;z-index:9999;
                    font-size:${fontSize}px;color:${color};white-space:nowrap;opacity:0.7;
                    font-family:Helvetica,Arial,sans-serif;transform:translate(8px,8px);`;
                document.body.appendChild(textGhost);
            }

            function moveTextGhost(e) {
                if (textGhost) {
                    textGhost.style.left = e.clientX + 'px';
                    textGhost.style.top = e.clientY + 'px';
                }
            }

            function removeTextGhost() {
                if (textGhost) { textGhost.remove(); textGhost = null; }
                document.removeEventListener('mousemove', moveTextGhost);
            }

            document.getElementById('pdf-enhance-btn').addEventListener('click', () => {
                const btn = document.getElementById('pdf-enhance-btn');
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Läuft...';
                const enhance = {
                    deskew: document.getElementById('pdf-enhance-deskew').checked,
                    sharpen: document.getElementById('pdf-enhance-sharpen').checked,
                    contrast: document.getElementById('pdf-enhance-contrast').checked,
                    threshold: document.getElementById('pdf-enhance-threshold').checked,
                };
                fetch(API_BASE + `/api/pdf/${FILE_ID}/enhance`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enhance }),
                })
                .then(r => r.json())
                .then(data => {
                    if (data.error) { alert(data.error); return; }
                    loadPdf();
                    if (window.refreshVersions) window.refreshVersions();
                })
                .catch(() => alert('Fehler bei der Verbesserung'))
                .finally(() => {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="bi bi-stars"></i> Verbessern';
                });
            });

            document.getElementById('place-text-overlay').addEventListener('click', () => {
                const text = document.getElementById('text-overlay-input').value.trim();
                if (!text) { alert('Bitte Text eingeben'); return; }
                placingText = true;
                document.getElementById('pdf-container').style.cursor = 'none';
                if (window._setAnnotationPassthrough) window._setAnnotationPassthrough(true);
                const fontSize = parseInt(document.getElementById('text-overlay-size').value) || 14;
                const color = document.getElementById('anno-color').value;
                createTextGhost(text, fontSize, color);
                document.addEventListener('mousemove', moveTextGhost);
            });

            // Listen on pdf-container (captures clicks on Fabric upper-canvas too)
            document.getElementById('pdf-container').addEventListener('click', (e) => {
                if (!placingText) return;
                placingText = false;
                document.getElementById('pdf-container').style.cursor = '';
                if (window._setAnnotationPassthrough) window._setAnnotationPassthrough(false);
                removeTextGhost();
                const rect = pdfCanvas.getBoundingClientRect();
                // Scale from canvas pixels to PDF points
                const scaleX = pdfCanvas.width / rect.width;
                const x = (e.clientX - rect.left) * scaleX / currentScale;
                const y = (e.clientY - rect.top) * scaleX / currentScale;
                const text = document.getElementById('text-overlay-input').value.trim();
                const fontSize = parseInt(document.getElementById('text-overlay-size').value) || 14;
                const color = hexToRgb(document.getElementById('anno-color').value);

                fetch(API_BASE + `/api/pdf/${FILE_ID}/text-overlay`, {
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
        }

        function hexToRgb(hex) {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? {
                r: parseInt(result[1], 16), g: parseInt(result[2], 16), b: parseInt(result[3], 16)
            } : { r: 0, g: 0, b: 0 };
        }

        window.currentPdfPage = () => currentPage;
        window.reloadPdf = () => loadPdf();

        loadPdf();
    };
})();
