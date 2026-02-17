# DocEditor

Nicht-destruktiver PDF- und Bild-Editor im Browser. Originaldateien bleiben immer erhalten – jede Bearbeitung erzeugt eine neue Version. Ein Audit-Log protokolliert alle Aktionen.

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

## Schnellstart

```bash
pip install -r requirements.txt
python3 app.py
```

Dann im Browser: http://localhost:5000

## Einbindung in ein bestehendes Flask-Projekt

Als Git-Submodul klonen:

```bash
git submodule add https://github.com/christianbehrendt25-web/doceditor.git doceditor
```

In der bestehenden App registrieren:

```python
import sys
sys.path.insert(0, "doceditor")
from app import register_blueprints

register_blueprints(app, url_prefix="/doceditor")
```

DocEditor ist dann unter `/doceditor/` erreichbar.

## Konfiguration

| Umgebungsvariable    | Beschreibung                          | Default              |
|----------------------|---------------------------------------|----------------------|
| `DOCEDITOR_STORAGE`  | Pfad zum Storage-Verzeichnis          | `./storage`          |
| `DOCEDITOR_PREFIX`   | URL-Prefix fuer alle Routen           | _(leer = Root)_      |

## API

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
- **Frontend:** PDF.js, Fabric.js, Bootstrap 5
- **Storage:** Lokales Dateisystem, JSON-Metadaten, JSONL-Audit-Log
