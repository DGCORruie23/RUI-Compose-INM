from django.urls import path
from . import views

urlpatterns = [
     path('', views.estadistica, name="estadistica"),
     path('buscar/', views.busqueda, name="busqueda"),
     path('reincidencia/', views.reincidencia, name="reincidente"),

#    Consultas en ajax
     path('buscar_rescate/', views.buscar_reincidente_ajax, name='buscar_rescate'),
     path('reincidentes_dia/', views.reincidentes_xdia_ajax, name='reincidencia'),
     path('reincidentes_fechas/', views.reincidentes_xfechas_ajax, name='reincidenciaFechas'),

     path("pdf/", views.generar_pdf, name="generar_pdf"),
     path("pdfT/", views.generar_pdfT, name="generar_pdfT"),
     path("pdf_ceco/", views.generar_pdf_ceco, name="generar_pdf_ceco"),
     path("cuadro_datos/", views.generar_cuadro_diario, name="generar_cuadro_diario"),
     path("excelT/", views.exportar_excel_reporteT, name="exportar_excel_reporteT"),
]