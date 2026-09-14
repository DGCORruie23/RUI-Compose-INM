"""
Rutas de la ficha/listado de Parque Vehicular (solo lectura). Vive en un
archivo separado de mapa/urls.py -- aunque las vistas ya son parte de la
app 'mapa' (ver views.py, seccion "Parque Vehicular") -- para conservar el
prefijo publico "/vehiculos/..." tal cual estaba cuando esto era su propia
app de Django, sin romper links/fetch ya existentes.
"""

from django.urls import path

from mapa import views

app_name = "vehiculos"

urlpatterns = [
    path("", views.vehiculos_dashboard, name="dashboard"),
    path("listado/", views.vehiculos_listado, name="listado"),
    path("api/filtrar/", views.filtrar_dashboard, name="filtrar_dashboard"),
    path("api/listado/", views.filtrar_listado, name="filtrar_listado"),
    path("fragmento/listado/", views.listado_fragmento, name="listado_fragmento"),
    path("listado/exportar/", views.exportar_excel_vehiculos, name="exportar_excel"),
    path("api/popover/", views.popover_vehiculos, name="popover_vehiculos"),
    path("api/popover/kilometraje/", views.popover_kilometraje, name="popover_kilometraje"),
    path("api/mapa-ubicaciones/", views.mapa_ubicaciones_geojson, name="mapa_ubicaciones_geojson"),
    path("api/conteo/", views.conteo_total, name="conteo_total"),
    path("fragmento/resumen-estado/", views.resumen_estado_fragmento, name="resumen_estado_fragmento"),
    path("fragmento/<str:placa>/", views.detalle_fragmento, name="detalle_fragmento"),
    path("descargar-pdf/<str:placa>/", views.descargar_pdf_ficha, name="descargar_pdf_ficha"),
    # Alternativas por id para vehiculos sin placa real (placa de relleno
    # tipo "S/P", "SIN NUMERO DE PLACA", etc: ni son unicas ni todas son
    # validas como segmento de URL). Ver mapa/views.py _placa_ambigua().
    path("fragmento/id/<int:vehiculo_id>/", views.detalle_fragmento_por_id, name="detalle_fragmento_id"),
    path("id/<int:vehiculo_id>/", views.detalle_vehiculo_por_id, name="detalle_id"),
    # Debe ir al final: "placa" es un segmento genérico y atraparía
    # cualquier ruta de un solo nivel si se declara antes que las de arriba.
    path("<str:placa>/", views.detalle_vehiculo, name="detalle"),
]
