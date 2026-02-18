# DocEditor

Nicht-destruktiver PDF- und Bild-Editor im Browser. Originaldateien bleiben immer erhalten. Strukturelle Bearbeitungen (Drehen, Seiten loeschen, Merge …) werden in einer separaten `current/`-Datei gespeichert. Annotationen (Freihand, Formen, Text-Overlays) werden pro Nutzer als JSON abgelegt – nie in die PDF gebacken – und koennen beim Export gezielt eingeblendet werden.

## Storage-Modell

```
storage/
  originals/<id>.<ext>          # unveraenderlich (Authentizitaetsnachweis)
  current/<id>.<ext>            # nur wenn strukturell bearbeitet
  annotations/<id>/<user>.json  # eine Schicht pro Nutzer
```

**Annotation-JSON** (pro User pro Datei):
```json
{
  "user": "user1",
  "updated_at": "2026-02-18T...",
  "fabric_pages": {
    "0": { /* Fabric.js canvas JSON */ }
  },
  "text_overlays": [
    { "page": 0, "text": "...", "x": 100, "y": 200,
      "font_size": 12, "font_name": "Helvetica", "color": [0,0,0] }
  ]
}
```

## Monorepo-Struktur

```
doceditor/
├── frontend/                       # Reine SPA, kein Server-Templating
│   ├── index.html
│   ├── css/main.css
│   └── js/
│       ├── app.js                  # Router + API_BASE Config
│       ├── file_browser.js
│       ├── pdf_viewer.js
│       ├── pdf_annotator.js        # Fabric.js-Overlay, laedt/speichert Annotation-Layer
│       ├── image_editor.js
│       └── version_panel.js        # Export- & Info-Panel (User-Selector, Layer, Download)
├── backend-python/
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── migrate_v1_to_v2.py         # Einmalige Migration vom alten Versionsmodell
│   ├── models/
│   │   ├── annotation_store.py     # Lesen/Schreiben der JSON-Layer
│   │   ├── version_store.py        # originals/ + current/ verwalten
│   │   ├── file_manager.py         # Business-Logik
│   │   ├── pdf_processor.py
│   │   ├── image_processor.py
│   │   └── ...
│   ├── routes/
│   │   ├── annotation_routes.py    # GET/PUT/DELETE /api/files/<id>/annotations/…
│   │   ├── files.py
│   │   ├── pdf_routes.py
│   │   └── ...
│   └── storage/
└── README.md
```

## Features

**PDF:**
- Anzeige im Browser (PDF.js)
- Seiten drehen, loeschen, umsortieren
- PDFs zusammenfuegen (Merge)
- Seiten verbessern (Entzerren, Schaerfe, Kontrast – fuer Scans)
- Text-Overlay als Annotation speichern (Vektor, scharf bei jedem Zoom)
- Freihand-Annotationen, Rechtecke, Kreise, Text (Fabric.js)

**Multi-User-Annotationen:**
- Jeder Nutzer hat einen eigenen Layer (`annotations/<id>/<user>.json`)
- Andere Nutzer-Layer werden im Viewer als halb-transparente, nicht-editierbare Objekte eingeblendet
- Beim Export waehlen, welche Layer eingeblendet werden sollen
- Fabric-Canvases werden client-seitig zu PNG gerendert und mit Text-Overlays zusammengefuehrt

**Bilder:**
- Zuschnitt, Groessenaenderung, Rotation
- Helligkeit, Kontrast, Saettigung
- Freihand-Zeichnen, Formen, Text (Fabric.js, direkt in Bild gebacken)

**Allgemein:**
- Originaldatei immer unveraendert
- Auf Original zuruecksetzen (loescht current + alle Annotation-Layer)
- Download: Original / Aktuell (ohne Annotationen) / Mit Annotationen (Export)
- Audit-Log fuer alle Aktionen (SQLite)
- Kein Account noetig (MVP ohne Auth)

## Schnellstart (Python-Backend)

```bash
cd backend-python
pip install -r requirements.txt
python3 app.py
```

Dann im Browser: http://localhost:5000

Das Backend liefert das Frontend aus `frontend/` automatisch als statische Dateien aus.

### Migration vom alten Versionsmodell (v1 → v2)

Falls eine bestehende Datenbank mit dem alten `FileVersion`-Modell vorhanden ist:

```bash
cd backend-python
python3 migrate_v1_to_v2.py
```

Das Skript kopiert die jeweils hoechste Version jeder Datei nach `current/`, entfernt die `file_versions`-Tabelle und bereinigt das `versions/`-Verzeichnis.

## Frontend separat hosten

Das Frontend kann auch von einem eigenen Webserver (nginx, Apache, `python3 -m http.server`) ausgeliefert werden. Dazu in `frontend/js/app.js`:

```javascript
window.API_BASE = "http://localhost:5000";
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
| `DATABASE_URL`       | SQLAlchemy-URL                        | SQLite in storage/   |

## API

### Dateien

| Methode  | Endpunkt                                  | Beschreibung                              |
|----------|-------------------------------------------|-------------------------------------------|
| `GET`    | `/api/files`                              | Alle Dateien auflisten                    |
| `POST`   | `/api/files/upload`                       | Datei hochladen (multipart)               |
| `GET`    | `/api/files/<id>`                         | Datei-Metadaten                           |
| `DELETE` | `/api/files/<id>`                         | Datei loeschen                            |
| `GET`    | `/api/files/<id>/download?mode=original\|current` | Datei herunterladen              |
| `POST`   | `/api/files/<id>/export-annotated`        | PDF mit gewaehlten Layers exportieren     |
| `POST`   | `/api/files/<id>/reset`                   | Auf Original zuruecksetzen                |
| `GET`    | `/api/audit-log`                          | Audit-Log abrufen                         |

### Annotationen

| Methode  | Endpunkt                                  | Beschreibung                              |
|----------|-------------------------------------------|-------------------------------------------|
| `GET`    | `/api/files/<id>/annotations`             | Alle Layer (alle Nutzer)                  |
| `GET`    | `/api/files/<id>/annotations/<user>`      | Layer eines Nutzers laden                 |
| `PUT`    | `/api/files/<id>/annotations/<user>`      | Layer eines Nutzers speichern             |
| `DELETE` | `/api/files/<id>/annotations/<user>`      | Layer eines Nutzers loeschen              |

### PDF

| Methode  | Endpunkt                          | Beschreibung                              |
|----------|-----------------------------------|-------------------------------------------|
| `GET`    | `/api/pdf/<id>/serve`             | PDF ausliefern (aktuelle Version)         |
| `GET`    | `/api/pdf/<id>/page-count`        | Seitenanzahl                              |
| `POST`   | `/api/pdf/<id>/rotate-page`       | Seite drehen                              |
| `POST`   | `/api/pdf/<id>/delete-page`       | Seite loeschen                            |
| `POST`   | `/api/pdf/<id>/reorder-pages`     | Seiten umsortieren                        |
| `POST`   | `/api/pdf/<id>/text-overlay`      | Text-Overlay als Annotation speichern     |
| `POST`   | `/api/pdf/<id>/annotate`          | Fabric-JSON als Annotation speichern      |
| `POST`   | `/api/pdf/<id>/enhance`           | Seiten verbessern (Scan-Optimierung)      |
| `POST`   | `/api/pdf/merge`                  | Mehrere PDFs zusammenfuegen               |
| `POST`   | `/api/photo-to-pdf`               | Bilder zu PDF konvertieren                |

### Bilder

| Methode  | Endpunkt                          | Beschreibung                              |
|----------|-----------------------------------|-------------------------------------------|
| `GET`    | `/api/image/<id>/serve`           | Bild ausliefern                           |
| `POST`   | `/api/image/<id>/crop`            | Zuschneiden                               |
| `POST`   | `/api/image/<id>/resize`          | Groesse aendern                           |
| `POST`   | `/api/image/<id>/rotate`          | Drehen                                    |
| `POST`   | `/api/image/<id>/adjust`          | Helligkeit/Kontrast/Saettigung            |
| `POST`   | `/api/image/<id>/annotate`        | PNG-Overlay compositen                    |

## Tech Stack

- **Backend:** Flask, SQLAlchemy (SQLite/PostgreSQL/MySQL), pikepdf, reportlab, Pillow, OpenCV, PyMuPDF
- **Frontend:** PDF.js, Fabric.js, Bootstrap 5 (eigenstaendige SPA)
- **Storage:** Lokales Dateisystem + SQLite (Audit-Log)
