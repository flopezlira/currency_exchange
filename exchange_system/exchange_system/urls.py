"""
URL configuration for exchange_system project.
"""
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_spectacular.views import SpectacularSwaggerView

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core.admin import custom_admin_site



schema_view = get_schema_view(
    openapi.Info(
        title="Currency Exchange API",
        default_version='v1',
        description="API documentation for the Currency Exchange System",
    ),
    public=True,
)

class CustomSpectacularSwaggerView(SpectacularSwaggerView):

    template_name = 'swagger_ui.html'


urlpatterns = [
    # Schema endpoint for drf-spectacular
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI endpoint
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # JWT endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Use the custom admin site
    path('admin/', custom_admin_site.urls),
    path('api/v1/', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)



