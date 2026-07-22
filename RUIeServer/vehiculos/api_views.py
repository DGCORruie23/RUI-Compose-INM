"""
Vistas de la API REST. De momento SOLO LECTURA (mismo criterio que ya
aplicamos al resto del módulo: consulta y filtrado, sin alta/edición
hasta que existan roles). Cuando se necesite escritura desde la API,
basta con cambiar ReadOnlyModelViewSet por ModelViewSet y agregar
permisos (permission_classes) — la estructura ya queda lista para eso.
"""

from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Asignacion, Estado, Situacion, TipoVehiculo, Vehiculo
from .serializers import (
    CatalogoSerializer,
    VehiculoDetalleSerializer,
    VehiculoListaSerializer,
)


class VehiculoPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class VehiculoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /vehiculos/api/v1/vehiculos/                -> listado paginado
    GET /vehiculos/api/v1/vehiculos/?situacion=Activo -> filtrado
    GET /vehiculos/api/v1/vehiculos/<id>/            -> detalle completo
    """
    queryset = Vehiculo.objects.select_related(
        "tipo_vehiculo", "asignacion", "situacion", "estado", "inmueble", "tarjeta"
    ).prefetch_related("fotos", "lecturas_km", "combustible", "capufe")
    pagination_class = VehiculoPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return VehiculoDetalleSerializer
        return VehiculoListaSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        situacion = self.request.query_params.get("situacion")
        tipo = self.request.query_params.get("tipo_vehiculo")
        asignacion = self.request.query_params.get("asignacion")
        placa = self.request.query_params.get("placa")

        if situacion:
            qs = qs.filter(situacion__nombre__iexact=situacion)
        if tipo:
            qs = qs.filter(tipo_vehiculo__nombre__iexact=tipo)
        if asignacion:
            qs = qs.filter(asignacion__nombre__iexact=asignacion)
        if placa:
            qs = qs.filter(placa__iexact=placa)
        return qs


@api_view(["GET"])
def catalogos(request):
    """
    GET /vehiculos/api/v1/catalogos/
    Regresa las opciones válidas de cada catálogo — útil para que un
    sistema externo sepa, por ejemplo, que 'situacion' SOLO acepta
    Activo / Mantenimiento / Posible baja, sin tener que adivinar.
    """
    return Response({
        "situacion": CatalogoSerializer(Situacion.objects.all(), many=True).data,
        "tipo_vehiculo": CatalogoSerializer(TipoVehiculo.objects.all(), many=True).data,
        "asignacion": CatalogoSerializer(Asignacion.objects.all(), many=True).data,
        "estado": CatalogoSerializer(Estado.objects.all(), many=True).data,
    })
