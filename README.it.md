# wagtail-image-directories

**Aggiunge metadati anno/slug e un navigatore visivo al modello immagini Wagtail. I nuovi originali possono essere salvati in `images/<year>/<slug>/`, mantenendo raccolte e operazioni in blocco di Wagtail.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Funzionalità principali

- Sfogliare directory con conteggi, dimensione stimata e paginazione.
- Caricare gruppi con limiti su dimensione, numero di file e pixel decodificati.
- Creare, rinominare, unire, spostare o eliminare gruppi con controlli dei permessi.
- Rispecchiare l’organizzazione nelle raccolte Wagtail.

## Requisiti e compatibilità

- Dipendenze dichiarate: `Wagtail >= 6.0`.
- La compatibilità di Python, Django e Wagtail va verificata congiuntamente. La dipendenza minima del pacchetto non conferma il supporto di tutte le versioni.

I metadati dichiarano Wagtail >= 6.0, ma una dipendenza minima non dimostra la compatibilità. Questo archivio non contiene una matrice automatizzata completa per tutte le combinazioni Django/Wagtail. Prima di aggiornare la produzione, verifica in staging le versioni effettive, il database, lo storage e le impostazioni di deployment.

## Installazione

Installa il pacchetto nello stesso ambiente virtuale del progetto Wagtail:

```bash
pip install wagtail-image-directories
```

Aggiungi le app nell’ordine indicato mantenendo le altre dipendenze del progetto:

```python
INSTALLED_APPS = [
    # Mantieni anche le altre dipendenze Django/Wagtail già necessarie.
    "wagtail.images",
    "wagtail_image_directories",
]
```

Creare un modello immagine concreto derivato da `AbstractDirectoryImage` e configurare entrambe le impostazioni del modello. L’esempio completo è nel README inglese.



## Configurazione iniziale

Esempio minimo per iniziare. Adatta nomi dei modelli, campi API e URL alla tua configurazione.

```python
# Sostituire "media" con il nome della propria app Django.
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

Poi creare e applicare le migrazioni dell’app che contiene il modello concreto ed eseguire `python manage.py migrate`. Cambia solo il percorso dei nuovi upload e non sposta i file multimediali già presenti.


## Impostazioni e comportamento importanti

Il README inglese in questa directory è il riferimento canonico e contiene le tabelle complete delle opzioni e gli esempi estesi. Questa traduzione copre la configurazione pratica e gli avvisi di sicurezza essenziali; consulta il riferimento inglese prima di modificare le opzioni avanzate.

Consulta il [README inglese](README.md) per la tabella completa delle impostazioni.

### Note importanti

I nuovi file usano `images/<year>/<slug>/`; la migrazione non sposta gli originali esistenti. Il pacchetto non crea ritagli, quindi limita separatamente le specifiche rendition in base alla quota disco.

## Sicurezza e operatività

- Mantieni aggiornate le dipendenze. Per l’HTML degli utenti usa il percorso previsto di sanificazione e rendering; non mostrare commenti o post salvati con `|safe` incondizionato.
- Verifica migrazioni e permessi con utenti normali, limitati, moderatori e amministratori.
- Nei progetti multi-sito, verifica ogni dominio configurato e un host sconosciuto. Se non viene trovato un Site, la query non deve estendersi ai record di tutti i siti.
- Tratta token API, credenziali SMTP e URL privati come segreti. Non inserirli in Git né in segnalazioni pubbliche.
- Esegui il backup del database e dei file multimediali prima di migrazioni, spostamenti in blocco, importazioni o pubblicazioni massive iniziali. Prova prima in staging.

## Combinazioni consigliate

- `wagtail-prose-editor-images` aggiunge il selettore Prose; `wagtail-desktop-publisher` serve per Markdown se l’endpoint immagini è integrato.
- Commenti e forum sono indipendenti.

## Lista di verifica

- [ ] Installa la versione candidata in staging e annota le versioni di Python, Django, Wagtail e database.
- [ ] Esegui `python manage.py check` e le migrazioni del pacchetto.
- [ ] Prova il flusso principale con un utente normale e uno limitato.
- [ ] Controlla log, accessi, cache, backup e ripristino.

L’archivio supera i controlli statici di sintassi e packaging, ma in questo ambiente non è stato eseguito un test completo d’integrazione Django/Wagtail. Considera la lista seguente un requisito per il rilascio, non la prova che ogni combinazione sia stata testata.

## Risoluzione dei problemi

Se il flusso non funziona, controlla configurazione dell’app, migrazioni, ordine URL, permessi e log Django. Confronta versione ed esempio con il README inglese.

## Licenza e supporto

MIT. Codice sorgente: [https://github.com/vovansrnd/wagtail-image-directories](https://github.com/vovansrnd/wagtail-image-directories).

