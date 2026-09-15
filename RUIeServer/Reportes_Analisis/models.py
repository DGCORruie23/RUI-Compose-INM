from django.db import models

from mapa.models import Nacionalidad

CATALOGO_PUNTOS_MEX_EXT = {
    "BAJA CALIFORNIA": ["TIJUANA", "MEXICALI"],
    "SONORA": ["SAN LUIS RÍO COLORADO", "NOGALES", "AGUA PRIETA"],
    "CHIHUAHUA": ["CIUDAD JUÁREZ", "OJINAGA"],
    "COAHUILA": ["CIUDAD ACUÑA", "PIEDRAS NEGRAS"],
    "TAMAULIPAS": ["NUEVO LAREDO", "REYNOSA", "MATAMOROS"],
}


class RegistroMexExtPunto(models.Model):
    CATEGORIA_CHOICES = [('MEX', 'Mexicano'), ('EXT', 'Extranjero')]
    ESTADO_CHOICES = [(e, e.title()) for e in CATALOGO_PUNTOS_MEX_EXT]
    PUNTO_CHOICES = [(p, p.title()) for lista in CATALOGO_PUNTOS_MEX_EXT.values() for p in lista]

    fecha = models.DateField(db_index=True)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, db_index=True)
    punto = models.CharField(max_length=50, choices=PUNTO_CHOICES)
    categoria = models.CharField(max_length=3, choices=CATEGORIA_CHOICES)
    nacionalidad = models.ForeignKey(Nacionalidad, on_delete=models.CASCADE, null=True, blank=True,
                                      help_text="Solo aplica si categoria=Extranjero")
    hombres = models.IntegerField(default=0)
    mujeres = models.IntegerField(default=0)
    ninos = models.IntegerField(default=0)
    ninas = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.punto} ({self.estado}) - {self.get_categoria_display()} - {self.fecha}"

    class Meta:
        verbose_name = "Registro Mex/Ext por Punto"
        verbose_name_plural = "Registros Mex/Ext por Punto"
        constraints = [
            models.UniqueConstraint(
                fields=['fecha', 'punto', 'categoria'],
                condition=models.Q(categoria='MEX'),
                name='unico_mex_por_punto_fecha',
            ),
            models.UniqueConstraint(
                fields=['fecha', 'punto', 'categoria', 'nacionalidad'],
                condition=models.Q(categoria='EXT'),
                name='unico_ext_por_punto_fecha_nacionalidad',
            ),
        ]
