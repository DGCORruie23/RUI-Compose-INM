from django.db import models

class Estado(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"

class Nacionalidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Nacionalidad"
        verbose_name_plural = "Nacionalidades"

class Repatriados(models.Model):
    fecha = models.DateField(db_index=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    nacionalidad = models.ForeignKey(Nacionalidad, on_delete=models.CASCADE, null=True, blank=True)
    mex_rep = models.IntegerField(default=0, verbose_name="Mexicanos Repatriados")
    adultos = models.IntegerField(default=0)
    menores = models.IntegerField(default=0)
    nna_solo = models.IntegerField(default=0, verbose_name="NNA No Acompañados")
    nna_acom = models.IntegerField(default=0, verbose_name="NNA Acompañados")
    terrestres = models.IntegerField(default=0)
    vuelos = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.estado.nombre} - {self.nacionalidad.nombre} - {self.fecha}"

    class Meta:
        verbose_name = "Repatriado"
        verbose_name_plural = "Repatriados"
        unique_together = ['fecha', 'estado', 'nacionalidad']

class Recibidos(models.Model):
    fecha = models.DateField(db_index=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    nacionalidad = models.ForeignKey(Nacionalidad, on_delete=models.CASCADE, null=True, blank=True)
    ext_rec= models.IntegerField(default=0, verbose_name="Extranjeros Recibidos")
    adultos = models.IntegerField(default=0)
    menores = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.estado.nombre} - {self.nacionalidad.nombre} - {self.fecha}"

    class Meta:
        verbose_name = "Recibido"
        verbose_name_plural = "Recibidos"
        unique_together = ['fecha', 'estado', 'nacionalidad']

class ExtRescatados(models.Model):
    fecha = models.DateField(db_index=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    nacionalidad = models.ForeignKey(Nacionalidad, on_delete=models.CASCADE, null=True, blank=True)
    rescatados = models.IntegerField(default=0)
    una_vez = models.IntegerField(default=0)
    reincidente = models.IntegerField(default=0)
    estacion = models.IntegerField(default=0)
    dif = models.IntegerField(default=0)
    conduccion = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.estado.nombre} - {self.nacionalidad.nombre} - {self.fecha}"

    class Meta:
        verbose_name = "Extranjero Rescatado"
        verbose_name_plural = "Extranjeros Rescatados"
        unique_together = ['fecha', 'estado', 'nacionalidad']

class Ingresos(models.Model):
    fecha = models.DateField(db_index=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    nacionalidad = models.ForeignKey(Nacionalidad, on_delete=models.CASCADE, null=True, blank=True)
    ingresos_total = models.IntegerField(default=0)
    aereos = models.IntegerField(default=0)
    maritimos = models.IntegerField(default=0)
    terrestres = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.estado.nombre} - {self.nacionalidad.nombre} - {self.fecha}"

    class Meta:
        verbose_name = "Ingreso"
        verbose_name_plural = "Ingresos"
        unique_together = ['fecha', 'estado', 'nacionalidad']

class Tramites(models.Model):
    fecha = models.DateField(db_index=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    nacionalidad = models.ForeignKey(Nacionalidad, on_delete=models.CASCADE, null=True, blank=True)
    total_documentos = models.IntegerField(default=0)
    residente_permanente = models.IntegerField(default=0)
    residente_temporal = models.IntegerField(default=0)
    residente_temp_estudio = models.IntegerField(default=0)
    visitante_humanitario = models.IntegerField(default=0)
    visitante_adopcion = models.IntegerField(default=0)
    visitante_regional = models.IntegerField(default=0)
    visitante_trabajador = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.estado.nombre} - {self.nacionalidad.nombre} - {self.fecha}"

    class Meta:
        verbose_name = "Trámite"
        verbose_name_plural = "Trámites"
        unique_together = ['fecha', 'estado', 'nacionalidad']

class Retornados(models.Model):
    fecha = models.DateField(db_index=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    nacionalidad = models.ForeignKey(Nacionalidad, on_delete=models.CASCADE, null=True, blank=True)
    retornados_total = models.IntegerField(default=0)
    deportado = models.IntegerField(default=0)
    retornado = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.estado.nombre} - {self.nacionalidad.nombre} - {self.fecha}"

    class Meta:
        verbose_name = "Retornado"
        verbose_name_plural = "Retornados"
        unique_together = ['fecha', 'estado', 'nacionalidad']

class Inadmitidos(models.Model):
    fecha = models.DateField(db_index=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    nacionalidad = models.ForeignKey(Nacionalidad, on_delete=models.CASCADE, null=True, blank=True)
    inadmitidos_total = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.estado.nombre} - {self.nacionalidad.nombre} - {self.fecha}"

    class Meta:
        verbose_name = "Inadmitido"
        verbose_name_plural = "Inadmitidos"
        unique_together = ['fecha', 'estado', 'nacionalidad']