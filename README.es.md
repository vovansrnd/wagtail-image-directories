# wagtail-image-directories

**Añade metadatos de año/slug y un navegador visual de imágenes al modelo de Wagtail. Los originales nuevos pueden guardarse en `images/<year>/<slug>/`, manteniendo las colecciones y operaciones por lotes de Wagtail.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Funciones principales

- Explorar directorios con recuentos, tamaño aproximado y paginación.
- Subir lotes con límites de tamaño, número de archivos y píxeles decodificados.
- Crear, renombrar, combinar, mover o eliminar grupos comprobando permisos.
- Replicar la organización en colecciones de Wagtail.

## Requisitos y compatibilidad

- Dependencias declaradas: `Wagtail >= 6.0`.
- La compatibilidad de Python, Django y Wagtail debe verificarse en conjunto. La dependencia mínima del paquete no confirma que todas las versiones estén soportadas.

Los metadatos declaran Wagtail >= 6.0, pero una dependencia mínima no demuestra compatibilidad. Este archivo no incluye una matriz automatizada completa para todas las combinaciones de Django/Wagtail. Antes de actualizar producción, prueba las versiones exactas, la base de datos, el almacenamiento y la configuración de despliegue en un entorno de pruebas.

## Instalación

Instala el paquete en el mismo entorno virtual que tu proyecto Wagtail:

```bash
pip install wagtail-image-directories
```

Añade las aplicaciones en el orden indicado y conserva las demás dependencias del proyecto:

```python
INSTALLED_APPS = [
    # Conserva también las demás dependencias Django/Wagtail que necesita el proyecto.
    "wagtail.images",
    "wagtail_image_directories",
]
```

Cree un modelo de imagen concreto derivado de `AbstractDirectoryImage` y configure ambos ajustes del modelo. El ejemplo completo está en el README en inglés.



## Configuración inicial

Ejemplo mínimo para empezar. Adapta los nombres de modelos, campos API y URL a tu configuración.

```python
# Sustituya "media" por el nombre de su aplicación Django.
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

Después genere y aplique las migraciones de la aplicación del modelo concreto y ejecute `python manage.py migrate`. Esto solo cambia la ruta de nuevas cargas; no mueve los archivos de medios existentes.


## Ajustes y comportamiento importantes

El README en inglés de este directorio es la referencia canónica y contiene las tablas completas de opciones y ejemplos ampliados. Esta traducción cubre la configuración práctica y las advertencias de seguridad esenciales; consulta la referencia inglesa antes de cambiar opciones avanzadas.

Consulta la [versión inglesa del README](README.md) para ver la referencia completa de ajustes.

### Notas importantes

Los archivos nuevos usan `images/<year>/<slug>/`; la migración no mueve los originales existentes. El paquete no genera recortes, así que limita por separado las especificaciones de rendition según la cuota de disco.

## Seguridad y operación

- Mantén las dependencias actualizadas. Para HTML escrito por usuarios, utiliza la limpieza y representación previstas; no muestres comentarios o publicaciones almacenadas con `|safe` incondicional.
- Comprueba migraciones y permisos con usuarios normales, restringidos, moderadores y administradores.
- En instalaciones multisitio, prueba cada dominio configurado y un host desconocido. Si no se encuentra un Site, la consulta nunca debe ampliarse a todos los sitios.
- Trata los tokens de API, las credenciales SMTP y las URL privadas como secretos. No los guardes en Git ni los incluyas en informes públicos.
- Haz copias de seguridad de la base de datos y de los medios antes de migraciones, movimientos masivos, importaciones o la primera publicación masiva. Prueba primero en staging.

## Combinaciones recomendadas

- `wagtail-prose-editor-images` añade el selector Prose; `wagtail-desktop-publisher` sirve para Markdown si se integra el endpoint de imágenes.
- Comentarios y foro son independientes.

## Lista de verificación

- [ ] Instala la versión candidata en staging y anota las versiones de Python, Django, Wagtail y la base de datos.
- [ ] Ejecuta `python manage.py check` y las migraciones del paquete.
- [ ] Prueba el flujo principal con un usuario normal y otro restringido.
- [ ] Revisa registros, acceso, caché, copias de seguridad y recuperación.

El archivo supera comprobaciones estáticas de sintaxis y empaquetado, pero no se ha ejecutado aquí una prueba completa de integración Django/Wagtail. Trata la lista siguiente como un requisito previo a la publicación, no como una afirmación de que se han probado todas las combinaciones.

## Solución de problemas

Si el flujo no funciona, revisa la configuración de la app, las migraciones, el orden de URL, los permisos y los registros de Django. Compara la versión y el ejemplo con el README inglés.

## Licencia y soporte

MIT. Código fuente: [https://github.com/vovansrnd/wagtail-image-directories](https://github.com/vovansrnd/wagtail-image-directories).

