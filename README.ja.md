# wagtail-image-directories

**Wagtail の画像モデルに年/slug メタデータとビジュアルな Image Navigator を追加します。新しいオリジナル画像は `images/<year>/<slug>/` に保存でき、Wagtail のコレクションと一括操作を利用できます。**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## 主な機能

- 画像数、推定容量、ページ送りを使ってディレクトリを閲覧。
- ファイルサイズ・ファイル数・デコード後ピクセル数に上限を設けた一括アップロード。
- 権限を確認してディレクトリや画像グループを作成、改名、統合、移動、削除。
- ディレクトリ構造を Wagtail コレクションに反映。

## 要件と互換性

- 宣言されている依存関係: `Wagtail >= 6.0`.
- Python、Django、Wagtail の互換性は組み合わせて確認してください。最低依存バージョンは全バージョンのサポートを意味しません。

パッケージのメタデータでは Wagtail >= 6.0 を宣言していますが、最小依存バージョンは全バージョンでの互換性を保証しません。このアーカイブには、すべての Django/Wagtail 組み合わせを網羅する自動テストマトリクスはありません。本番環境を更新する前に、正確なバージョン、データベース、ストレージバックエンド、デプロイ設定をステージングで確認してください。

## インストール

Wagtail プロジェクトと同じ仮想環境にパッケージをインストールします。

```bash
pip install wagtail-image-directories
```

プロジェクトで必要な他の依存関係を維持しながら、次の順序でアプリを追加します。

```python
INSTALLED_APPS = [
    # プロジェクトで必要な他の Django/Wagtail 依存関係も維持してください。
    "wagtail.images",
    "wagtail_image_directories",
]
```

`AbstractDirectoryImage` を継承した具体的な画像モデルを作成し、2 つの画像モデル設定を行います。完全な例は英語 README にあります。



## 初期設定

以下は最小の開始例です。モデル名、API フィールド、URL は実際の構成に合わせてください。

```python
# "media" を独自の Django アプリラベルに置き換えてください。
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

次に具体モデルを含むアプリの migration を作成・適用し、`python manage.py migrate` を実行します。変更されるのは新規アップロードのパスだけで、既存のメディアファイルは移動しません。


## 重要な設定と動作

このディレクトリの英語 README が正式な基準ドキュメントで、設定表と詳細例をすべて含みます。この翻訳では実際の導入手順と重要な安全上の注意を説明します。高度な設定を変更する前に英語版を確認してください。

設定の完全な一覧は[英語 README](README.md)を参照してください。

### 重要な注意事項

新規ファイルは `images/<year>/<slug>/` に保存されますが、マイグレーションは既存オリジナルを移動しません。このパッケージは crop を生成しないため、ディスク容量を考慮して rendition 仕様を別途制限してください。

## セキュリティと運用

- 依存関係を最新に保ってください。ユーザー作成 HTML には定められたサニタイズ/レンダリング経路を使い、保存済みコメントやフォーラム投稿を無条件に `|safe` で表示しないでください。
- 通常ユーザー、制限ユーザー、モデレーター、管理者でマイグレーションと権限を確認してください。
- マルチサイト環境では、設定済みのすべてのホストと未設定のホストをテストしてください。Site を特定できない場合、全サイトのレコードに検索範囲を拡張してはいけません。
- API トークン、SMTP 認証情報、非公開 URL は秘密情報として扱ってください。Git にコミットしたり、公開の不具合報告に含めたりしないでください。
- マイグレーション、大量移動、インポート、初回の一括公開の前に、データベースとメディアファイルをバックアップし、まずステージングで実行してください。

## 推奨構成

- `wagtail-prose-editor-images` は Prose 用画像選択を追加します。画像 API を連携すれば `wagtail-desktop-publisher` と Markdown 執筆にも適します。
- コメント/フォーラムパッケージは独立しています。

## 確認チェックリスト

- [ ] ステージングに候補版を導入し、Python、Django、Wagtail、DB の各バージョンを記録する。
- [ ] `python manage.py check` とパッケージのマイグレーションを実行する。
- [ ] 通常ユーザーと制限ユーザーで主要な操作を試す。
- [ ] ログ、アクセス制御、キャッシュ、バックアップ、復元を確認する。

このアーカイブは静的な構文・パッケージチェックに合格していますが、この環境では Django/Wagtail の完全な実行時統合テストを行っていません。以下の項目は全組み合わせのテスト済みという意味ではなく、リリース前の必須確認事項です。

## トラブルシューティング

動作しない場合は、アプリ設定、マイグレーション、URL の順序、ユーザー権限、Django ログを確認してください。パッケージ版と例を英語 README と照合してください。

## ライセンスとサポート

MIT. ソースコード: [https://github.com/vovansrnd/wagtail-image-directories](https://github.com/vovansrnd/wagtail-image-directories).

