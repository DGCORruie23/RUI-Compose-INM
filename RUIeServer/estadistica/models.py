from django.db import models
from mapa.models import Estado, TipoPRH

# Create your models here.

class Mapa_PRH(models.Model):
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    nombre = models.CharField(max_length=250)
    modalidad = models.ForeignKey(TipoPRH, on_delete=models.CASCADE, db_index=True)
    activo = models.BooleanField(default=False)
    latitud = models.FloatField()
    longitud = models.FloatField()
    rescates = models.IntegerField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.estado.nombre} - {self.activo} -{self.nombre} ({self.modalidad})"

    class Meta:
        verbose_name = "Datos Mapa Rescate x PRH"
        verbose_name_plural = "Datos Mapa Rescates x PRHs"