# wagtail-image-directories

**为 Wagtail 图片模型添加年份/slug 元数据和可视化图片导航器。新原图可存放在 `images/<year>/<slug>/` 中，同时保留 Wagtail 集合与批量操作能力。**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## 主要功能

- 按目录浏览图片数量、估算占用空间并分页。
- 批量上传时限制单文件大小、文件数量和解码后的像素总量。
- 在权限检查下创建、重命名、合并、移动或删除目录与图片组。
- 将目录组织结构映射到 Wagtail 集合。

## 依赖与兼容性

- 声明的依赖: `Wagtail >= 6.0`.
- Python、Django 与 Wagtail 的兼容性必须一起验证。最低依赖版本并不代表所有版本均受支持。

包元数据声明 Wagtail >= 6.0，但最低依赖版本并不代表已验证所有版本的兼容性。本归档不包含覆盖所有 Django/Wagtail 组合的完整自动化测试矩阵。升级生产环境前，请在预发布环境验证具体版本、数据库、文件存储后端和部署配置。

## 安装

请在与 Wagtail 项目相同的虚拟环境中安装此包：

```bash
pip install wagtail-image-directories
```

按以下顺序添加应用，同时保留项目原有的其他依赖：

```python
INSTALLED_APPS = [
    # 同时保留项目需要的其他 Django/Wagtail 依赖。
    "wagtail.images",
    "wagtail_image_directories",
]
```

创建继承自 `AbstractDirectoryImage` 的具体图片模型，并配置两个图片模型设置。完整示例请参阅英文 README。



## 初始配置

下面是最小起步示例。请根据项目调整模型名、API 字段和 URL。

```python
# 将 "media" 替换为您自己的 Django 应用标签。
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

然后为包含具体模型的应用生成并应用迁移，并运行 `python manage.py migrate`。这只会改变新上传文件的路径，不会移动现有媒体文件。


## 重要设置与行为

本目录中的英文 README 是规范参考文档，包含完整设置表和扩展示例。本译文覆盖实际安装步骤和关键安全注意事项；修改高级设置前请查阅英文文档。

完整设置说明请参阅[英文 README](README.md)。

### 重要注意事项

新文件使用 `images/<year>/<slug>/`；迁移不会移动已有原图。该包不生成裁剪图，因此必须根据磁盘配额单独限制 rendition 规格。

## 安全与运维建议

- 请保持依赖更新。用户编写的 HTML 应使用预期的清理和渲染路径；不要无条件对已存储的评论或论坛帖子使用 `|safe`。
- 请分别使用普通用户、受限用户、版主和管理员验证迁移与权限。
- 多站点部署时，请测试每个已配置域名以及一个未知主机。找不到 Site 时，查询不得扩大为读取所有站点的数据。
- API 令牌、SMTP 凭据和私有 URL 都应视为机密。不要提交到 Git，也不要放入公开的问题报告。
- 执行迁移、批量移动、导入或首次批量发布之前，请备份数据库和媒体文件，并先在预发布环境测试。

## 推荐组合

- `wagtail-prose-editor-images` 提供 Prose 图片选择器；Markdown 写作可搭配 `wagtail-desktop-publisher`，但必须集成图片上传接口。
- 评论与论坛包相互独立。

## 验证清单

- [ ] 在预发布环境安装候选版本，并记录 Python、Django、Wagtail 和数据库版本。
- [ ] 运行 `python manage.py check` 和包迁移。
- [ ] 使用普通用户与受限用户测试主要流程。
- [ ] 检查日志、访问权限、缓存、备份和恢复。

本归档通过静态语法与打包检查，但当前环境未完成 Django/Wagtail 运行时集成测试。请将以下清单视为发布前的必检项目，而不是所有版本组合均已测试的声明。

## 故障排查

如果流程无法运行，请检查应用配置、迁移、URL 顺序、用户权限和 Django 日志，并将包版本与示例和英文 README 对照。

## 许可证与支持

MIT. 源代码: [https://github.com/vovansrnd/wagtail-image-directories](https://github.com/vovansrnd/wagtail-image-directories).

