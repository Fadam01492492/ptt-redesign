from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "批踢踢 Redesign 管理後台"
admin.site.site_title = "批踢踢 Redesign 後台"
admin.site.index_title = "資料管理"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("forum.urls")),
]
