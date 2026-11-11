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
    path('api/get-inmueble-detalle/<int:inmueble_id>', views.api_get_inmueble_detalle, name="api_get_inmueble_detalle"),
    path('api/get-estado-detalle/<int:estado_id>', views.api_get_estado_detalle, name="api_get_estado_detalle"),
    path('api/get-personal-stats/<int:estado_id>', views.api_get_personal_stats, name="api_get_personal_stats"),
    
    path('organigramas', views.organigramas_list, name="organigramas_list"),
    path('guardar-organigrama', views.guardar_organigrama, name="guardar_organigrama"),
    path('eliminar-organigrama/<int:org_id>', views.eliminar_organigrama, name="eliminar_organigrama"),
    path('api/get-organigrama/<int:estado_id>', views.api_get_organigrama, name="api_get_organigrama"),
    
    path('vehiculos', views.vehiculos_list, name="vehiculos_list"),
    path('guardar-vehiculo', views.guardar_vehiculo, name="guardar_vehiculo"),
    path('eliminar-vehiculo/<int:vehiculo_id>', views.eliminar_vehiculo, name="eliminar_vehiculo"),
    path('api/get-vehiculo/<int:vehiculo_id>', views.api_get_vehiculo, name="api_get_vehiculo"),
    
    path('api/get-vehiculo-historial/<int:vehiculo_id>', views.api_get_vehiculo_historial, name="api_get_vehiculo_historial"),
    path('guardar-kilometraje', views.guardar_kilometraje, name="guardar_kilometraje"),
    path('guardar-prestado', views.guardar_prestado, name="guardar_prestado"),
    path('guardar-siniestro', views.guardar_siniestro, name="guardar_siniestro"),
    path('guardar-capufe', views.guardar_capufe, name="guardar_capufe"),
    path('guardar-combustible', views.guardar_combustible, name="guardar_combustible"),
    
    path('prhs', views.prhs_list, name="prhs_list"),
    path('guardar-prh', views.guardar_prh, name="guardar_prh"),
    path('eliminar-prh/<int:prh_id>', views.eliminar_prh, name="eliminar_prh"),
    path('api/get-prh/<int:prh_id>', views.api_get_prh, name="api_get_prh"),
    
    path('puntos-internacion', views.puntos_internacion_list, name="puntos_internacion_list"),
    path('guardar-punto-internacion', views.guardar_punto_internacion, name="guardar_punto_internacion"),
    path('eliminar-punto-internacion/<int:punto_id>', views.eliminar_punto_internacion, name="eliminar_punto_internacion"),
    path('api/get-punto-internacion/<int:punto_id>', views.api_get_punto_internacion, name="api_get_punto_internacion"),
]