from django.urls import path, include
from mapa import views

urlpatterns = [
    path('informacion', views.mapa_informacion, name="mostrar_mapa"),
    path('carga-datos', views.carga_datos, name="carga_datos"),
    path('carga-nacionalidades', views.carga_nacionalidades, name="carga_nacionalidades"),
    path('carga-oficinas', views.carga_oficinas, name="carga_oficinas"),
    path('carga-datos-batch', views.carga_datos_batch, name="carga_datos_batch"),
    path('api/periodo-custom', views.api_periodo_custom, name="api_periodo_custom"),
    path('api/nacionalidad-ranking', views.api_nacionalidad_ranking, name="api_nacionalidad_ranking"),
    path('api/reporte-nacionalidades', views.api_reporte_nacionalidades, name="api_reporte_nacionalidades"),
    path('reportes', views.reportes, name="reportes"),
]