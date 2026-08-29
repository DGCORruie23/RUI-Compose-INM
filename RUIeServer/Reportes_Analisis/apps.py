# @FADAR -- app creada para alojar el dashboard y los reportes de rescates,
# trasladados desde la app "mapa".
from django.apps import AppConfig


class ReportesAnalisisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Reportes_Analisis'
