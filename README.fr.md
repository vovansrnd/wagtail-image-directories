# wagtail-image-directories

**Ajoute des métadonnées année/slug et un navigateur visuel au modèle d’images Wagtail. Les nouveaux originaux peuvent être stockés dans `images/<year>/<slug>/`, tout en conservant les collections et opérations groupées de Wagtail.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Fonctionnalités principales

- Parcourir les répertoires avec nombre d’images, taille estimée et pagination.
- Téléverser par lots avec limites de taille, de nombre de fichiers et de pixels décodés.
- Créer, renommer, fusionner, déplacer ou supprimer des groupes avec vérification des autorisations.
- Reproduire l’organisation dans les collections Wagtail.

## Prérequis et compatibilité

- Dépendances déclarées: `Wagtail >= 6.0`.
- La compatibilité de Python, Django et Wagtail doit être vérifiée conjointement. La dépendance minimale du paquet ne confirme pas que toutes les versions sont prises en charge.

Les métadonnées déclarent Wagtail >= 6.0, mais une dépendance minimale ne prouve pas la compatibilité. Cette archive ne contient pas de matrice automatisée complète pour toutes les combinaisons Django/Wagtail. Avant une mise à jour en production, testez les versions exactes, la base de données, le stockage et la configuration de déploiement en préproduction.

## Installation

Installez le paquet dans le même environnement virtuel que votre projet Wagtail :

```bash
pip install wagtail-image-directories
```

Ajoutez les applications dans cet ordre en conservant les autres dépendances du projet :

```python
INSTALLED_APPS = [
    # Conservez également les autres dépendances Django/Wagtail déjà requises.
    "wagtail.images",
    "wagtail_image_directories",
]
```

Créez un modèle d’image concret dérivé de `AbstractDirectoryImage` et configurez les deux paramètres du modèle. L’exemple complet figure dans le README anglais.



## Configuration initiale

Exemple minimal pour démarrer. Adaptez les noms de modèles, les champs API et les URL à votre configuration.

```python
# Remplacez "media" par le nom de votre application Django.
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

Créez et appliquez ensuite les migrations de l’application qui contient le modèle concret, puis exécutez `python manage.py migrate`. Cela ne change que le chemin des nouveaux envois et ne déplace pas les fichiers existants.


## Paramètres et comportement importants

Le README anglais de ce répertoire est la référence canonique et contient les tableaux complets des options et les exemples détaillés. Cette traduction couvre la mise en place pratique et les avertissements de sécurité essentiels ; consultez la référence anglaise avant de modifier les options avancées.

Consultez le [README en anglais](README.md) pour la référence complète des paramètres.

### Points importants

Les nouveaux fichiers utilisent `images/<year>/<slug>/` ; la migration ne déplace pas les originaux existants. Le paquet ne crée pas de recadrages : limitez séparément les spécifications de rendition selon le quota disque.

## Sécurité et exploitation

- Maintenez les dépendances à jour. Pour le HTML utilisateur, utilisez le chemin prévu de nettoyage et de rendu ; n’affichez pas les commentaires ou messages stockés avec un `|safe` inconditionnel.
- Vérifiez migrations et autorisations avec des utilisateurs normaux, restreints, modérateurs et administrateurs.
- En environnement multisite, testez chaque domaine configuré ainsi qu’un hôte inconnu. Si aucun Site n’est trouvé, une requête ne doit jamais s’élargir à tous les sites.
- Traitez les jetons API, identifiants SMTP et URL privées comme des secrets. Ne les committez pas dans Git et ne les publiez pas dans les rapports de bug.
- Sauvegardez la base de données et les fichiers médias avant les migrations, déplacements en masse, imports ou première publication en masse. Testez d’abord en préproduction.

## Combinaisons recommandées

- `wagtail-prose-editor-images` ajoute le sélecteur Prose ; `wagtail-desktop-publisher` convient au Markdown si l’endpoint d’images est intégré.
- Les commentaires et le forum sont indépendants.

## Liste de vérification

- [ ] Installez la version candidate en préproduction et notez les versions de Python, Django, Wagtail et de la base de données.
- [ ] Exécutez `python manage.py check` et les migrations du paquet.
- [ ] Testez le flux principal avec un utilisateur normal et un utilisateur restreint.
- [ ] Vérifiez journaux, accès, cache, sauvegardes et restauration.

L’archive passe les contrôles statiques de syntaxe et de packaging, mais l’intégration Django/Wagtail complète n’a pas été exécutée dans cet environnement. Considérez la liste ci-dessous comme une condition de publication, et non comme la preuve que toutes les combinaisons sont testées.

## Dépannage

Si le flux ne fonctionne pas, vérifiez la configuration de l’application, les migrations, l’ordre des URL, les autorisations et les journaux Django. Comparez la version et l’exemple avec le README anglais.

## Licence et assistance

MIT. Code source: [https://github.com/vovansrnd/wagtail-image-directories](https://github.com/vovansrnd/wagtail-image-directories).

