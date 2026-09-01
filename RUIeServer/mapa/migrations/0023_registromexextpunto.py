# @FADAR
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mapa', '0022_situacionveh_vehiculosor_situacion'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistroMexExtPunto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(db_index=True)),
                ('estado', models.CharField(choices=[('BAJA CALIFORNIA', 'Baja California'), ('SONORA', 'Sonora'), ('CHIHUAHUA', 'Chihuahua'), ('COAHUILA', 'Coahuila'), ('TAMAULIPAS', 'Tamaulipas')], db_index=True, max_length=50)),
                ('punto', models.CharField(choices=[('TIJUANA', 'Tijuana'), ('MEXICALI', 'Mexicali'), ('SAN LUIS RÍO COLORADO', 'San Luis Río Colorado'), ('NOGALES', 'Nogales'), ('AGUA PRIETA', 'Agua Prieta'), ('CIUDAD JUÁREZ', 'Ciudad Juárez'), ('OJINAGA', 'Ojinaga'), ('CIUDAD ACUÑA', 'Ciudad Acuña'), ('PIEDRAS NEGRAS', 'Piedras Negras'), ('NUEVO LAREDO', 'Nuevo Laredo'), ('REYNOSA', 'Reynosa'), ('MATAMOROS', 'Matamoros')], max_length=50)),
                ('categoria', models.CharField(choices=[('MEX', 'Mexicano'), ('EXT', 'Extranjero')], max_length=3)),
                ('hombres', models.IntegerField(default=0)),
                ('mujeres', models.IntegerField(default=0)),
                ('ninos', models.IntegerField(default=0)),
                ('ninas', models.IntegerField(default=0)),
                ('nacionalidad', models.ForeignKey(blank=True, help_text='Solo aplica si categoria=Extranjero', null=True, on_delete=django.db.models.deletion.CASCADE, to='mapa.nacionalidad')),
            ],
            options={
                'verbose_name': 'Registro Mex/Ext por Punto',
                'verbose_name_plural': 'Registros Mex/Ext por Punto',
            },
        ),
    ]
