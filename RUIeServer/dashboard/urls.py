from django.urls import path
from . import views

urlpatterns = [
     path('', views.dashboard, name="dashboard"),
     path('datos/', views.mostrarData, name="mostrar"),
     path('editar/<int:pk>', views.editarData, name="editar"),
     path('datos/fecha', views.datos_fecha, name="datos_por_fecha"),
     path('datos/fechas', views.datos_fechas, name="datos_por_fechas"),
     path('datos/eliminarM', views.eliminar_registros, name="eliminar_varios_registros"),
     path('datos/<int:year>/<int:month>/<int:day>/', views.tabla_registros, name='tabla_registros_fecha'),


     path('edoFuerza', views.edoFuerza, name="pagina_pruebas_edoFuerza"),
     path('edoFuerza/editarEdoFuerza/<int:id_edo_fuerza>', views.editar_estado_fuerza, name='editar_estado_fuerza'),
     path('edoFuerza/eliminarEdoFuerza/<int:id_edo_fuerza>', views.eliminarEdoFuerza, name='eliminar_estado_fuerza'),
     path('edoFuerza/anadirPunto', views.agregar_punto, name='agregar_punto'),

     path('puntosI', views.puntosI, name="paginaPuntosI"),
     path('puntosI/anadirPuntoInternacion', views.agregar_puntoInternacion, name='agregar_puntoInternacion'),
     path('puntosI/editarPuntoI/<int:id_puntoI>', views.editar_puntoInternacion, name='editar_puntoI'),
     path('puntosI/eliminarPuntoI/<int:id_puntoI>', views.eliminarPuntoI, name='eliminar_PuntoI'),

     path('usuarios', views.Usuarios, name="pagina_pruebas_usuarios"),
     path('usuarios/editarUsuario/<int:id_usuario>', views.editar_usuario, name='editar_usuario'),
     path('usuarios/anadirUsuario', views.agregar_usuario, name='agregar_usuario'),
     path('usuarios/eliminarUsuario/<int:id_usuario>', views.eliminarUsuario, name='eliminar_usuario'),
]

