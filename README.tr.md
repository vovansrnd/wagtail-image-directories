# wagtail-image-directories

**Wagtail görsel modeline yıl/slug metaverisi ve görsel bir Image Navigator ekler. Yeni orijinaller `images/<year>/<slug>/` altında saklanabilir; Wagtail koleksiyonları ve toplu işlemler korunur.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Temel özellikler

- Sayı, yaklaşık disk kullanımı ve sayfalama ile dizinleri görüntüleme.
- Dosya boyutu, adet ve çözümlenmiş piksel sınırlarıyla toplu yükleme.
- İzin denetimleriyle grupları oluşturma, yeniden adlandırma, birleştirme, taşıma ve silme.
- Dizin yapısını Wagtail koleksiyonlarına yansıtma.

## Gereksinimler ve uyumluluk

- Bildirilen bağımlılıklar: `Wagtail >= 6.0`.
- Python, Django ve Wagtail uyumluluğu birlikte kontrol edilmelidir. Paketin asgari bağımlılığı tüm sürümlerin desteklendiğini kanıtlamaz.

Paket metaverisi Wagtail >= 6.0 belirtir; ancak asgari bağımlılık, tüm sürümlerle uyumluluğu kanıtlamaz. Bu arşiv tüm Django/Wagtail kombinasyonları için tam otomatik test matrisi içermez. Üretimi yükseltmeden önce tam sürümleri, veritabanını, depolama arka ucunu ve dağıtım ayarlarını staging ortamında sınayın.

## Kurulum

Paketi Wagtail projenizle aynı sanal ortama yükleyin:

```bash
pip install wagtail-image-directories
```

Diğer proje bağımlılıklarını koruyarak uygulamaları bu sırayla ekleyin:

```python
INSTALLED_APPS = [
    # Projenin zaten kullandığı diğer Django/Wagtail bağımlılıklarını da koruyun.
    "wagtail.images",
    "wagtail_image_directories",
]
```

`AbstractDirectoryImage` sınıfından türeyen somut bir görüntü modeli oluşturun ve iki model ayarını yapılandırın. Tam örnek İngilizce README içindedir.



## İlk yapılandırma

Başlangıç için en küçük örnek aşağıdadır. Model adlarını, API alanlarını ve URL’leri yapılandırmanıza uyarlayın.

```python
# "media" değerini kendi Django uygulamanızın adıyla değiştirin.
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

Ardından somut modeli içeren uygulama için migration oluşturup uygulayın ve `python manage.py migrate` çalıştırın. Bu yalnızca yeni yüklemelerin yolunu değiştirir; mevcut medya dosyalarını taşımaz.


## Önemli ayarlar ve davranış

Bu dizindeki İngilizce README, tüm seçenek tablolarını ve genişletilmiş örnekleri içeren temel başvuru belgesidir. Bu çeviri pratik kurulumu ve temel güvenlik uyarılarını kapsar; gelişmiş ayarları değiştirmeden önce İngilizce başvuruya bakın.

Tam ayar listesi için [İngilizce README](README.md) dosyasına bakın.

### Önemli notlar

Yeni dosyalar `images/<year>/<slug>/` yolunu kullanır; geçiş mevcut orijinalleri taşımaz. Paket kırpım oluşturmaz, bu nedenle disk kotasını dikkate alarak rendition kurallarını ayrıca sınırlayın.

## Güvenlik ve işletim

- Bağımlılıkları güncel tutun. Kullanıcı HTML’si için belirlenen temizleme/görüntüleme yolunu kullanın; kaydedilmiş yorumları veya forum gönderilerini koşulsuz `|safe` ile göstermeyin.
- Geçişleri ve izinleri normal, kısıtlı, moderatör ve yönetici hesaplarıyla kontrol edin.
- Çoklu site kurulumlarında yapılandırılmış her alan adını ve bilinmeyen bir hostu sınayın. Site bulunamazsa sorgu tüm sitelerdeki kayıtları kapsayacak şekilde genişlememelidir.
- API tokenlarını, SMTP kimlik bilgilerini ve özel URL’leri gizli kabul edin. Bunları Git’e eklemeyin veya herkese açık hata raporlarında paylaşmayın.
- Geçişler, toplu taşıma, içe aktarma veya ilk toplu yayın öncesinde veritabanını ve medya dosyalarını yedekleyin. Önce staging ortamında deneyin.

## Önerilen kombinasyonlar

- `wagtail-prose-editor-images` Prose görsel seçicisini ekler; `wagtail-desktop-publisher`, görsel uç noktası entegre edilmişse Markdown için uygundur.
- Yorum ve forum paketleri bağımsızdır.

## Doğrulama kontrol listesi

- [ ] Aday sürümü staging ortamına kurun; Python, Django, Wagtail ve veritabanı sürümlerini kaydedin.
- [ ] `python manage.py check` ve paket geçişlerini çalıştırın.
- [ ] Ana akışı normal ve kısıtlı hesapla sınayın.
- [ ] Kayıtları, erişimi, önbelleği, yedeklemeyi ve geri yüklemeyi kontrol edin.

Arşiv statik sözdizimi ve paketleme kontrollerini geçer; ancak bu ortamda tam Django/Wagtail çalışma zamanı entegrasyonu test edilmedi. Aşağıdaki listeyi tüm sürümlerin test edildiğinin kanıtı değil, yayın öncesi zorunlu kontrol olarak görün.

## Sorun giderme

Akış çalışmıyorsa uygulama ayarlarını, geçişleri, URL sırasını, kullanıcı izinlerini ve Django kayıtlarını kontrol edin. Paket sürümünü ve örneği İngilizce README ile karşılaştırın.

## Lisans ve destek

MIT. Kaynak kod: [https://github.com/vovansrnd/wagtail-image-directories](https://github.com/vovansrnd/wagtail-image-directories).

