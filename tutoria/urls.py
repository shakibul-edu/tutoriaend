"""
URL configuration for tutoria project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.schemas import get_schema_view
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from base.authentication import GoogleLoginView
from tutoria import settings
from django.conf.urls.static import static
from .views import CustomTokenObtainPairView, CustomTokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("auth/google/", GoogleLoginView.as_view()),
    path('', include('base.urls')),  # Include the base app's URLs
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('rest_framework.urls')),  # Include DRF's authentication URLs

    # Raw OpenAPI schema
    path("api-docs/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI
    path("api-docs/docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # ReDoc UI
    path("api-docs/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    
]

# This is the crucial part for serving media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
