# wagtail-image-directories

**Adiciona metadados de ano/slug e um navegador visual ao modelo de imagens do Wagtail. Novos originais podem ser armazenados em `images/<year>/<slug>/`, mantendo coleções e operações em lote do Wagtail.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## Principais recursos

- Navegar por diretórios com contagens, tamanho aproximado e paginação.
- Enviar lotes com limites de tamanho, quantidade de arquivos e pixels decodificados.
- Criar, renomear, mesclar, mover ou excluir grupos com verificação de permissões.
- Espelhar a organização nas coleções do Wagtail.

## Requisitos e compatibilidade

- Dependências declaradas: `Wagtail >= 6.0`.
- A compatibilidade entre Python, Django e Wagtail deve ser verificada em conjunto. A dependência mínima do pacote não confirma suporte a todas as versões.

Os metadados declaram Wagtail >= 6.0, mas uma dependência mínima não comprova compatibilidade. Este arquivo não inclui uma matriz automatizada completa para todas as combinações de Django/Wagtail. Antes de atualizar produção, teste as versões exatas, o banco de dados, o armazenamento e as configurações de implantação em staging.

## Instalação

Instale o pacote no mesmo ambiente virtual do seu projeto Wagtail:

```bash
pip install wagtail-image-directories
```

Adicione os apps nesta ordem, mantendo as demais dependências do projeto:

```python
INSTALLED_APPS = [
    # Preserve também as outras dependências Django/Wagtail já necessárias.
    "wagtail.images",
    "wagtail_image_directories",
]
```

Crie um modelo concreto de imagem derivado de `AbstractDirectoryImage` e configure as duas opções do modelo. O exemplo completo está no README em inglês.



## Configuração inicial

Exemplo mínimo para começar. Adapte nomes de modelos, campos da API e URLs à sua configuração.

```python
# Substitua "media" pelo nome do seu aplicativo Django.
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

Depois gere e aplique as migrações do app que contém o modelo concreto e execute `python manage.py migrate`. Isso altera apenas o caminho de novos uploads; não move arquivos de mídia existentes.


## Configurações e comportamento importantes

O README em inglês deste diretório é a referência canônica e contém as tabelas completas de opções e exemplos detalhados. Esta tradução cobre a configuração prática e os avisos essenciais de segurança; consulte a referência em inglês antes de alterar opções avançadas.

Consulte o [README em inglês](README.md) para a referência completa das configurações.

### Observações importantes

Arquivos novos usam `images/<year>/<slug>/`; a migração não move os originais existentes. O pacote não gera cortes, portanto limite as especificações de rendition separadamente considerando a cota de disco.

## Segurança e operação

- Mantenha as dependências atualizadas. Para HTML escrito por usuários, use o fluxo previsto de sanitização e renderização; não exiba comentários ou posts armazenados com `|safe` incondicional.
- Verifique migrações e permissões com usuários comuns, restritos, moderadores e administradores.
- Em instalações multissite, teste cada domínio configurado e um host desconhecido. Se nenhum Site for encontrado, a consulta não deve abranger registros de todos os sites.
- Trate tokens de API, credenciais SMTP e URLs privadas como segredos. Não os envie ao Git nem os inclua em relatórios públicos.
- Faça backup do banco de dados e dos arquivos de mídia antes de migrações, movimentações em lote, importações ou da primeira publicação em massa. Teste primeiro em staging.

## Combinações recomendadas

- `wagtail-prose-editor-images` adiciona o seletor do Prose; `wagtail-desktop-publisher` atende Markdown se o endpoint de imagens for integrado.
- Comentários e fórum são independentes.

## Lista de verificação

- [ ] Instale a versão candidata em staging e registre as versões de Python, Django, Wagtail e banco de dados.
- [ ] Execute `python manage.py check` e as migrações do pacote.
- [ ] Teste o fluxo principal com usuário comum e usuário restrito.
- [ ] Confira logs, acesso, cache, backups e restauração.

O arquivo passou pelas verificações estáticas de sintaxe e empacotamento, mas a integração completa com Django/Wagtail não foi executada neste ambiente. Trate a lista abaixo como requisito para o lançamento, não como prova de que todas as combinações foram testadas.

## Solução de problemas

Se o fluxo não funcionar, confira a configuração do app, migrações, ordem das URLs, permissões e logs do Django. Compare a versão e o exemplo com o README em inglês.

## Licença e suporte

MIT. Código-fonte: [https://github.com/vovansrnd/wagtail-image-directories](https://github.com/vovansrnd/wagtail-image-directories).

