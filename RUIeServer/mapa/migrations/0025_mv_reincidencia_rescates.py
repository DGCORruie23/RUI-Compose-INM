# @FADAR
from django.db import migrations

# Reincidente = misma persona (nombre, apellidos, nacionalidad) con >=2
# apariciones en TODO el historico de usuario_rescatepunto. Antes esto se
# calculaba en Python (GROUP BY + set, cacheado 20 min); ahora vive como
# vista materializada en Postgres -- no toca ningun indice/columna de
# usuario_rescatepunto, solo agrega un objeto nuevo.
CREATE_MV = """
CREATE MATERIALIZED VIEW mapa_mv_reincidencia_rescates AS
SELECT
    nombre,
    apellidos,
    nacionalidad,
    COUNT(*) AS veces,
    CASE WHEN COUNT(*) >= 2 THEN 'Reincidente' ELSE 'Rescate primera vez' END AS clasificacion
FROM usuario_rescatepunto
GROUP BY nombre, apellidos, nacionalidad
WITH DATA;

CREATE UNIQUE INDEX mapa_mv_reincidencia_rescates_uniq
    ON mapa_mv_reincidencia_rescates (nombre, apellidos, nacionalidad);
"""

DROP_MV = "DROP MATERIALIZED VIEW IF EXISTS mapa_mv_reincidencia_rescates;"


class Migration(migrations.Migration):

    dependencies = [
        ('mapa', '0024_registromexextpunto_constraints'),
    ]

    operations = [
        migrations.RunSQL(sql=CREATE_MV, reverse_sql=DROP_MV),
    ]
