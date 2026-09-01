# @FADAR
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mapa', '0023_registromexextpunto'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='registromexextpunto',
            constraint=models.UniqueConstraint(condition=models.Q(('categoria', 'MEX')), fields=('fecha', 'punto', 'categoria'), name='unico_mex_por_punto_fecha'),
        ),
        migrations.AddConstraint(
            model_name='registromexextpunto',
            constraint=models.UniqueConstraint(condition=models.Q(('categoria', 'EXT')), fields=('fecha', 'punto', 'categoria', 'nacionalidad'), name='unico_ext_por_punto_fecha_nacionalidad'),
        ),
    ]
