# wagtail-image-directories

**Voegt jaar/slug-metadata en een visuele Image Navigator toe aan het Wagtail-afbeeldingsmodel. Nieuwe originelen kunnen worden opgeslagen in `images/<year>/<slug>/`, met behoud van Wagtail-collecties en bulkbewerkingen.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Belangrijkste functies

- Mappen bekijken met aantallen, geschatte opslag en paginering.
- Bestanden in batches uploaden met limieten voor grootte, aantal en gedecodeerde pixels.
- Mappen en afbeeldingsgroepen maken, hernoemen, samenvoegen, verplaatsen of verwijderen met rechtencontroles.
- De mappenstructuur spiegelen in Wagtail-collecties.

## Vereisten en compatibiliteit

- Gedeclareerde afhankelijkheden: `Wagtail >= 6.0`.
- Controleer de compatibiliteit van Python, Django en Wagtail gezamenlijk. De minimale pakketafhankelijkheid bewijst niet dat alle versies worden ondersteund.

De pakketmetadata vermeldt Wagtail >= 6.0, maar een minimale afhankelijkheid bewijst geen compatibiliteit. Dit archief bevat geen volledige geautomatiseerde matrix voor alle Django/Wagtail-combinaties. Test vóór een productie-upgrade de exacte versies, database, opslagbackend en deploymentinstellingen in staging.

## Installatie

Installeer het pakket in dezelfde virtuele omgeving als je Wagtail-project:

```bash
pip install wagtail-image-directories
```

Voeg de apps in deze volgorde toe en behoud de overige projectafhankelijkheden:

```python
INSTALLED_APPS = [
    # Behoud ook de overige Django/Wagtail-afhankelijkheden die het project nodig heeft.
    "wagtail.images",
    "wagtail_image_directories",
]
```

Maak een concreet afbeeldingsmodel op basis van `AbstractDirectoryImage` en configureer beide modelinstellingen. Het volledige voorbeeld staat in de Engelse README.



## Eerste configuratie

Minimaal startvoorbeeld. Pas modelnamen, API-velden en URL’s aan je configuratie aan.

```python
# Vervang "media" door de naam van uw Django-app.
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

Maak en voer daarna migraties uit voor de app met het concrete model en voer `python manage.py migrate` uit. Dit wijzigt alleen het pad van nieuwe uploads en verplaatst geen bestaande mediabestanden.


## Belangrijke instellingen en gedrag

De Engelse README in deze map is de canonieke referentie met volledige instellingstabellen en uitgebreide voorbeelden. Deze vertaling behandelt de praktische installatie en de belangrijkste veiligheidswaarschuwingen; raadpleeg de Engelse referentie voordat je geavanceerde instellingen wijzigt.

Raadpleeg de [Engelse README](README.md) voor het volledige instellingenoverzicht.

### Belangrijke aandachtspunten

Nieuwe bestanden gebruiken `images/<year>/<slug>/`; de migratie verplaatst bestaande originelen niet. Het pakket maakt geen crops, dus beperk rendition-specificaties apart op basis van de schijfquota.

## Beveiliging en beheer

- Houd afhankelijkheden bijgewerkt. Gebruik voor door gebruikers geschreven HTML het bedoelde opschonings- en renderpad; geef opgeslagen reacties of forumberichten niet onvoorwaardelijk weer met `|safe`.
- Controleer migraties en rechten met gewone, beperkte gebruikers, moderators en beheerders.
- Test bij meerdere sites elk ingesteld domein en een onbekende host. Als geen Site wordt gevonden, mag een query niet worden verbreed naar records van alle sites.
- Behandel API-tokens, SMTP-inloggegevens en privé-URL’s als geheimen. Commit ze niet naar Git en vermeld ze niet in openbare bugrapporten.
- Maak een back-up van database en mediabestanden vóór migraties, bulkverplaatsingen, imports of de eerste bulkpublicatie. Test zulke handelingen eerst in staging.

## Aanbevolen combinaties

- `wagtail-prose-editor-images` voegt de Prose-afbeeldingskiezer toe; `wagtail-desktop-publisher` past bij Markdown als het uploadendpoint is geïntegreerd.
- Reacties en forum staan los van dit pakket.

## Controlelijst

- [ ] Installeer de kandidaat in staging en noteer de Python-, Django-, Wagtail- en databaseversies.
- [ ] Voer `python manage.py check` en de pakketmigraties uit.
- [ ] Test de hoofdworkflow met een gewone en beperkte gebruiker.
- [ ] Controleer logs, toegang, caching, back-ups en herstel.

Het archief slaagt voor statische syntax- en packagingcontroles, maar volledige Django/Wagtail-runtime-integratie is hier niet uitgevoerd. Beschouw de lijst hieronder als vrijgavevoorwaarde, niet als bewijs dat elke combinatie is getest.

## Probleemoplossing

Als de workflow niet werkt, controleer appconfiguratie, migraties, URL-volgorde, gebruikersrechten en Django-logs. Vergelijk pakketversie en voorbeeld met de Engelse README.

## Licentie en ondersteuning

MIT. Broncode: [https://github.com/vovansrnd/wagtail-image-directories](https://github.com/vovansrnd/wagtail-image-directories).

