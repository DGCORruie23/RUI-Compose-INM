# @FADAR -- namespaced ('Reportes_Analisis:') para no chocar con los
# mismos nombres de url que aun viven en mapa/urls.py mientras dura el
# traslado por fases.
from django.urls import path
from Reportes_Analisis import views

app_name = 'Reportes_Analisis'

urlpatterns = [
    path('rescates', views.rescates_dashboard, name="rescates_dashboard"),

    # @FADAR -- Regiones (CECO): widget/detalle interactivo + reporte formal
    path('rescates/regiones', views.rescates_regiones, name="rescates_regiones"),
    path('rescates/reporte/regiones', views.rescates_reporte_regiones, name="rescates_reporte_regiones"),
    path('rescates/reporte/regiones/pdf', views.rescates_reporte_regiones_pdf, name="rescates_reporte_regiones_pdf"),
    path('rescates/reporte/regiones/excel', views.rescates_reporte_regiones_excel, name="rescates_reporte_regiones_excel"),

    # @FADAR -- Cuadro de Datos
    path('rescates/reporte/cuadro', views.rescates_reporte_cuadro, name="rescates_reporte_cuadro"),
    path('rescates/reporte/cuadro/pdf', views.rescates_reporte_cuadro_pdf, name="rescates_reporte_cuadro_pdf"),
    path('rescates/reporte/cuadro/excel', views.rescates_reporte_cuadro_excel, name="rescates_reporte_cuadro_excel"),

    # @FADAR -- Informe Diario
    path('rescates/reporte/informe', views.rescates_reporte_informe, name="rescates_reporte_informe"),
    path('rescates/reporte/informe/pdf', views.rescates_reporte_informe_pdf, name="rescates_reporte_informe_pdf"),
    path('rescates/reporte/informe/excel', views.rescates_reporte_informe_excel, name="rescates_reporte_informe_excel"),

    # @FADAR -- CECO 2
    path('rescates/reportes/ceco2', views.rescates_reporte_ceco2, name="rescates_reporte_ceco2"),
    path('rescates/reportes/ceco2/pdf', views.rescates_reporte_ceco2_pdf, name="rescates_reporte_ceco2_pdf"),
    path('rescates/reportes/ceco2/excel', views.rescates_reporte_ceco2_excel, name="rescates_reporte_ceco2_excel"),

    # @FADAR -- CECO V1/V2
    path('rescates/reportes/ceco-v1', views.rescates_reporte_cecov1, name="rescates_reporte_cecov1"),
    path('rescates/reportes/ceco-v1/pdf', views.rescates_reporte_cecov1_pdf, name="rescates_reporte_cecov1_pdf"),
    path('rescates/reportes/ceco-v1/excel', views.rescates_reporte_cecov1_excel, name="rescates_reporte_cecov1_excel"),
    path('rescates/reportes/ceco-v2', views.rescates_reporte_cecov2, name="rescates_reporte_cecov2"),
    path('rescates/reportes/ceco-v2/pdf', views.rescates_reporte_cecov2_pdf, name="rescates_reporte_cecov2_pdf"),
    path('rescates/reportes/ceco-v2/excel', views.rescates_reporte_cecov2_excel, name="rescates_reporte_cecov2_excel"),

    # @FADAR -- Reporte Personalizado
    path('rescates/reportes/personalizado', views.rescates_reporte_personalizado, name="rescates_reporte_personalizado"),
    path('rescates/reportes/personalizado/pdf', views.rescates_reporte_personalizado_pdf, name="rescates_reporte_personalizado_pdf"),
    path('rescates/reportes/personalizado/excel', views.rescates_reporte_personalizado_excel, name="rescates_reporte_personalizado_excel"),

    # @FADAR -- Mexicanos vs Extranjeros (nunca vivio en esta ubicacion, traido de Desarrollo)
    path('rescates/reportes/mexicanos-extranjeros', views.reporte_mex_extranjeros, name="reporte_mex_extranjeros"),
    path('rescates/reportes/mexicanos-extranjeros/pdf', views.reporte_mex_extranjeros_pdf, name="reporte_mex_extranjeros_pdf"),
    path('rescates/reportes/mexicanos-extranjeros/excel', views.reporte_mex_extranjeros_excel, name="reporte_mex_extranjeros_excel"),
]
