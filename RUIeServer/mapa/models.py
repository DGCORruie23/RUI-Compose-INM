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

# @FADAR -- catalogo "de prueba" a nivel app (no en la base): unica fuente
# de verdad de los 5 estados / 12 puntos, para no mantenerlo duplicado
# entre este modelo y el reporte Mexicanos y Extranjeros (mapa/views.py).
CATALOGO_PUNTOS_MEX_EXT = {
    "BAJA CALIFORNIA": ["TIJUANA", "MEXICALI"],
    "SONORA": ["SAN LUIS RÍO COLORADO", "NOGALES", "AGUA PRIETA"],
    "CHIHUAHUA": ["CIUDAD JUÁREZ", "OJINAGA"],
    "COAHUILA": ["CIUDAD ACUÑA", "PIEDRAS NEGRAS"],
    "TAMAULIPAS": ["NUEVO LAREDO", "REYNOSA", "MATAMOROS"],
}


# @FADAR -- captura real por punto (reemplaza FORMATO_MEX-.xlsm): a
# diferencia de Repatriados/Recibidos (solo estado, adultos/menores), aqui
# se guarda por punto especifico y con Hombres/Mujeres/Ninos/Ninas real.
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
        # @FADAR -- evita captura duplicada. Nacionalidad es NULL en todos
        # los MEX (NULL != NULL en SQL, un unique_together simple no lo
        # cubriria), por eso van 2 constraints condicionadas en vez de una.
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

class TipoDependencia(models.Model):
    actividad = models.ForeignKey('TipoActividad', on_delete=models.CASCADE, related_name='actividad')
    nombre = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Tipo de Dependencia"
        verbose_name_plural = "Tipos de Dependencias"

class TipoActividad(models.Model):
    nombre = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Tipo de Actividad"
        verbose_name_plural = "Tipos de Actividades"

class TipoOficina(models.Model):
    nombre = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Tipo de Oficina"
        verbose_name_plural = "Tipos de Oficinas"

class ProgramaIPC(models.Model):
    inmueble = models.ForeignKey('Inmueble', on_delete=models.CASCADE, related_name='pipc')
    inm_pipc = models.BooleanField(default=False)
    fecha_inm = models.DateField(null=True, blank=True)
    comodante_pipc = models.BooleanField(default=False)
    fecha_comodante = models.DateField(null=True, blank=True)
    plan_emergencia = models.BooleanField(default=False)
    fecha_inicio_plan = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Programa IPC {self.id}"

    class Meta:
        verbose_name = "Programa IPC"
        verbose_name_plural = "Programas IPC"


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

    tipo_oficina = models.ManyToManyField(TipoOficina, blank=True)
    situacion_actual = models.ForeignKey(SituacionActual, on_delete=models.PROTECT, blank=True, null=True)
    tipo_inmueble = models.ForeignKey(TipoInmueble, on_delete=models.PROTECT, blank=True, null=True)
    tipo_actividad = models.ManyToManyField(TipoActividad, blank=True)
    
    superficie_total = models.FloatField()
    superficie_construida = models.FloatField()
    superficie_utilizada = models.FloatField()
    numero_de_niveles = models.IntegerField()
    anio_construccion = models.DateField(null=True, blank=True)

    fecha_ocupacion = models.DateField(null=True, blank=True)

    figura_ocupacion = models.ForeignKey(FiguraOcupacion, on_delete=models.PROTECT, blank=True, null=True)

    monto_renta = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    
    comodato = models.ForeignKey(Comodato, on_delete=models.PROTECT, blank=True, null=True)

    def __str__(self):
        return f"{self.id} - {self.nombre_inmueble} - {self.municipio} - {self.situacion_actual}"

    class Meta:
        verbose_name = "Inmueble"
        verbose_name_plural = "Inmuebles"

class HistoricoComentarios(models.Model):
    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, related_name='comentarios')
    comentario = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario en {self.inmueble.nombre_inmueble} - {self.fecha_creacion.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = "Historial de Comentario"
        verbose_name_plural = "Historial de Comentarios"

#---------------------------------------------------------------------
# Personal
#---------------------------------------------------------------------

class TipoPlaza(models.Model):
    plazaT = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.plazaT

    class Meta:
        verbose_name = "Tipo Plaza"
        verbose_name_plural = "Tipos Plazas"

class EstatusPersonal(models.Model):
    estatus = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.estatus

    class Meta:
        verbose_name = "Estatus P"
        verbose_name_plural = "Estatus P"

class PersonalINM(models.Model):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('X', 'Otro'),
    ]

    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    estatus = models.ForeignKey(EstatusPersonal, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_plaza = models.ForeignKey(TipoPlaza, on_delete=models.SET_NULL, null=True, blank=True)
    codigo_plaza = models.CharField(max_length=20)
    nivel = models.CharField(max_length=4)
    num_empleado = models.CharField(max_length=8, null=True, blank=True)
    nombre = models.CharField(max_length=100, null=True, blank=True)
    apellido = models.CharField(max_length=100, null=True, blank=True)
    curp = models.CharField(max_length=20, null=True, blank=True)
    tipo_movimiento = models.BooleanField(default=True, null=True, blank=True)
    fecha_ingreso_inm = models.DateField(null=True, blank=True)
    fecha_ingreso_plaza = models.DateField(null=True, blank=True)
    vig_inicio_mov = models.DateField(null=True, blank=True)
    vig_termino_mov = models.DateField(null=True, blank=True)
    puesto_especifico = models.CharField(max_length=200)
    sueldo_bruto = models.FloatField(null=True, blank=True)
    sueldo_neto = models.FloatField(null=True, blank=True)
    actividad = models.ManyToManyField(TipoDependencia, blank=True)
    jefe_oficina = models.BooleanField(default=False, null=True, blank=True)
    lugar_asignado = models.ForeignKey('Inmueble', on_delete=models.CASCADE, related_name='inmuebleAsignado', blank=True, null=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre or ''} {self.apellido or ''} - {self.puesto_especifico}"

    class Meta:
        verbose_name = "Personal INM"
        verbose_name_plural = "Personal INM"
        unique_together = ['codigo_plaza']

class OrganigramaF(models.Model):
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    archivo = models.FileField(upload_to='Organigramas', null=True, blank=True)
    vigencia = models.DateField(null=True, blank=True)


    class Meta:
        verbose_name = "Organigrama"
        verbose_name_plural = "Organigramas"
        unique_together = ['estado']

#---------------------------------------------------------------------
# Vehiculos
#---------------------------------------------------------------------

class TipoVeh(models.Model):
    tipo_veh = models.CharField(max_length=100)

    def __str__(self):
        return self.tipo_veh

class TipoAsignacionVeh(models.Model):
    tipo = models.CharField(max_length=20)

    def __str__(self):
        return self.tipo
    
class SituacionVeh(models.Model):
    situacion = models.CharField(max_length=50)

    def __str__(self):
        return self.situacion

class FotosVeh(models.Model):
    frente = models.FileField(upload_to='fotosVeh', null=True, blank=True)
    lateral = models.FileField(upload_to='fotosVeh', null=True, blank=True)
    trasera = models.FileField(upload_to='fotosVeh', null=True, blank=True)

    def __str__(self):
        return str(self.id)

class VehiculosOR(models.Model):
    marca = models.CharField(max_length=200)
    modelo = models.CharField(max_length=200)
    anio = models.DateField(null=True, blank=True)
    placa = models.CharField(max_length=20)
    no_motor = models.CharField(max_length=20)
    tarjeta_asig = models.CharField(max_length=30, null=True, blank=True)
    fecha_disp_comb = models.DateField(null=True, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2) 
    tipoVeh = models.ForeignKey(TipoVeh, on_delete=models.CASCADE, null=True, blank=True)
    asignacion = models.ForeignKey(TipoAsignacionVeh, on_delete=models.CASCADE, db_index=True)
    fecha_asignacion = models.DateField(null=True, blank=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    fotografias = models.ForeignKey(FotosVeh, on_delete=models.CASCADE, null=True, blank=True)
    situacion = models.ForeignKey(SituacionVeh, on_delete=models.CASCADE, null=True, blank=True)
    balizado = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.placa})"

class PrestadoDe(models.Model):
    vehiculo = models.ForeignKey(VehiculosOR, on_delete=models.CASCADE, db_index=True)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_index=True)
    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    fecha_prestamo = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.vehiculo} - Prestado a {self.estado}"

class CatalogoMotivoBaja(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class MotivoBaja(models.Model):
    vehiculo = models.ForeignKey(VehiculosOR, on_delete=models.CASCADE, db_index=True)
    motivo = models.ForeignKey(CatalogoMotivoBaja, on_delete=models.PROTECT)
    comentario = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"Baja de {self.vehiculo} ({self.motivo.nombre})"

class Siniestros(models.Model):
    vehiculo = models.ForeignKey(VehiculosOR, on_delete=models.CASCADE, db_index=True)
    fecha = models.DateField(null=True, blank=True)
    folio = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"Siniestro de {self.vehiculo} - Folio {self.folio or 'S/F'}"

class Kilometraje(models.Model):
    TIPO_UNIDAD_CHOICES = (
        ('KM', 'kilometro'),
        ('MI', 'Milla'),
    )
    vehiculo = models.ForeignKey(VehiculosOR, on_delete=models.CASCADE, db_index=True)
    fecha = models.DateField(null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_UNIDAD_CHOICES)
    odometro = models.DecimalField(max_digits=10, decimal_places=2) 
    evidencia = models.FileField(upload_to='fotosVeh', null=True, blank=True)

    def __str__(self):
        return f"{self.vehiculo} - {self.odometro} {self.tipo}"

class Capufe(models.Model):
    vehiculo = models.ForeignKey(VehiculosOR, on_delete=models.CASCADE, db_index=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_termino = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Capufe {self.vehiculo} ({self.fecha_inicio} a {self.fecha_termino})"

class CombustibleExt(models.Model):
    vehiculo = models.ForeignKey(VehiculosOR, on_delete=models.CASCADE, db_index=True)
    fecha = models.DateField(null=True, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2) 

    def __str__(self):
        return f"Combustible Ext. {self.vehiculo} - ${self.monto}" 

