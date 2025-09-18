from django.contrib import admin
from external.swagger.swagger import (
    SpectacularSwaggerView,
    SpectacularAPIView,
    SpectacularRedocView,
)

from config import settings
from django.urls import path, include
from django.conf.urls.static import static
from renderer.views import render_index_page

# Swagger Urls
swagger_urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger_ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
# Custom Apps Urls
api_urlpatterns = [
    path("account/", include("apps.account.urls")),
    path("location/", include("apps.location.urls")),
    path("appointment/", include("apps.appointment.urls")),
    path("report/", include("apps.report.urls")),
]

# Django Ckeditor 5 urls
ckeditor_urlpatterns = [path("ckeditor5/", include("django_ckeditor_5.urls"))]

urlpatterns = (
    [
        path("", render_index_page, name="home_page"),
        path("admin/", admin.site.urls),
    ]
    + swagger_urlpatterns
    + api_urlpatterns
    + ckeditor_urlpatterns
)


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
