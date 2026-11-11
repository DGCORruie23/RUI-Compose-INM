# Generated manually — 2026-06-17
# Cambia el campo 'actividad' de ForeignKey a ManyToManyField en PersonalINM

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mapa', '0018_personalinm_fecha_nacimiento_personalinm_sexo'),
    ]

    operations = [
        # Paso 1: Eliminar el campo ForeignKey original
        migrations.RemoveField(
            model_name='personalinm',
            name='actividad',
        ),
        # Paso 2: Agregar el nuevo campo ManyToManyField
        migrations.AddField(
            model_name='personalinm',
            name='actividad',
            field=models.ManyToManyField(blank=True, to='mapa.tipoactividad'),
        ),
    ]
