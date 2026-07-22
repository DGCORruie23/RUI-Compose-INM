from django.urls import path

from . import views

app_name = "vehiculos"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("listado/", views.listado, name="listado"),
    path("api/filtrar/", views.filtrar_dashboard, name="filtrar_dashboard"),
    path("api/listado/", views.filtrar_listado, name="filtrar_listado"),
    path("fragmento/listado/", views.listado_fragmento, name="listado_fragmento"),
    path("listado/exportar/", views.exportar_excel, name="exportar_excel"),
    path("api/popover/", views.popover_vehiculos, name="popover_vehiculos"),
    path("api/popover/kilometraje/", views.popover_kilometraje, name="popover_kilometraje"),
    path("api/mapa-ubicaciones/", views.mapa_ubicaciones_geojson, name="mapa_ubicaciones_geojson"),
    path("fragmento/resumen-estado/", views.resumen_estado_fragmento, name="resumen_estado_fragmento"),
    path("fragmento/<str:placa>/", views.detalle_fragmento, name="detalle_fragmento"),
    # Debe ir al final: "placa" es un segmento genérico y atraparía
    # cualquier ruta de un solo nivel si se declara antes que las de arriba.
    path("<str:placa>/", views.detalle_vehiculo, name="detalle"),
]
