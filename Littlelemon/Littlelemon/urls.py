from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("LittlelemonApp.urls")),
    path("api-token-auth/", obtain_auth_token, name="api-token-auth"),
]

if settings.DEBUG:
    urlpatterns.insert(1, path("__debug__/", include("debug_toolbar.urls")))
