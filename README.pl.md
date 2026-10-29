# wagtail-image-directories

**Dodaje metadane roku/slug i wizualny nawigator do modelu obrazów Wagtail. Nowe oryginały mogą trafiać do `images/<year>/<slug>/`, z zachowaniem kolekcji Wagtail i operacji zbiorczych.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Najważniejsze funkcje

- Przeglądanie katalogów z licznikami, szacowanym rozmiarem i paginacją.
- Przesyłanie partii z limitami rozmiaru, liczby plików i zdekodowanych pikseli.
- Tworzenie, zmiana nazw, łączenie, przenoszenie i usuwanie grup z kontrolą uprawnień.
- Odwzorowanie struktury katalogów w kolekcjach Wagtail.

## Wymagania i zgodność

- Zadeklarowane zależności: `Wagtail >= 6.0`.
- Zgodność Pythona, Django i Wagtail należy sprawdzać łącznie. Minimalna zależność pakietu nie potwierdza obsługi każdej wersji.

Metadane deklarują Wagtail >= 6.0, ale minimalna zależność nie dowodzi zgodności. Archiwum nie zawiera pełnej automatycznej macierzy wszystkich kombinacji Django/Wagtail. Przed aktualizacją produkcji sprawdź dokładne wersje, bazę danych, backend plików i konfigurację wdrożenia na środowisku testowym.

## Instalacja

Zainstaluj pakiet w tym samym środowisku wirtualnym co projekt Wagtail:

```bash
pip install wagtail-image-directories
```

Dodaj aplikacje w tej kolejności, zachowując pozostałe zależności projektu:

```python
INSTALLED_APPS = [
    # Zachowaj również inne zależności Django/Wagtail wymagane przez projekt.
    "wagtail.images",
    "wagtail_image_directories",
]
```

Utwórz konkretny model obrazu dziedziczący po `AbstractDirectoryImage` i skonfiguruj oba ustawienia modelu. Pełny przykład znajduje się w angielskim README.



## Pierwsza konfiguracja

Minimalny przykład na początek. Dostosuj nazwy modeli, pola API i adresy URL do swojej konfiguracji.

```python
# Zastąp "media" nazwą aplikacji Django.
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

Następnie utwórz i zastosuj migracje aplikacji z konkretnym modelem oraz uruchom `python manage.py migrate`. Zmienia to ścieżkę tylko nowych plików i nie przenosi istniejących mediów.


## Ważne ustawienia i zachowanie

Angielski README w tym katalogu jest kanoniczną dokumentacją i zawiera pełne tabele opcji oraz rozszerzone przykłady. To tłumaczenie opisuje praktyczną konfigurację i najważniejsze ostrzeżenia bezpieczeństwa; przed zmianą zaawansowanych opcji sprawdź dokumentację angielską.

Pełną tabelę ustawień znajdziesz w [angielskim README](README.md).

### Ważne uwagi

Nowe pliki trafiają do `images/<year>/<slug>/`; migracja nie przenosi istniejących oryginałów. Pakiet nie generuje kadrów, dlatego ogranicz specyfikacje rendition osobno, uwzględniając limit dysku.

## Bezpieczeństwo i eksploatacja

- Aktualizuj zależności. Dla HTML użytkowników stosuj przewidziany mechanizm oczyszczania i renderowania; nie wyświetlaj zapisanych komentarzy ani postów bezwarunkowo przez `|safe`.
- Sprawdź migracje i uprawnienia jako zwykły, ograniczony użytkownik, moderator i administrator.
- W instalacji wieloserwisowej przetestuj każdą skonfigurowaną domenę i nieznany host. Brak Site nie może rozszerzać zapytania na rekordy wszystkich witryn.
- Traktuj tokeny API, dane SMTP i prywatne adresy URL jako sekrety. Nie dodawaj ich do Git ani do publicznych zgłoszeń.
- Wykonaj kopię zapasową bazy i plików multimedialnych przed migracjami, masowym przenoszeniem, importem lub pierwszą masową publikacją. Najpierw przetestuj te operacje na stagingu.

## Zalecane połączenia

- `wagtail-prose-editor-images` dodaje selektor Prose; `wagtail-desktop-publisher` obsługuje Markdown, jeśli zintegrowano endpoint obrazów.
- Komentarze i forum są niezależne.

## Lista kontrolna

- [ ] Zainstaluj wersję kandydującą na stagingu i zapisz wersje Pythona, Django, Wagtail oraz bazy.
- [ ] Uruchom `python manage.py check` i migracje pakietu.
- [ ] Przetestuj główny przepływ jako zwykły i ograniczony użytkownik.
- [ ] Sprawdź logi, dostęp, cache, kopie zapasowe i odtwarzanie.

Archiwum przechodzi statyczne kontrole składni i pakowania, ale w tym środowisku nie wykonano pełnych testów integracyjnych Django/Wagtail. Poniższą listę traktuj jako warunek wydania, a nie potwierdzenie przetestowania każdej kombinacji.

## Rozwiązywanie problemów

Jeśli przepływ nie działa, sprawdź konfigurację aplikacji, migracje, kolejność URL, uprawnienia i logi Django. Porównaj wersję pakietu i przykład z angielskim README.

## Licencja i pomoc

MIT. Kod źródłowy: [https://github.com/vovansrnd/wagtail-image-directories](https://github.com/vovansrnd/wagtail-image-directories).

