from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from common.health import health_check

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/health/", health_check, name="health"),
    path("api/v1/health/", health_check, name="health_v1"),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/posts/", include("apps.posts.urls")),
    path("api/v1/media/", include("apps.media_files.urls")),
    path("api/v1/groups/", include("apps.groups.urls")),
    path("api/v1/chat/", include("apps.chat.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/admin/", include("apps.admin_management.urls")),
]

if settings.STORAGE_BACKEND == "local":
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
