from django.urls import path
from . import views

app_name = "wagtail_image_directories"

urlpatterns = [
    path("navigator/", views.ImageNavigatorView.as_view(), name="navigator"),
    path("filtered/", views.admin_filtered_images, name="filtered_images"),
    path("api/directories/<str:year>/", views.year_directories_ajax, name="year_directories_ajax"),
    path("directory/create/", views.create_directory, name="create_directory"),
    path("directory/delete/", views.delete_directory, name="delete_directory"),
    path("directories/rename/", views.rename_directory, name="rename_directory"),
    path("directories/merge/", views.merge_directories, name="merge_directories"),
    path("directories/search/", views.directory_search, name="directory_search"),
    path("images/upload/", views.ajax_upload_images, name="ajax_upload_images"),
    # МАССОВЫЕ ДЕЙСТВИЯ:
    path("images/bulk-delete/", views.bulk_delete_images, name="bulk_delete_images"),
    path("images/bulk-move/", views.bulk_move_images, name="bulk_move_images"),
    path("images/move-chooser/", views.image_move_chooser, name="image_move_chooser"),
]
