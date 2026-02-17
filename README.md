# DocEditor

Nicht-destruktiver PDF- und Bild-Editor im Browser. Originaldateien bleiben immer erhalten – jede Bearbeitung erzeugt eine neue Version. Ein Audit-Log protokolliert alle Aktionen.

## Monorepo-Struktur

```
doceditor/
├── frontend/                   # Reine SPA, kein Server-Templating
│   ├── index.html              # Single Page mit Hash-Router
│   ├── css/main.css
│   └── js/
│       ├── app.js              # Router + API_BASE Config
│       ├── file_browser.js
│       ├── pdf_viewer.js
│       ├── pdf_annotator.js
│       ├── image_editor.js
│       └── version_panel.js
├── spec/
│   └── openapi.yaml            # Komplette API-Spezifikation
├── backend-python/             # Flask-Implementierung
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── models/                 # Framework-agnostische Business-Logik
│   ├── routes/                 # Reine API-Routes (kein Template-Rendering)
│   └── storage/
├── README.md
└── .gitignore
```

**Frontend und Backend sind entkoppelt.** Das Frontend ist eine eigenstaendige SPA mit Hash-Router (`#/`, `#/pdf/{id}`, `#/image/{id}`). Alle API-Aufrufe nutzen die konfigurierbare `API_BASE`-Variable. Die API ist per OpenAPI-Spec in `spec/openapi.yaml` definiert – das Backend kann in jeder Sprache implementiert werden.

## Features

**PDF:**
- Anzeige im Browser (PDF.js)
- Seiten drehen, loeschen, umsortieren
- PDFs zusammenfuegen (Merge)
- Text-Overlay (Vektor, scharf bei jedem Zoom)
- Freihand-Annotationen, Rechtecke, Kreise, Text (Fabric.js)

**Bilder:**
- Zuschnitt, Groessenaenderung, Rotation
- Helligkeit, Kontrast, Saettigung
- Freihand-Zeichnen, Formen, Text (Fabric.js)

**Allgemein:**
- Vollstaendige Versionshistorie mit Revert
- Download jeder einzelnen Version
- JSONL Audit-Log (append-only)
- Kein Account noetig (MVP ohne Auth)

## Schnellstart (Python-Backend)

```bash
cd backend-python
pip install -r requirements.txt
python3 app.py
```

Dann im Browser: http://localhost:5000

Das Backend liefert das Frontend aus `frontend/` automatisch als statische Dateien aus.

## Frontend separat hosten

Das Frontend kann auch von einem eigenen Webserver (z.B. nginx, Apache, `python3 -m http.server`) ausgeliefert werden. Dazu in `frontend/js/app.js` die `API_BASE`-Variable setzen:

```javascript
window.API_BASE = "http://localhost:5000";  // oder anderer Backend-Server
```

## Einbindung in ein bestehendes Flask-Projekt

```python
import sys
sys.path.insert(0, "doceditor/backend-python")
from app import register_blueprints

register_blueprints(app, url_prefix="/doceditor")
```

DocEditor-API ist dann unter `/doceditor/api/...` erreichbar. Das Frontend muss mit `API_BASE = "/doceditor"` konfiguriert werden.

## Konfiguration

| Umgebungsvariable    | Beschreibung                          | Default              |
|----------------------|---------------------------------------|----------------------|
| `DOCEDITOR_STORAGE`  | Pfad zum Storage-Verzeichnis          | `./storage`          |
| `DOCEDITOR_PREFIX`   | URL-Prefix fuer alle API-Routen       | _(leer = Root)_      |

## API

Die vollstaendige API-Spezifikation befindet sich in [`spec/openapi.yaml`](spec/openapi.yaml).

| Methode  | Endpunkt                              | Beschreibung                    |
|----------|---------------------------------------|---------------------------------|
| `GET`    | `/api/files`                          | Alle Dateien auflisten          |
| `POST`   | `/api/files/upload`                   | Datei hochladen (multipart)     |
| `GET`    | `/api/files/<id>`                     | Datei-Metadaten                 |
| `DELETE` | `/api/files/<id>`                     | Datei loeschen                  |
| `GET`    | `/api/files/<id>/download[/<version>]`| Datei herunterladen             |
| `GET`    | `/api/files/<id>/versions`            | Versionshistorie                |
| `POST`   | `/api/files/<id>/revert/<version>`    | Auf Version zuruecksetzen       |
| `GET`    | `/api/audit-log`                      | Audit-Log abrufen               |
| `GET`    | `/api/pdf/<id>/serve`                 | PDF ausliefern                  |
| `GET`    | `/api/pdf/<id>/page-count`            | Seitenanzahl                    |
| `POST`   | `/api/pdf/<id>/rotate-page`           | Seite drehen                    |
| `POST`   | `/api/pdf/<id>/delete-page`           | Seite loeschen                  |
| `POST`   | `/api/pdf/<id>/reorder-pages`         | Seiten umsortieren              |
| `POST`   | `/api/pdf/<id>/text-overlay`          | Text auf Seite platzieren       |
| `POST`   | `/api/pdf/<id>/annotate`              | PNG-Overlay auf Seite stempeln  |
| `POST`   | `/api/pdf/merge`                      | Mehrere PDFs zusammenfuegen     |
| `GET`    | `/api/image/<id>/serve`               | Bild ausliefern                 |
| `POST`   | `/api/image/<id>/crop`                | Zuschneiden                     |
| `POST`   | `/api/image/<id>/resize`              | Groesse aendern                 |
| `POST`   | `/api/image/<id>/rotate`              | Drehen                          |
| `POST`   | `/api/image/<id>/adjust`              | Helligkeit/Kontrast/Saettigung  |
| `POST`   | `/api/image/<id>/annotate`            | PNG-Overlay compositen          |

## Tech Stack

- **Backend:** Flask, pikepdf, reportlab, Pillow
- **Frontend:** PDF.js, Fabric.js, Bootstrap 5 (eigenstaendige SPA)
- **Storage:** Lokales Dateisystem, JSON-Metadaten, JSONL-Audit-Log
- **API-Spec:** OpenAPI 3.0
