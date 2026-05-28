from django.urls import path, include
from mapa import views

urlpatterns = [
    path('informacion', views.mapa_informacion, name="mostrar_mapa"),
    path('mapa-interactivo', views.mapa_interactivo, name="mostrar_mapa_int"),
    path('mapa-ejemplo', views.mapa_ejemplo, name="mapa_ejemplo"),
    path('carga-datos', views.carga_datos, name="carga_datos"),
    path('carga-nacionalidades', views.carga_nacionalidades, name="carga_nacionalidades"),
    path('carga-oficinas', views.carga_oficinas, name="carga_oficinas"),
    
    path('titulares', views.titulares_list, name="titulares_list"),
    path('carga-datos-batch', views.carga_datos_batch, name="carga_datos_batch"),
    path('api/periodo-custom', views.api_periodo_custom, name="api_periodo_custom"),
    path('api/nacionalidad-ranking', views.api_nacionalidad_ranking, name="api_nacionalidad_ranking"),
    path('api/reporte-nacionalidades', views.api_reporte_nacionalidades, name="api_reporte_nacionalidades"),
    path('reportes', views.reportes, name="reportes"),
    path('guardar-titular', views.guardar_titular, name="guardar_titular"),
    path('eliminar-titular/<int:titular_id>', views.eliminar_titular, name="eliminar_titular"),
    path('api/get-titular/<int:titular_id>', views.api_get_titular, name="api_get_titular"),
    path('personal', views.personal_list, name="personal_list"),
    path('carga-rapida-personal', views.carga_rapida_personal, name="carga_rapida_personal"),
    path('guardar-personal', views.guardar_personal, name="guardar_personal"),
    path('eliminar-personal/<int:personal_id>', views.eliminar_personal, name="eliminar_personal"),
    path('api/get-personal/<int:personal_id>', views.api_get_personal, name="api_get_personal"),
    path('inmuebles', views.inmuebles_list, name="inmuebles_list"),
    path('guardar-inmueble', views.guardar_inmueble, name="guardar_inmueble"),
    path('eliminar-inmueble/<int:inmueble_id>', views.eliminar_inmueble, name="eliminar_inmueble"),
    path('api/get-inmueble/<int:inmueble_id>', views.api_get_inmueble, name="api_get_inmueble"),
    path('api/guardar-comodato', views.api_guardar_comodato, name="api_guardar_comodato"),
    
    path('organigramas', views.organigramas_list, name="organigramas_list"),
    path('guardar-organigrama', views.guardar_organigrama, name="guardar_organigrama"),
    path('eliminar-organigrama/<int:org_id>', views.eliminar_organigrama, name="eliminar_organigrama"),
    path('api/get-organigrama/<int:estado_id>', views.api_get_organigrama, name="api_get_organigrama"),
    path('api/get-inmueble-detalle/<int:inmueble_id>', views.api_get_inmueble_detalle, name="api_get_inmueble_detalle"),
]