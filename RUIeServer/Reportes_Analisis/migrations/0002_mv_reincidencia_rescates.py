# @FADAR -- adopta la vista materializada mapa_mv_reincidencia_rescates
# (creada originalmente por una migracion que se retira de mapa) sin tocar
# la base de datos: la vista y sus 900k+ filas ya existen, esto solo mueve
# el registro de la migracion a esta app. El DROP real solo corre si algun
# dia se revierte esta migracion.
from django.db import migrations

DROP_MV = "DROP MATERIALIZED VIEW IF EXISTS mapa_mv_reincidencia_rescates;"


class Migration(migrations.Migration):

    dependencies = [
        ('Reportes_Analisis', '0001_initial'),
        ('usuario', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(sql=migrations.RunSQL.noop, reverse_sql=DROP_MV),
    ]
