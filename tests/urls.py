from django.urls import include, path

urlpatterns = [
    path("wagtail-image-directories/", include("wagtail_image_directories.urls")),
]
