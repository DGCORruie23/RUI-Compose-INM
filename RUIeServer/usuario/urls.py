from django.urls import path, include
from usuario import views

urlpatterns = [
    path('cargarPais', views.cargarPais, name="cargar_pais"),
    path('cargarFuerza', views.cargarEdoFuerza, name="cargar_fuerza"),
    #path('dashboard/', views.cargarEdoF, name="cargar_f"),
    path('cargarMunicipios', views.cargarMunicipios, name="cargar_municipios"),
    path('cargarPuntosI', views.cargarPuntoI, name="cargar_puntoI"),
    path('cargarInadmitidos', views.cargarInadmitidos, name="cargar_Inadmitidos"),

    path('Usuarios', views.cargaMasivaUser, name="cargar_usuarios"),
    path('Paises', views.infoPaises),
    path('Fuerza', views.infoEstadoFuerza),
    path('Municipios', views.infoMunicipios),
    path('PuntosI', views.infoPuntosInterna),
    path('frases', views.infoFrases),
    
    path('fechas', views.generarExcelFechas, name="fechas_descarga"),
    path('fechasOR', views.generarExcelFechasOR, name="fechas_OR"),

    path('descargaN', views.generarExcelNombres),
    path('descargaC', views.generarExcelConteo),
    path('descargaD', views.pagDuplicados),

    path('descargaD_a', views.downloadDuplicados, name="descarga_duplicados"),
    path('descargaTab22', views.generarExcelTab),
    path('descargaExcel', views.generarExcelORs, name="descarga_excel"),
    path('descargaExcelUsuarios', views.generarExcelUsuarios, name="descarga_excelUsuarios"),
    path('descargaExcelEdoFuerza', views.generarExcelEdoFuerza, name="descarga_excelEdoFuerza"),
    path('descargaExcelPuntosI', views.generarExcelPuntosI, name="descarga_excelPuntosI"),

    path('updateApp', views.msgUpdateUrl, name="info_app"),

    path('politica_privacidad', views.politica_privacidad, name="info_politica_privacidad"),

]
