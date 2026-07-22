"""
Modelos Django mapeados al esquema de database/schema_postgres.sql

IMPORTANTE: managed = False en cada Meta.
Esto le dice a Django "esta tabla ya existe (o la crea el script SQL,
no una migración de Django), solo úsala para leer/escribir" — Django
nunca va a intentar crear, alterar o borrar estas tablas por su cuenta.
Si el día de mañana SÍ quieres que Django controle el esquema, basta con
quitar managed=False y correr makemigrations/migrate normalmente.

Todas las FK usan db_column explícito para que coincida exactamente con
los nombres de columna del script SQL (evita ambigüedad entre cómo
Django nombraría el campo por default vs. cómo se llama en la base).
"""

from django.db import models


# --- Catálogos ------------------------------------------------------

class TipoVehiculo(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        managed = False
        db_table = "tipo_vehiculo"
        verbose_name = "Tipo de vehículo"
        verbose_name_plural = "Tipos de vehículo"

    def __str__(self):
        return self.nombre


class Asignacion(models.Model):
    nombre = models.CharField(max_length=30, unique=True)

    class Meta:
        managed = False
        db_table = "asignacion"
        verbose_name_plural = "Asignaciones"

    def __str__(self):
        return self.nombre


class Estado(models.Model):
    """Catálogo geográfico (entidad federativa) — distinto de Situación."""
    nombre = models.CharField(max_length=60, unique=True)

    class Meta:
        managed = False
        db_table = "estado"
        verbose_name_plural = "Estados"

    def __str__(self):
        return self.nombre


class Situacion(models.Model):
    """Estatus operativo del vehículo: Activo, Mantenimiento, Posible baja."""
    nombre = models.CharField(max_length=30, unique=True)

    class Meta:
        managed = False
        db_table = "situacion"
        verbose_name_plural = "Situaciones"

    def __str__(self):
        return self.nombre


class Inmueble(models.Model):
    nombre = models.CharField(max_length=150, unique=True)

    class Meta:
        managed = False
        db_table = "inmueble"
        verbose_name_plural = "Inmuebles"

    def __str__(self):
        return self.nombre


class Tarjeta(models.Model):
    numero = models.CharField(max_length=30, unique=True)
    banco = models.CharField(max_length=80, blank=True, null=True)
    activa = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "tarjeta"
        verbose_name_plural = "Tarjetas"

    def __str__(self):
        return self.numero


class MotivoBajaCatalogo(models.Model):
    nombre = models.CharField(max_length=150, unique=True)

    class Meta:
        managed = False
        db_table = "motivo_baja_catalogo"
        verbose_name = "Motivo de baja (catálogo)"
        verbose_name_plural = "Motivos de baja (catálogo)"

    def __str__(self):
        return self.nombre


# --- Entidad principal ------------------------------------------------

class Vehiculo(models.Model):
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    anio = models.SmallIntegerField()
    placa = models.CharField(max_length=20, unique=True)
    no_motor = models.CharField(max_length=60, unique=True)

    tipo_vehiculo = models.ForeignKey(
        TipoVehiculo, on_delete=models.PROTECT, db_column="tipo_vehiculo_id", related_name="vehiculos"
    )
    asignacion = models.ForeignKey(
        Asignacion, on_delete=models.PROTECT, db_column="asignacion_id", related_name="vehiculos"
    )
    situacion = models.ForeignKey(
        Situacion, on_delete=models.PROTECT, db_column="situacion_id", related_name="vehiculos"
    )
    estado = models.ForeignKey(
        Estado, on_delete=models.SET_NULL, null=True, blank=True, db_column="estado_id", related_name="vehiculos"
    )
    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.SET_NULL, null=True, blank=True, db_column="inmueble_id", related_name="vehiculos"
    )
    tarjeta = models.ForeignKey(
        Tarjeta, on_delete=models.SET_NULL, null=True, blank=True, db_column="tarjeta_id", related_name="vehiculos"
    )

    creado_en = models.DateTimeField(auto_now_add=True, db_column="creado_en")
    actualizado_en = models.DateTimeField(auto_now=True, db_column="actualizado_en")

    class Meta:
        managed = False
        db_table = "vehiculo"
        verbose_name_plural = "Vehículos"

    def __str__(self):
        return f"{self.placa} · {self.marca} {self.modelo}"


# --- Evidencia fotográfica (imágenes) ----------------------------------

def _ruta_foto_vehiculo(instance, filename):
    """vehiculos/<placa>/<archivo> — organiza las fotos por vehículo dentro
    de MEDIA_ROOT. Django guarda esta ruta relativa en la columna de texto;
    el archivo en sí vive en disco (o en el storage que configures)."""
    return f"vehiculos/{instance.vehiculo.placa}/{filename}"


class FotoVehiculo(models.Model):
    # OneToOne: hoy es "un conjunto de fotos por vehículo". Si más adelante
    # se necesita historial (varias evidencias en el tiempo), cambiar a
    # ForeignKey + un campo "vista" (frente/lateral/trasera), un registro
    # por foto — mismo patrón que ya usa Kilometraje.
    vehiculo = models.OneToOneField(
        Vehiculo, on_delete=models.CASCADE, db_column="vehiculo_id", related_name="fotos"
    )
    frente = models.ImageField(upload_to=_ruta_foto_vehiculo, blank=True, null=True)
    lateral = models.ImageField(upload_to=_ruta_foto_vehiculo, blank=True, null=True)
    trasera = models.ImageField(upload_to=_ruta_foto_vehiculo, blank=True, null=True)
    actualizado_en = models.DateTimeField(auto_now=True, db_column="actualizado_en")

    class Meta:
        managed = False
        db_table = "foto_vehiculo"
        verbose_name = "Evidencia fotográfica"
        verbose_name_plural = "Evidencia fotográfica"

    def __str__(self):
        return f"Fotos de {self.vehiculo.placa}"


# --- Tablas transaccionales (historial) --------------------------------

class PrestamoVehiculo(models.Model):
    vehiculo = models.ForeignKey(
        Vehiculo, on_delete=models.CASCADE, db_column="vehiculo_id", related_name="prestamos"
    )
    estado = models.ForeignKey(
        Estado, on_delete=models.SET_NULL, null=True, blank=True, db_column="estado_id"
    )
    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.SET_NULL, null=True, blank=True, db_column="inmueble_id"
    )
    fecha_prestamo = models.DateField()

    class Meta:
        managed = False
        db_table = "prestamo_vehiculo"
        verbose_name_plural = "Préstamos de vehículo"


class VehiculoBaja(models.Model):
    """Antes 'MotivoBaja' en el diagrama — renombrada para no confundirse
    con el catálogo MotivoBajaCatalogo."""
    vehiculo = models.ForeignKey(
        Vehiculo, on_delete=models.CASCADE, db_column="vehiculo_id", related_name="bajas"
    )
    motivo = models.ForeignKey(
        MotivoBajaCatalogo, on_delete=models.PROTECT, db_column="motivo_id", related_name="bajas"
    )
    comentario = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True, db_column="creado_en")

    class Meta:
        managed = False
        db_table = "vehiculo_baja"
        verbose_name = "Baja de vehículo"
        verbose_name_plural = "Bajas de vehículo"


class Siniestro(models.Model):
    vehiculo = models.ForeignKey(
        Vehiculo, on_delete=models.CASCADE, db_column="vehiculo_id", related_name="siniestros"
    )
    fecha = models.DateField()
    folio = models.CharField(max_length=50, unique=True)

    class Meta:
        managed = False
        db_table = "siniestro"
        verbose_name_plural = "Siniestros"


def _ruta_evidencia_km(instance, filename):
    return f"kilometraje/{instance.vehiculo.placa}/{filename}"


class Kilometraje(models.Model):
    vehiculo = models.ForeignKey(
        Vehiculo, on_delete=models.CASCADE, db_column="vehiculo_id", related_name="lecturas_km"
    )
    fecha = models.DateField()
    tipo = models.CharField(max_length=30)  # ej. 'Inicial', 'Revisión', 'Carga de gasolina'
    odometro = models.PositiveIntegerField()
    evidencia = models.ImageField(upload_to=_ruta_evidencia_km, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "kilometraje"
        verbose_name_plural = "Lecturas de kilometraje"
        ordering = ["-fecha"]


class Capufe(models.Model):
    vehiculo = models.ForeignKey(
        Vehiculo, on_delete=models.CASCADE, db_column="vehiculo_id", related_name="capufe"
    )
    fecha_inicio = models.DateField()
    fecha_termino = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "capufe"
        verbose_name = "Registro Capufe"
        verbose_name_plural = "Registros Capufe"


class CombustibleExterno(models.Model):
    """Fuente única de verdad para dispersiones de combustible (ver
    corrección #9 del análisis del esquema: antes se duplicaba en
    Vehiculo.fecha_disp_comb / monto, lo cual perdía el historial)."""
    vehiculo = models.ForeignKey(
        Vehiculo, on_delete=models.CASCADE, db_column="vehiculo_id", related_name="combustible"
    )
    tarjeta = models.ForeignKey(
        Tarjeta, on_delete=models.SET_NULL, null=True, blank=True, db_column="tarjeta_id"
    )
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = "combustible_externo"
        verbose_name = "Combustible externo"
        verbose_name_plural = "Combustible externo"
        ordering = ["-fecha"]
