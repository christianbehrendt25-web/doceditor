// Fabric.js overlay for PDF annotation – v2 (annotation store)
(function () {
    let fabricCanvas = null;
    let currentTool = 'select';
    let listenersAttached = false;

    window.initPdfAnnotator = function () {
        currentTool = 'select';
        if (fabricCanvas) { fabricCanvas.dispose(); fabricCanvas = null; }

        window.onPdfPageRendered = function (width, height) {
            if (fabricCanvas) {
                fabricCanvas.dispose();
            }
            fabricCanvas = new fabric.Canvas('annotation-canvas', {
                width: width,
                height: height,
                isDrawingMode: false,
                selection: true,
            });
            if (fabricCanvas.wrapperEl) {
                fabricCanvas.wrapperEl.style.position = 'absolute';
                fabricCanvas.wrapperEl.style.top = '0';
                fabricCanvas.wrapperEl.style.left = '0';
            }
            fabricCanvas.freeDrawingBrush.color = document.getElementById('anno-color').value;
            fabricCanvas.freeDrawingBrush.width = parseInt(document.getElementById('anno-stroke').value) || 2;
            setTool(currentTool);
            loadAnnotationsForPage(window.currentPdfPage() - 1);
        };

        // Allow text-overlay placement to pass through Fabric canvas
        window._setAnnotationPassthrough = function (enabled) {
            if (!fabricCanvas) return;
            const wrapper = fabricCanvas.wrapperEl;
            if (wrapper) {
                wrapper.style.pointerEvents = enabled ? 'none' : '';
            }
        };

        // Expose so version panel can trigger reload after user change
        window.reloadAnnotations = function () {
            if (!fabricCanvas) return;
            loadAnnotationsForPage(window.currentPdfPage() - 1);
        };

        if (!listenersAttached) {
            listenersAttached = true;

            document.querySelectorAll('#annotation-toolbar [data-tool]').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('#annotation-toolbar [data-tool]').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    currentTool = btn.dataset.tool;
                    setTool(currentTool);
                });
            });

            document.getElementById('anno-color').addEventListener('input', (e) => {
                if (fabricCanvas) fabricCanvas.freeDrawingBrush.color = e.target.value;
            });
            document.getElementById('anno-stroke').addEventListener('input', (e) => {
                if (fabricCanvas) fabricCanvas.freeDrawingBrush.width = parseInt(e.target.value) || 2;
            });

            document.getElementById('clear-annotations').addEventListener('click', () => {
                if (fabricCanvas) fabricCanvas.clear();
            });

            document.getElementById('save-annotations').addEventListener('click', () => {
                if (!fabricCanvas || fabricCanvas.getObjects().length === 0) {
                    alert('Keine Annotationen vorhanden');
                    return;
                }
                const user = window.ANNO_USER || 'anonymous';
                const page = window.currentPdfPage() - 1;
                const fabricJson = fabricCanvas.toJSON();

                // Merge with existing annotation data, then PUT
                fetch(API_BASE + `/api/files/${FILE_ID}/annotations/${user}`)
                    .then(r => r.json())
                    .then(existing => {
                        existing.fabric_pages = existing.fabric_pages || {};
                        existing.fabric_pages[String(page)] = fabricJson;
                        return fetch(API_BASE + `/api/files/${FILE_ID}/annotations/${user}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(existing),
                        });
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.error) { alert(data.error); return; }
                        if (window.refreshAnnotationPanel) window.refreshAnnotationPanel();
                    });
            });
        }
    };

    function loadAnnotationsForPage(page) {
        if (!fabricCanvas) return;
        const user = window.ANNO_USER || 'anonymous';

        fetch(API_BASE + `/api/files/${FILE_ID}/annotations/${user}`)
            .then(r => r.json())
            .then(data => {
                fabricCanvas.clear();
                const pageJson = data.fabric_pages && data.fabric_pages[String(page)];
                if (pageJson) {
                    fabricCanvas.loadFromJSON(pageJson, () => {
                        fabricCanvas.getObjects().forEach(obj => obj.set({ selectable: true, evented: true }));
                        fabricCanvas.renderAll();
                        addOtherUsersLayers(page, user);
                    });
                } else {
                    addOtherUsersLayers(page, user);
                }
            });
    }

    function addOtherUsersLayers(page, currentUser) {
        fetch(API_BASE + `/api/files/${FILE_ID}/annotations`)
            .then(r => r.json())
            .then(allAnnotations => {
                allAnnotations.forEach(anno => {
                    if (anno.user === currentUser) return;
                    const pageJson = anno.fabric_pages && anno.fabric_pages[String(page)];
                    if (!pageJson || !pageJson.objects || pageJson.objects.length === 0) return;
                    fabric.util.enlivenObjects(pageJson.objects, (objects) => {
                        objects.forEach(obj => {
                            obj.set({ selectable: false, evented: false, opacity: 0.45 });
                        });
                        fabricCanvas.add(...objects);
                        fabricCanvas.renderAll();
                    });
                });
            });
    }

    function setTool(tool) {
        if (!fabricCanvas) return;
        fabricCanvas.isDrawingMode = (tool === 'draw');
        fabricCanvas.selection = (tool === 'select');
        fabricCanvas.defaultCursor = tool === 'select' ? 'default' : 'crosshair';
        fabricCanvas.off('mouse:down');
        fabricCanvas.off('mouse:move');
        fabricCanvas.off('mouse:up');

        if (tool === 'rect' || tool === 'circle') {
            setupShapeTool(tool);
        } else if (tool === 'text') {
            fabricCanvas.on('mouse:down', (opt) => {
                const pointer = fabricCanvas.getPointer(opt.e);
                const text = new fabric.IText('Text', {
                    left: pointer.x,
                    top: pointer.y,
                    fontSize: 16,
                    fill: document.getElementById('anno-color').value,
                });
                fabricCanvas.add(text);
                fabricCanvas.setActiveObject(text);
                document.querySelector('#annotation-toolbar [data-tool="select"]').click();
            });
        }
    }

    function setupShapeTool(shape) {
        let isDrawing = false, origin, shapeObj;
        fabricCanvas.on('mouse:down', (opt) => {
            isDrawing = true;
            origin = fabricCanvas.getPointer(opt.e);
            const color = document.getElementById('anno-color').value;
            const stroke = parseInt(document.getElementById('anno-stroke').value) || 2;
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
})();
