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

class PuntosInternacionEstacion(models.Model):
    nombre = models.CharField(max_length=100)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    tipo = models.CharField(max_length=100, choices=[('AEREO', 'AEREO'), ('MARITIMO', 'MARITIMO'), ('TERRESTRE', 'TERRESTRE'), ('ESTACION', 'ESTACION')])
    latitud = models.FloatField()
    longitud = models.FloatField()
    
    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

    class Meta:
        verbose_name = "Punto de Internacion"
        verbose_name_plural = "Puntos de Internacion"
        unique_together = ['nombre', 'tipo']

class TipoPRH(models.Model):
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Tipo PRH"
        verbose_name_plural = "Tipos de PRHs"

class PRHs(models.Model):
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    nombre = models.CharField(max_length=100)
    modalidad = models.ForeignKey(TipoPRH, on_delete=models.CASCADE, db_index=True)
    activo = models.BooleanField(default=False)
    coordenadasTexto = models.CharField(max_length=100)
    latitud = models.FloatField()
    longitud = models.FloatField()
    
    def __str__(self):
        return f"{self.estado.nombre} - {self.activo} -{self.nombre} ({self.modalidad})"

    class Meta:
        verbose_name = "Punto de Rescate"
        verbose_name_plural = "Puntos de Rescates"

class CatalogoOR(models.Model):
    titular = models.CharField(max_length=100, unique=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    domicilio = models.CharField(max_length=300)
    correo = models.CharField(max_length=100)
    
    def __str__(self):
        return self.titular

    class Meta:
        verbose_name = "Catalogo OR"
        verbose_name_plural = "Catalogo ORs"

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

class Encuentros(models.Model):
    fecha = models.DateField(db_index=True)
    agencia = models.CharField(max_length=100, db_index=True)
    ciudadEU = models.CharField(max_length=100, db_index=True)
    estadoEU = models.CharField(max_length=100, db_index=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    nacionalidad = models.ForeignKey(Nacionalidad, on_delete=models.CASCADE, null=True, blank=True)
    encuentros_total = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.fecha} - {self.agencia} - {self.estadoEU} - {self.nacionalidad.nombre} - {self.encuentros_total}"

    class Meta:
        verbose_name = "Encuentro"
        verbose_name_plural = "Encuentros"
        unique_together = ['fecha', 'agencia', 'ciudadEU', 'estadoEU', 'estado', 'nacionalidad']

#---------------------------------------------------------------------
#Modelos para Titulares, Estudios, Telefonos, Trayectorias y Experiencias
#---------------------------------------------------------------------
class TipoProcendencia(models.Model):
    institucion = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.institucion

    class Meta:
        verbose_name = "Procedencia"
        verbose_name_plural = "Procedencia"

class GradoAcademico(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Grado Académico"
        verbose_name_plural = "Grados Académicos"

class TipoNombramiento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Tipo de Nombramiento"
        verbose_name_plural = "Tipos de Nombramientos"

class Titular(models.Model):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('X', 'Otro'),
    ]

    fotografia = models.ImageField(upload_to='titulares', null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    curp = models.CharField(max_length=18, unique=True)
    nacionalidad = models.ForeignKey(Nacionalidad, on_delete=models.CASCADE, null=True, blank=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    nivel = models.CharField(max_length=20)
    codigo_plaza = models.CharField(max_length=20, unique=True, null=True, blank=True)
    tipo_nombramiento = models.ForeignKey(TipoNombramiento, on_delete=models.PROTECT, blank=True, null=True)
    procedencia = models.ForeignKey(TipoProcendencia, on_delete=models.PROTECT, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"

    class Meta:
        verbose_name = "Titular"
        verbose_name_plural = "Titulares"

class Estudio(models.Model):
    titular = models.ForeignKey(Titular, on_delete=models.CASCADE, related_name='estudios')
    grado = models.ForeignKey(GradoAcademico, on_delete=models.PROTECT)
    carrera = models.CharField(max_length=150)
    institucion = models.CharField(max_length=200, null=True, blank=True)
    fecha_conclusion = models.DateField(null=True, blank=True)
    documento_estudio = models.FileField(upload_to='estudios', null=True, blank=True)
    
    def __str__(self):
        return f"{self.grado.nombre} en {self.carrera}"

    class Meta:
        verbose_name = "Estudio"
        verbose_name_plural = "Estudios"

class TelefonoTitular(models.Model):
    TIPO_CHOICES = [
        ('PERSONAL', 'Personal'),
        ('OFICINA', 'Oficina'),
        ('ASISTENTE', 'Asistente'),
        ('EMERGENCIA', 'Emergencia'),
        ('OTRO', 'Otro'),
    ]
    titular = models.ForeignKey(Titular, on_delete=models.CASCADE, related_name='telefonos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    numero = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.tipo}: {self.numero}"

    class Meta:
        verbose_name = "Teléfono de contacto"
        verbose_name_plural = "Teléfonos de contacto"

class CorreoTitular(models.Model):
    TIPO_CHOICES = [
        ('PERSONAL', 'Personal'),
        ('INSTITUCIONAL', 'Institucional'),
        ('OTRO', 'Otro'),
    ]
    titular = models.ForeignKey(Titular, on_delete=models.CASCADE, related_name='correos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    correo = models.EmailField()

    def __str__(self):
        return self.correo

    class Meta:
        verbose_name = "Correo electrónico"
        verbose_name_plural = "Correos electrónicos"

class TrayectoriaLaboral(models.Model):
    titular = models.ForeignKey(Titular, on_delete=models.CASCADE, related_name='trayectoria')
    puesto = models.CharField(max_length=150)
    area = models.CharField(max_length=150)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    actual = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.puesto} en {self.area}"

    class Meta:
        verbose_name = "Trayectoria Laboral"
        verbose_name_plural = "Trayectorias Laborales"

class ExperienciaProfesional(models.Model):
    titular = models.ForeignKey(Titular, on_delete=models.CASCADE, related_name='experiencia_externa')
    institucion = models.CharField(max_length=150)
    cargo = models.CharField(max_length=150)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.cargo} en {self.institucion}"

    class Meta:
        verbose_name = "Experiencia Profesional"
        verbose_name_plural = "Experiencias Profesionales"

#---------------------------------------------------------------------
# Inmueble 
#---------------------------------------------------------------------

class Comodato(models.Model):
    nombre = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Comodato"
        verbose_name_plural = "Comodatos"

class FiguraOcupacion(models.Model):
    tipo = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.tipo

    class Meta:
        verbose_name = "Figura de Ocupación"
        verbose_name_plural = "Figuras de Ocupación"


class TipoInmueble(models.Model):
    nombre = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Tipo de Inmueble"
        verbose_name_plural = "Tipos de Inmuebles"

class SituacionActual(models.Model):
    nombre = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Situación Actual"
        verbose_name_plural = "Situaciones Actuales"

class TipoActividad(models.Model):
    nombre = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Tipo de Actividad"
        verbose_name_plural = "Tipos de Actividades"

class Inmueble(models.Model):

    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    nombre_inmueble = models.CharField(max_length=200)
    calle = models.CharField(max_length=200)
    numero_exterior = models.CharField(max_length=10)
    numero_interior = models.CharField(max_length=10)
    colonia = models.CharField(max_length=200)
    municipio = models.CharField(max_length=200)
    codigo_postal = models.CharField(max_length=5)

    latitud = models.FloatField()
    longitud = models.FloatField()

    tipo_actividad = models.ForeignKey(TipoActividad, on_delete=models.PROTECT, blank=True, null=True)
    situacion_actual = models.ForeignKey(SituacionActual, on_delete=models.PROTECT, blank=True, null=True)
    tipo_inmueble = models.ForeignKey(TipoInmueble, on_delete=models.PROTECT, blank=True, null=True)
    
    superficie_total = models.FloatField()
    superficie_construida = models.FloatField()
    superficie_utilizada = models.FloatField()
    numero_de_niveles = models.IntegerField()
    anio_construccion = models.IntegerField()

    fecha_ocupacion = models.DateField(null=True, blank=True)

    figura_ocupacion = models.ForeignKey(FiguraOcupacion, on_delete=models.PROTECT, blank=True, null=True)

    monto_renta = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    
    comodato = models.ForeignKey(Comodato, on_delete=models.PROTECT, blank=True, null=True)
    vigencia_pipc = models.DateField(null=True, blank=True)

    observaciones = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - {self.nombre_inmueble} - {self.municipio} - {self.tipo_actividad} - {self.situacion_actual}"

    class Meta:
        verbose_name = "Inmueble"
        verbose_name_plural = "Inmuebles"