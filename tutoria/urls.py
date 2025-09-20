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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls')),  # Include the base app's URLs
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('rest_framework.urls')),  # Include DRF's authentication URLs
    path('schema/', get_schema_view(
        title="My API",
        description="API documentation for my project",
        version="1.0.0"
    ), name="openapi-schema"),

    # Raw OpenAPI schema
    path("api-docs/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI
    path("api-docs/docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # ReDoc UI
    path("api-docs/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    
]
