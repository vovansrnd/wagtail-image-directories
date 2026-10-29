# wagtail-image-directories

**Ergänzt das Wagtail-Bildmodell um Jahr/Slug-Metadaten und einen visuellen Image Navigator. Neue Originale können unter `images/<year>/<slug>/` gespeichert werden; Wagtail-Collections und Stapelaktionen bleiben verfügbar.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Wichtigste Funktionen

- Verzeichnisse mit Bildanzahl, geschätzter Größe und Seitennavigation durchsuchen.
- Stapel-Uploads mit Grenzen für Dateigröße, Anzahl und dekodierte Pixel.
- Verzeichnisse und Bildgruppen mit Berechtigungsprüfungen erstellen, umbenennen, zusammenführen, verschieben oder löschen.
- Verzeichnisstruktur in Wagtail-Collections abbilden.

## Voraussetzungen und Kompatibilität

- Deklarierte Abhängigkeiten: `Wagtail >= 6.0`.
- Die Kompatibilität von Python, Django und Wagtail muss gemeinsam geprüft werden. Die minimale Paketabhängigkeit bestätigt keine Unterstützung jeder Version.

Die Paketmetadaten deklarieren Wagtail >= 6.0. Eine minimale Abhängigkeit ist jedoch kein Kompatibilitätstest. Dieses Quellarchiv enthält keine vollständige automatisierte Matrix für alle Django-/Wagtail-Kombinationen. Prüfen Sie vor einem Produktionsupgrade die konkreten Versionen, Datenbank, Speicher-Backend und Deployment-Einstellungen in einer Staging-Umgebung.

## Installation

Installieren Sie das Paket in derselben virtuellen Umgebung wie Ihr Wagtail-Projekt:

```bash
pip install wagtail-image-directories
```

Fügen Sie die Apps in der angegebenen Reihenfolge hinzu und behalten Sie die übrigen Projektabhängigkeiten bei:

```python
INSTALLED_APPS = [
    # Behalten Sie auch andere bereits benötigte Django-/Wagtail-Abhängigkeiten bei.
    "wagtail.images",
    "wagtail_image_directories",
]
```

Erstellen Sie ein konkretes Bildmodell auf Basis von `AbstractDirectoryImage` und konfigurieren Sie beide Bildmodell-Einstellungen. Das vollständige Beispiel steht in der englischen README.



## Erste Konfiguration

Minimales Einstiegsbeispiel. Passen Sie Modellnamen, API-Felder und URLs an Ihre Konfiguration an.

```python
# Ersetzen Sie "media" durch den Namen Ihrer Django-App.
from django.db import models
from wagtail.images.models import AbstractRendition
from wagtail_image_directories.models import AbstractDirectoryImage

class CustomImage(AbstractDirectoryImage):
    pass

class CustomRendition(AbstractRendition):
    image = models.ForeignKey(CustomImage, on_delete=models.CASCADE, related_name="renditions")
    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)

WAGTAILIMAGES_IMAGE_MODEL = "media.CustomImage"
WAGTAILIMAGES_RENDITION_MODEL = "media.CustomRendition"
```

Erstellen und wenden Sie anschließend Migrationen für die App mit dem konkreten Bildmodell an und führen Sie `python manage.py migrate` aus. Das ändert nur den Pfad neuer Uploads und verschiebt keine vorhandenen Mediendateien.


## Wichtige Einstellungen und Verhalten

Die englische README in diesem Verzeichnis ist die maßgebliche Referenz und enthält vollständige Einstellungstabellen und ausführliche Beispiele. Diese Übersetzung erklärt die praktische Einrichtung und die wichtigsten Sicherheitshinweise; konsultieren Sie vor Änderungen an erweiterten Einstellungen die englische Referenz.

Die vollständige Einstellungsreferenz finden Sie in der [englischen README](README.md).

### Wichtige Hinweise

Neue Dateien erhalten den Pfad `images/<year>/<slug>/`; Migrationen verschieben keine vorhandenen Originale. Das Paket erzeugt keine Crops, daher müssen Rendition-Spezifikationen separat und mit Blick auf die Speicherquote begrenzt werden.

## Sicherheit und Betrieb

- Halten Sie Abhängigkeiten aktuell. Verwenden Sie für nutzererstelltes HTML den vorgesehenen Bereinigungs- und Ausgabepfad; geben Sie gespeicherte Kommentare oder Forenbeiträge nicht bedingungslos mit `|safe` aus.
- Prüfen Sie Migrationen und Berechtigungen mit normalen, eingeschränkten Benutzern, Moderatoren und Administratoren.
- Testen Sie bei mehreren Wagtail-Sites jede konfigurierte Domain sowie einen unbekannten Host. Wenn keine Site gefunden wird, darf eine Abfrage nicht auf Datensätze aller Sites erweitert werden.
- Behandeln Sie API-Tokens, SMTP-Zugangsdaten und private URLs als Geheimnisse. Committen Sie diese nicht in Git und veröffentlichen Sie sie nicht in Fehlerberichten.
- Sichern Sie Datenbank und Mediendateien vor Migrationen, Massenverschiebungen, Importen oder der ersten Massenveröffentlichung. Testen Sie diese Vorgänge zuerst in Staging.

## Empfohlene Kombinationen

- `wagtail-prose-editor-images` ergänzt den Prose-Bilddialog; `wagtail-desktop-publisher` eignet sich für Markdown, wenn der Upload-Endpunkt integriert ist.
- Kommentare und Forum sind unabhängig.

## Checkliste zur Überprüfung

- [ ] Installieren Sie den Kandidaten in Staging und notieren Sie Python-, Django-, Wagtail- und Datenbankversionen.
- [ ] Führen Sie `python manage.py check` und die Paketmigrationen aus.
- [ ] Prüfen Sie den Hauptablauf mit einem normalen und einem eingeschränkten Benutzer.
- [ ] Prüfen Sie Logs, Zugriffskontrolle, Caching, Backups und Wiederherstellung.

Das Archiv besteht statische Syntax- und Packaging-Prüfungen; die vollständige Django-/Wagtail-Laufzeitintegration wurde in dieser Umgebung jedoch nicht getestet. Betrachten Sie die folgende Checkliste als Freigabekriterium und nicht als Behauptung, dass jede Versionskombination getestet wurde.

## Fehlerbehebung

Wenn der Ablauf nicht funktioniert, prüfen Sie App-Konfiguration, Migrationen, URL-Reihenfolge, Benutzerrechte und Django-Logs. Vergleichen Sie Paketversion und Beispiel mit der englischen README.

## Lizenz und Support

MIT. Quellcode: [https://github.com/vovansrnd/wagtail-image-directories](https://github.com/vovansrnd/wagtail-image-directories).

