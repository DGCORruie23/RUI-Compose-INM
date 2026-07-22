"""
Registro en el admin de Django. Mientras no exista una pantalla propia de
captura con roles, esto permite que personal autorizado cargue vehículos,
fotos y catálogos directo desde /admin/ — incluye subida de imágenes
(Django genera el widget de archivo automáticamente para ImageField).
"""

from django.contrib import admin

from .models import (
    Asignacion,
    Capufe,
    CombustibleExterno,
    Estado,
    FotoVehiculo,
    Inmueble,
    Kilometraje,
    MotivoBajaCatalogo,
    PrestamoVehiculo,
    Siniestro,
    Situacion,
    Tarjeta,
    TipoVehiculo,
    Vehiculo,
    VehiculoBaja,
)


# --- Catálogos: administración simple, solo nombre --------------------

@admin.register(TipoVehiculo)
@admin.register(Asignacion)
@admin.register(Estado)
@admin.register(Situacion)
@admin.register(Inmueble)
class CatalogoSimpleAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(Tarjeta)
class TarjetaAdmin(admin.ModelAdmin):
    list_display = ("id", "numero", "banco", "activa")
    list_filter = ("activa", "banco")
    search_fields = ("numero", "banco")


@admin.register(MotivoBajaCatalogo)
class MotivoBajaCatalogoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


# --- Evidencia fotográfica: inline dentro del propio vehículo ----------

class FotoVehiculoInline(admin.StackedInline):
    model = FotoVehiculo
    extra = 0
    max_num = 1
    can_delete = False


# --- Vehículo: entidad principal ---------------------------------------

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ("placa", "marca", "modelo", "anio", "tipo_vehiculo", "situacion", "asignacion")
    list_filter = ("situacion", "tipo_vehiculo", "asignacion", "estado")
    search_fields = ("placa", "no_motor", "marca", "modelo")
    autocomplete_fields = ("tipo_vehiculo", "asignacion", "situacion", "estado", "inmueble", "tarjeta")
    inlines = [FotoVehiculoInline]


# --- Historial / tablas transaccionales --------------------------------

@admin.register(PrestamoVehiculo)
class PrestamoVehiculoAdmin(admin.ModelAdmin):
    list_display = ("vehiculo", "fecha_prestamo", "estado", "inmueble")
    list_filter = ("estado",)
    autocomplete_fields = ("vehiculo", "estado", "inmueble")


@admin.register(VehiculoBaja)
class VehiculoBajaAdmin(admin.ModelAdmin):
    list_display = ("vehiculo", "motivo", "creado_en")
    list_filter = ("motivo",)
    autocomplete_fields = ("vehiculo", "motivo")


@admin.register(Siniestro)
class SiniestroAdmin(admin.ModelAdmin):
    list_display = ("vehiculo", "fecha", "folio")
    search_fields = ("folio",)
    autocomplete_fields = ("vehiculo",)


@admin.register(Kilometraje)
class KilometrajeAdmin(admin.ModelAdmin):
    list_display = ("vehiculo", "fecha", "tipo", "odometro")
    list_filter = ("tipo",)
    autocomplete_fields = ("vehiculo",)
    # Django genera el widget de subida de archivo solo para 'evidencia' (ImageField)


@admin.register(Capufe)
class CapufeAdmin(admin.ModelAdmin):
    list_display = ("vehiculo", "fecha_inicio", "fecha_termino")
    autocomplete_fields = ("vehiculo",)


@admin.register(CombustibleExterno)
class CombustibleExternoAdmin(admin.ModelAdmin):
    list_display = ("vehiculo", "fecha", "monto", "tarjeta")
    autocomplete_fields = ("vehiculo", "tarjeta")
