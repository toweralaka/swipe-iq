from django.contrib import admin
from django.urls import path
from health.views import health
from editorial.views import media_preview

from accounts.views import RequestLinkView, ExchangeView, MeView, LogoutView, login_help, assetlinks
from editorial.student_api import ExaminationList, SubjectList, TopicList, UnitList, UnitDetail, StudentMedia

urlpatterns = [
    path("login", login_help),
    path(".well-known/assetlinks.json", assetlinks),
    path("api/v1/auth/request-link/", RequestLinkView.as_view()),
    path("api/v1/auth/exchange/", ExchangeView.as_view()),
    path("api/v1/auth/me/", MeView.as_view()),
    path("api/v1/auth/logout/", LogoutView.as_view()),
    path("api/v1/examinations/", ExaminationList.as_view()),
    path("api/v1/subjects/", SubjectList.as_view()),
    path("api/v1/topics/", TopicList.as_view()),
    path("api/v1/units/", UnitList.as_view()),
    path("api/v1/units/<int:pk>/", UnitDetail.as_view()),
    path("api/v1/media/<uuid:asset_id>/", StudentMedia.as_view()),
    path("editorial/media/<uuid:asset_id>/", media_preview, name="editorial-media"),
    path("admin/", admin.site.urls),
    path("api/v1/health/", health, name="health"),
]
