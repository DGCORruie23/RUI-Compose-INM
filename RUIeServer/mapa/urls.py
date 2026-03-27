from django.urls import path, include
from mapa import views

urlpatterns = [
    path('informacion', views.mapa_informacion, name="mostrar_mapa"),
    path('carga-datos', views.carga_datos, name="carga_datos"),
]