from django.urls import path
from Reportes_Analisis import views

app_name = 'Reportes_Analisis'

urlpatterns = [
    path('rescates', views.rescates_dashboard, name="rescates_dashboard"),
    path('rescates/pdf', views.rescates_dashboard_pdf, name="rescates_dashboard_pdf"),

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

    # @FADAR -- CECO 2.1 (copia de CECO 2, solo primera vez, sin reincidentes)
    path('rescates/reportes/ceco2-1', views.rescates_reporte_ceco21, name="rescates_reporte_ceco21"),
    path('rescates/reportes/ceco2-1/pdf', views.rescates_reporte_ceco21_pdf, name="rescates_reporte_ceco21_pdf"),
    path('rescates/reportes/ceco2-1/excel', views.rescates_reporte_ceco21_excel, name="rescates_reporte_ceco21_excel"),

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

    # @FADAR -- Reporte especial de nacionalidades (lista fija de 4 paises)
    path('rescates/reportes/nacionalidades-especiales', views.rescates_reporte_nacionalidades_especiales, name="rescates_reporte_nacionalidades_especiales"),
    path('rescates/reportes/nacionalidades-especiales/pdf', views.rescates_reporte_nacionalidades_especiales_pdf, name="rescates_reporte_nacionalidades_especiales_pdf"),
    path('rescates/reportes/nacionalidades-especiales/excel', views.rescates_reporte_nacionalidades_especiales_excel, name="rescates_reporte_nacionalidades_especiales_excel"),

    # @FADAR -- Nacionalidades extracontinentales (lista dinamica, solo con registros)
    path('rescates/reportes/nacionalidades-extracontinentales', views.rescates_reporte_nacionalidades_extracontinentales, name="rescates_reporte_nacionalidades_extracontinentales"),
    path('rescates/reportes/nacionalidades-extracontinentales/pdf', views.rescates_reporte_nacionalidades_extracontinentales_pdf, name="rescates_reporte_nacionalidades_extracontinentales_pdf"),
    path('rescates/reportes/nacionalidades-extracontinentales/excel', views.rescates_reporte_nacionalidades_extracontinentales_excel, name="rescates_reporte_nacionalidades_extracontinentales_excel"),

    # @FADAR -- Disuadidos (formato CECO2, usa casaSeguridad como regla de negocio de facto)
    path('rescates/reportes/disuadidos', views.rescates_reporte_disuadidos, name="rescates_reporte_disuadidos"),
    path('rescates/reportes/disuadidos/pdf', views.rescates_reporte_disuadidos_pdf, name="rescates_reporte_disuadidos_pdf"),
    path('rescates/reportes/disuadidos/excel', views.rescates_reporte_disuadidos_excel, name="rescates_reporte_disuadidos_excel"),

    # @FADAR -- Mexicanos vs Extranjeros
    path('rescates/reportes/mexicanos-extranjeros', views.reporte_mex_extranjeros, name="reporte_mex_extranjeros"),
    path('rescates/reportes/mexicanos-extranjeros/pdf', views.reporte_mex_extranjeros_pdf, name="reporte_mex_extranjeros_pdf"),
    path('rescates/reportes/mexicanos-extranjeros/excel', views.reporte_mex_extranjeros_excel, name="reporte_mex_extranjeros_excel"),

    # @FADAR -- Rescates vía ferrocarril (analisis de ruta, no un reporte operativo diario)
    path('rescates/reportes/ferrocarril', views.rescates_reporte_ferrocarril, name="rescates_reporte_ferrocarril"),
    path('rescates/reportes/ferrocarril/pdf', views.rescates_reporte_ferrocarril_pdf, name="rescates_reporte_ferrocarril_pdf"),
    path('rescates/reportes/ferrocarril/excel', views.rescates_reporte_ferrocarril_excel, name="rescates_reporte_ferrocarril_excel"),
]
