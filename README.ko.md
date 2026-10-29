# wagtail-image-directories

**Wagtail 이미지 모델에 연도/slug 메타데이터와 시각적 Image Navigator를 추가합니다. 새 원본 파일을 `images/<year>/<slug>/`에 저장할 수 있으며 Wagtail 컬렉션과 일괄 작업을 유지합니다.**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## 주요 기능

- 이미지 개수, 대략적인 디스크 사용량, 페이지 이동을 포함한 디렉터리 탐색.
- 파일 크기, 개수, 디코딩된 픽셀 수 제한이 있는 일괄 업로드.
- 권한을 확인하며 디렉터리/이미지 그룹 생성, 이름 변경, 병합, 이동, 삭제.
- 디렉터리 구조를 Wagtail 컬렉션에 반영.

## 요구 사항 및 호환성

- 선언된 종속성: `Wagtail >= 6.0`.
- Python, Django, Wagtail의 호환성은 함께 확인해야 합니다. 최소 종속성 버전은 모든 버전의 지원을 의미하지 않습니다.

패키지 메타데이터는 Wagtail >= 6.0을 선언하지만 최소 의존성은 모든 버전의 호환성을 입증하지 않습니다. 이 아카이브에는 모든 Django/Wagtail 조합을 다루는 완전한 자동 테스트 매트릭스가 없습니다. 운영 환경을 업그레이드하기 전에 정확한 버전, 데이터베이스, 저장소 백엔드 및 배포 설정을 스테이징에서 검증하세요.

## 설치

Wagtail 프로젝트와 같은 가상 환경에 패키지를 설치하세요:

```bash
pip install wagtail-image-directories
```

프로젝트의 기존 종속성을 유지하면서 다음 순서로 앱을 추가하세요:

```python
INSTALLED_APPS = [
    # 프로젝트에 필요한 다른 Django/Wagtail 종속성도 유지하세요.
    "wagtail.images",
    "wagtail_image_directories",
]
```

`AbstractDirectoryImage`를 상속하는 구체적인 이미지 모델을 만들고 두 이미지 모델 설정을 구성하세요. 전체 예시는 영문 README에 있습니다.



## 초기 설정

아래는 최소 시작 예제입니다. 모델 이름, API 필드, URL을 실제 구성에 맞추세요.

```python
# "media"를 자체 Django 앱 라벨로 바꾸세요.
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

그런 다음 구체 모델이 있는 앱의 마이그레이션을 생성/적용하고 `python manage.py migrate`를 실행하세요. 새 업로드 경로만 바뀌며 기존 미디어 파일은 이동하지 않습니다.


## 중요 설정 및 동작

이 디렉터리의 영어 README가 정식 기준 문서이며 전체 설정 표와 자세한 예제를 포함합니다. 이 번역은 실제 설치 절차와 핵심 보안 주의사항을 다룹니다. 고급 설정을 변경하기 전에 영어 문서를 확인하세요.

전체 설정 참조는 [영문 README](README.md)를 확인하세요.

### 중요한 참고 사항

새 파일은 `images/<year>/<slug>/`에 저장되지만 마이그레이션은 기존 원본을 이동하지 않습니다. 이 패키지는 크롭을 생성하지 않으므로 디스크 할당량을 고려해 rendition 규칙을 별도로 제한하세요.

## 보안 및 운영 지침

- 종속성을 최신 상태로 유지하세요. 사용자 작성 HTML에는 지정된 정리/렌더링 경로를 사용하고, 저장된 댓글이나 포럼 게시물을 무조건 `|safe`로 출력하지 마세요.
- 일반 사용자, 제한 사용자, 중재자, 관리자 계정으로 마이그레이션과 권한을 확인하세요.
- 멀티사이트 환경에서는 설정된 모든 도메인과 알 수 없는 호스트를 테스트하세요. Site를 찾지 못했을 때 조회 범위를 모든 사이트의 레코드로 넓혀서는 안 됩니다.
- API 토큰, SMTP 자격 증명, 비공개 URL은 비밀로 취급하세요. Git에 커밋하거나 공개 버그 보고서에 포함하지 마세요.
- 마이그레이션, 대량 이동, 가져오기 또는 최초 대량 게시 전에 데이터베이스와 미디어 파일을 백업하고 먼저 스테이징에서 실행하세요.

## 권장 조합

- `wagtail-prose-editor-images`는 Prose 이미지 선택기를 추가합니다. 이미지 API를 통합하면 `wagtail-desktop-publisher`를 통한 Markdown 작성에도 적합합니다.
- 댓글/포럼 패키지는 독립적입니다.

## 검증 체크리스트

- [ ] 스테이징에 후보 버전을 설치하고 Python, Django, Wagtail 및 DB 버전을 기록하세요.
- [ ] `python manage.py check`와 패키지 마이그레이션을 실행하세요.
- [ ] 일반 사용자와 제한 사용자로 주요 흐름을 테스트하세요.
- [ ] 로그, 접근 제어, 캐시, 백업 및 복원 절차를 점검하세요.

이 아카이브는 정적 구문 및 패키징 검사를 통과했지만 현재 환경에서 Django/Wagtail 런타임 통합 테스트 전체를 실행하지는 못했습니다. 아래 목록은 모든 조합을 테스트했다는 주장이 아니라 출시 전 필수 확인 항목입니다.

## 문제 해결

흐름이 작동하지 않으면 앱 설정, 마이그레이션, URL 순서, 사용자 권한 및 Django 로그를 확인하세요. 패키지 버전과 예제를 영문 README와 비교하세요.

## 라이선스 및 지원

MIT. 소스 코드: [https://github.com/vovansrnd/wagtail-image-directories](https://github.com/vovansrnd/wagtail-image-directories).

