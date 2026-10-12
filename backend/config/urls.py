from django.contrib import admin
from django.urls import path
from health.views import health
from editorial.views import media_preview

urlpatterns = [
    path("editorial/media/<uuid:asset_id>/", media_preview, name="editorial-media"),
    path("admin/", admin.site.urls),
    path("api/v1/health/", health, name="health"),
]
