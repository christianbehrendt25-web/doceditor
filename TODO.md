# DocEditor - TODO

## 1. DB-Backend (SQLAlchemy) ← AKTUELL
VersionStore + AuditLogger auf SQLAlchemy umstellen.
Universell: SQLite (Default/Dev), PostgreSQL, MySQL ueber DATABASE_URL.
Dateien bleiben im Dateisystem, nur Metadaten + Audit-Log in die DB.

## 2. Foto-zu-PDF Konvertierung
Fotos von Dokumenten in PDF wandeln mit Bildverbesserung:
- Begradigung (Deskewing)
- Schaerfe verbessern
- Lesbarkeit optimieren (Kontrast, Schwellwert)
- Mehrere Fotos zu mehrseitigem PDF zusammenfassen (konfigurierbar)

## 3. OCR
Texterkennung fuer gescannte Dokumente / Fotos.
Schritt 1: Unsichtbare Textebene im PDF (durchsuchbar).
Schritt 2: Text extrahieren/exportieren.

## 4. Annotationen verfeinern
Erste Erweiterungen:
- Pfeil-Formen
- Haekchen
Spaeter: Highlight-Marker, Stempel, Linien, Radierer.

## 5. Kommentarsection
- Kommentarliste pro Datei (ein-/ausblendbar)
- Sticky Notes positioniert auf der Seite

## 6. Bearbeitungsstatus
Einfache Stufen: Entwurf → In Bearbeitung → Fertig.
Spaeter ggf. Workflow mit Freigabe/Review.

## 7. Thumbnails in Dateiliste
Vorschaubilder statt nur Dateinamen in der Dateiuebersicht anzeigen.

## 8. PDF-Seitenleiste mit Miniatur-Thumbnails
Alle Seiten eines PDFs als kleine Vorschaubilder in einer Seitenleiste.
Schnelle Navigation per Klick auf Thumbnail.

## 9. Drag & Drop Upload
Dateien direkt aufs Browser-Fenster ziehen zum Hochladen.

## 10. Tagging / Kategorien
Dokumente mit Tags oder Kategorien versehen, filtern und gruppieren.
Ordnerstruktur wird von der Hauptapp uebernommen, nicht von DocEditor.

## 11. Suche
Dokumente nach Name, Tags, Inhalt durchsuchen.
Besonders sinnvoll in Kombination mit OCR.

## 12. Mehrsprachigkeit (i18n)
UI-Texte externalisieren, aktuell alles deutsch hardcoded.
Mindestens DE + EN.

## 13. Mobile / Responsive
UI muss auf mobilen Geraeten funktionieren.
