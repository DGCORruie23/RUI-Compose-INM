"""
Rutas de la API REST, versionadas (v1) para poder evolucionar el
contrato después sin romper a quien ya se conectó. Se incluye desde
vehiculos/urls.py bajo el prefijo api/v1/.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api_views

router = DefaultRouter()
router.register("vehiculos", api_views.VehiculoViewSet, basename="api-vehiculo")

urlpatterns = [
    path("catalogos/", api_views.catalogos, name="api-catalogos"),
    path("", include(router.urls)),
]
