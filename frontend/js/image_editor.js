// Image editor with Fabric.js
(function () {
    let fabricCanvas = null;
    let baseImage = null;
    let currentTool = 'select';
    let cropRect = null;
    let listenersAttached = false;

    window.initImageEditor = function () {
        currentTool = 'select';
        if (fabricCanvas) { fabricCanvas.dispose(); fabricCanvas = null; }
        baseImage = null;
        cropRect = null;

        loadImage();

        if (!listenersAttached) {
            listenersAttached = true;

            document.querySelectorAll('#image-tools [data-tool]').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('#image-tools [data-tool]').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    currentTool = btn.dataset.tool;
                    setTool(currentTool);
                });
            });

            document.getElementById('apply-crop').addEventListener('click', () => {
                if (!cropRect || !baseImage) return;
                const scale = baseImage.scaleX;
                const left = Math.round(cropRect.left / scale);
                const top = Math.round(cropRect.top / scale);
                const right = left + Math.round(cropRect.width / scale);
                const bottom = top + Math.round(cropRect.height / scale);

                fetch(API_BASE + `/api/image/${FILE_ID}/crop`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ left, top, right, bottom }),
                })
                .then(r => r.json())
                .then(data => {
                    if (data.error) { alert(data.error); return; }
                    loadImage();
                    if (window.refreshVersions) window.refreshVersions();
                });
            });

            document.getElementById('cancel-crop').addEventListener('click', () => {
                if (cropRect && fabricCanvas) { fabricCanvas.remove(cropRect); cropRect = null; }
                document.querySelector('#image-tools [data-tool="select"]').click();
            });

            document.getElementById('rotate-left').addEventListener('click', () => {
                fetch(API_BASE + `/api/image/${FILE_ID}/rotate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ angle: -90 }),
                }).then(r => r.json()).then(data => {
                    if (data.error) { alert(data.error); return; }
                    loadImage();
                    if (window.refreshVersions) window.refreshVersions();
                });
            });

            document.getElementById('rotate-right').addEventListener('click', () => {
                fetch(API_BASE + `/api/image/${FILE_ID}/rotate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ angle: 90 }),
                }).then(r => r.json()).then(data => {
                    if (data.error) { alert(data.error); return; }
                    loadImage();
                    if (window.refreshVersions) window.refreshVersions();
                });
            });

            document.getElementById('resize-btn').addEventListener('click', () => {
                document.getElementById('resize-controls').style.display = '';
                if (baseImage) {
                    document.getElementById('resize-w').value = Math.round(baseImage.width);
                    document.getElementById('resize-h').value = Math.round(baseImage.height);
                }
            });

            document.getElementById('cancel-resize').addEventListener('click', () => {
                document.getElementById('resize-controls').style.display = 'none';
            });

            document.getElementById('apply-resize').addEventListener('click', () => {
                const w = parseInt(document.getElementById('resize-w').value);
                const h = parseInt(document.getElementById('resize-h').value);
                if (!w || !h) return;
                fetch(API_BASE + `/api/image/${FILE_ID}/resize`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ width: w, height: h }),
                }).then(r => r.json()).then(data => {
                    if (data.error) { alert(data.error); return; }
                    document.getElementById('resize-controls').style.display = 'none';
                    loadImage();
                    if (window.refreshVersions) window.refreshVersions();
                });
            });

            document.getElementById('apply-filters').addEventListener('click', () => {
                const brightness = parseFloat(document.getElementById('brightness').value);
                const contrast = parseFloat(document.getElementById('contrast').value);
                const saturation = parseFloat(document.getElementById('saturation').value);
                fetch(API_BASE + `/api/image/${FILE_ID}/adjust`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ brightness, contrast, saturation }),
                }).then(r => r.json()).then(data => {
                    if (data.error) { alert(data.error); return; }
                    document.getElementById('brightness').value = 1;
                    document.getElementById('contrast').value = 1;
                    document.getElementById('saturation').value = 1;
                    loadImage();
                    if (window.refreshVersions) window.refreshVersions();
                });
            });

            document.getElementById('draw-color').addEventListener('input', (e) => {
                if (fabricCanvas) fabricCanvas.freeDrawingBrush.color = e.target.value;
            });
            document.getElementById('draw-stroke').addEventListener('input', (e) => {
                if (fabricCanvas) fabricCanvas.freeDrawingBrush.width = parseInt(e.target.value) || 2;
            });

            document.getElementById('clear-objects').addEventListener('click', () => {
                if (!fabricCanvas) return;
                const objects = fabricCanvas.getObjects().filter(o => o !== baseImage);
                objects.forEach(o => fabricCanvas.remove(o));
            });

            document.getElementById('save-image').addEventListener('click', () => {
                if (!fabricCanvas || !baseImage) return;
                const objects = fabricCanvas.getObjects().filter(o => o !== baseImage);
                if (objects.length === 0) {
                    alert('Keine Annotierungen vorhanden');
                    return;
                }
                fabricCanvas.remove(baseImage);
                const dataUrl = fabricCanvas.toDataURL({ format: 'png' });
                fabricCanvas.add(baseImage);
                fabricCanvas.sendToBack(baseImage);

                fetch(API_BASE + `/api/image/${FILE_ID}/annotate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ overlay: dataUrl }),
                }).then(r => r.json()).then(data => {
                    if (data.error) { alert(data.error); return; }
                    loadImage();
                    if (window.refreshVersions) window.refreshVersions();
                });
            });
        }
    };

    function loadImage() {
        const url = API_BASE + `/api/image/${FILE_ID}/serve?t=${Date.now()}`;
        fabric.Image.fromURL(url, (img) => {
            baseImage = img;
            const maxW = window.innerWidth * 0.6;
            let scale = 1;
            if (img.width > maxW) scale = maxW / img.width;

            if (fabricCanvas) fabricCanvas.dispose();
            fabricCanvas = new fabric.Canvas('image-canvas', {
                width: img.width * scale,
                height: img.height * scale,
                isDrawingMode: false,
            });

            img.set({ left: 0, top: 0, scaleX: scale, scaleY: scale, selectable: false, evented: false });
            fabricCanvas.add(img);
            fabricCanvas.sendToBack(img);

            fabricCanvas.freeDrawingBrush.color = document.getElementById('draw-color').value;
            fabricCanvas.freeDrawingBrush.width = parseInt(document.getElementById('draw-stroke').value) || 2;
            setTool(currentTool);
        }, { crossOrigin: 'anonymous' });
    }

    function setTool(tool) {
        if (!fabricCanvas) return;
        fabricCanvas.isDrawingMode = (tool === 'draw');
        fabricCanvas.selection = (tool === 'select');
        fabricCanvas.off('mouse:down');
        fabricCanvas.off('mouse:move');
        fabricCanvas.off('mouse:up');

        document.getElementById('crop-controls').style.display = (tool === 'crop') ? '' : 'none';

        if (tool === 'crop') {
            setupCropTool();
        } else if (tool === 'rect' || tool === 'circle') {
            setupShapeTool(tool);
        } else if (tool === 'textbox') {
            fabricCanvas.on('mouse:down', (opt) => {
                const pointer = fabricCanvas.getPointer(opt.e);
                const text = new fabric.IText('Text', {
                    left: pointer.x, top: pointer.y, fontSize: 20,
                    fill: document.getElementById('draw-color').value,
                });
                fabricCanvas.add(text);
                fabricCanvas.setActiveObject(text);
                document.querySelector('#image-tools [data-tool="select"]').click();
            });
        }
    }

    function setupShapeTool(shape) {
        let isDrawing = false, origin, shapeObj;
        fabricCanvas.on('mouse:down', (opt) => {
            isDrawing = true;
            origin = fabricCanvas.getPointer(opt.e);
            const color = document.getElementById('draw-color').value;
            const stroke = parseInt(document.getElementById('draw-stroke').value) || 2;
            if (shape === 'rect') {
                shapeObj = new fabric.Rect({
                    left: origin.x, top: origin.y, width: 0, height: 0,
                    fill: 'transparent', stroke: color, strokeWidth: stroke,
                });
            } else {
                shapeObj = new fabric.Ellipse({
                    left: origin.x, top: origin.y, rx: 0, ry: 0,
                    fill: 'transparent', stroke: color, strokeWidth: stroke,
                });
            }
            fabricCanvas.add(shapeObj);
        });
        fabricCanvas.on('mouse:move', (opt) => {
            if (!isDrawing) return;
            const pointer = fabricCanvas.getPointer(opt.e);
            if (shape === 'rect') {
                shapeObj.set({
                    width: Math.abs(pointer.x - origin.x),
                    height: Math.abs(pointer.y - origin.y),
                    left: Math.min(pointer.x, origin.x),
                    top: Math.min(pointer.y, origin.y),
                });
            } else {
                shapeObj.set({
                    rx: Math.abs(pointer.x - origin.x) / 2,
                    ry: Math.abs(pointer.y - origin.y) / 2,
                    left: Math.min(pointer.x, origin.x),
                    top: Math.min(pointer.y, origin.y),
                });
            }
            fabricCanvas.renderAll();
        });
        fabricCanvas.on('mouse:up', () => { isDrawing = false; });
    }

    function setupCropTool() {
        if (cropRect && fabricCanvas) { fabricCanvas.remove(cropRect); cropRect = null; }
        let isDrawing = false, origin;
        fabricCanvas.on('mouse:down', (opt) => {
            if (cropRect) { fabricCanvas.remove(cropRect); }
            isDrawing = true;
            origin = fabricCanvas.getPointer(opt.e);
            cropRect = new fabric.Rect({
                left: origin.x, top: origin.y, width: 0, height: 0,
                fill: 'rgba(0,123,255,0.1)', stroke: '#007bff', strokeWidth: 2,
                strokeDashArray: [5, 5], selectable: true,
            });
            fabricCanvas.add(cropRect);
        });
        fabricCanvas.on('mouse:move', (opt) => {
            if (!isDrawing) return;
            const pointer = fabricCanvas.getPointer(opt.e);
            cropRect.set({
                width: Math.abs(pointer.x - origin.x),
                height: Math.abs(pointer.y - origin.y),
                left: Math.min(pointer.x, origin.x),
                top: Math.min(pointer.y, origin.y),
            });
            fabricCanvas.renderAll();
        });
        fabricCanvas.on('mouse:up', () => { isDrawing = false; });
    }
})();
