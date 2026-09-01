from django.contrib import admin
from .models import (
    Estado, Nacionalidad, Repatriados, Recibidos, RegistroMexExtPunto, ExtRescatados,
    Ingresos, Tramites, Retornados, Inadmitidos,
    PuntosInternacionEstacion, CatalogoOR, Encuentros,
    TipoPRH, PRHs, Titular, Estudio, GradoAcademico,
    TelefonoTitular, TrayectoriaLaboral, ExperienciaProfesional,
    CorreoTitular, TipoNombramiento, TipoProcendencia,
    Comodato, FiguraOcupacion, TipoInmueble, SituacionActual,
    TipoActividad, Inmueble, HistoricoComentarios, TipoOficina,
    ProgramaIPC, PersonalINM, OrganigramaF, EstatusPersonal, TipoPlaza, TipoDependencia,
    TipoVeh, TipoAsignacionVeh, SituacionVeh, FotosVeh, VehiculosOR,
    PrestadoDe, CatalogoMotivoBaja, MotivoBaja, Siniestros, Kilometraje,
    Capufe, CombustibleExt
)

@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Nacionalidad)
class NacionalidadAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Repatriados)
class RepatriadosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'nacionalidad', 'mex_rep', 'adultos', 'menores')
    list_filter = ('estado', 'nacionalidad', 'fecha')
    search_fields = ('estado__nombre', 'nacionalidad__nombre')

@admin.register(Recibidos)
class RecibidosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'nacionalidad', 'ext_rec', 'adultos', 'menores')
    list_filter = ('estado', 'nacionalidad', 'fecha')
    search_fields = ('estado__nombre', 'nacionalidad__nombre')

@admin.register(RegistroMexExtPunto)
class RegistroMexExtPuntoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'punto', 'categoria', 'nacionalidad', 'hombres', 'mujeres', 'ninos', 'ninas')
    list_filter = ('estado', 'punto', 'categoria', 'fecha')
    search_fields = ('punto', 'nacionalidad__nombre')

@admin.register(ExtRescatados)
class ExtRescatadosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'nacionalidad', 'rescatados', 'una_vez', 'reincidente')
    list_filter = ('estado', 'nacionalidad', 'fecha')
    search_fields = ('estado__nombre', 'nacionalidad__nombre')

@admin.register(Ingresos)
class IngresosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'nacionalidad', 'ingresos_total', 'terrestres')
    list_filter = ('estado', 'nacionalidad', 'fecha')
    search_fields = ('estado__nombre', 'nacionalidad__nombre')

@admin.register(Tramites)
class TramitesAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'nacionalidad', 'total_documentos', 'visitante_humanitario')
    list_filter = ('estado', 'nacionalidad', 'fecha')
    search_fields = ('estado__nombre', 'nacionalidad__nombre')

@admin.register(Retornados)
class RetornadosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'nacionalidad', 'retornados_total', 'deportado')
    list_filter = ('estado', 'nacionalidad', 'fecha')
    search_fields = ('estado__nombre', 'nacionalidad__nombre')

@admin.register(Inadmitidos)
class InadmitidosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'nacionalidad', 'inadmitidos_total')
    list_filter = ('estado', 'nacionalidad', 'fecha')
    search_fields = ('estado__nombre', 'nacionalidad__nombre')

@admin.register(PuntosInternacionEstacion)
class PuntosAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'estado', 'tipo', 'latitud', 'longitud')
    list_filter = ('estado', 'tipo')
    search_fields = ('nombre', 'estado__nombre')

@admin.register(CatalogoOR)
class CatalogoORAdmin(admin.ModelAdmin):
    list_display = ('titular', 'estado', 'correo')
    list_filter = ('estado',)
    search_fields = ('titular', 'estado__nombre')

@admin.register(Encuentros)
class EncuentrosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'agencia', 'estadoEU', 'estado', 'nacionalidad', 'encuentros_total')
    list_filter = ('fecha', 'estadoEU', 'estado', 'nacionalidad')
    search_fields = ('agencia', 'ciudadEU', 'estadoEU', 'estado__nombre', 'nacionalidad__nombre')

@admin.register(TipoPRH)
class TipoPRHAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(PRHs)
class PRHsAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'estado', 'modalidad', 'activo')
    list_filter = ('estado', 'modalidad', 'activo')
    search_fields = ('nombre', 'estado__nombre', 'modalidad__nombre')

class EstudioInline(admin.TabularInline):
    model = Estudio
    extra = 1

class TelefonoInline(admin.TabularInline):
    model = TelefonoTitular
    extra = 1

class CorreoInline(admin.TabularInline):
    model = CorreoTitular
    extra = 1

class TrayectoriaInline(admin.TabularInline):
    model = TrayectoriaLaboral
    extra = 1

class ExperienciaInline(admin.StackedInline):
    model = ExperienciaProfesional
    extra = 1

@admin.register(Titular)
class TitularAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido_paterno', 'apellido_materno', 'estado', 'nacionalidad')
    list_filter = ('estado', 'nacionalidad', 'sexo')
    search_fields = ('nombre', 'apellido_paterno', 'apellido_materno', 'curp')
    inlines = [TelefonoInline, CorreoInline, EstudioInline, TrayectoriaInline, ExperienciaInline]

@admin.register(Estudio)
class EstudioAdmin(admin.ModelAdmin):
    list_display = ('carrera', 'grado', 'titular', 'institucion')
    list_filter = ('grado',)
    search_fields = ('carrera', 'institucion', 'titular__nombre')

@admin.register(GradoAcademico)
class GradoAcademicoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(TipoNombramiento)
class TipoNombramientoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(TipoProcendencia)
class TipoProcendenciaAdmin(admin.ModelAdmin):
    list_display = ('institucion',)
    search_fields = ('institucion',)

@admin.register(Comodato)
class ComodatoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(FiguraOcupacion)
class FiguraOcupacionAdmin(admin.ModelAdmin):
    list_display = ('tipo',)
    search_fields = ('tipo',)

@admin.register(TipoInmueble)
class TipoInmuebleAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(SituacionActual)
class SituacionActualAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(TipoActividad)
class TipoActividadAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(TipoDependencia)
class TipoDependenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(TipoOficina)
class TipoOficinaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

class HistoricoComentariosInline(admin.TabularInline):
    model = HistoricoComentarios
    extra = 1
    readonly_fields = ('fecha_creacion',)

class ProgramaIPCInline(admin.StackedInline):
    model = ProgramaIPC
    extra = 1

@admin.register(Inmueble)
class InmuebleAdmin(admin.ModelAdmin):
    list_display = ('nombre_inmueble', 'municipio', 'estado', 'tipo_inmueble', 'get_tipos_actividad', 'situacion_actual')
    list_filter = ('estado', 'tipo_inmueble', 'tipo_actividad', 'situacion_actual', 'figura_ocupacion')
    search_fields = ('nombre_inmueble', 'municipio', 'colonia', 'calle', 'codigo_postal')
    inlines = [HistoricoComentariosInline, ProgramaIPCInline]

    def get_tipos_actividad(self, obj):
        return ", ".join([ta.nombre for ta in obj.tipo_actividad.all()])
    get_tipos_actividad.short_description = 'Tipos de Actividad'

@admin.register(HistoricoComentarios)
class HistoricoComentariosAdmin(admin.ModelAdmin):
    list_display = ('inmueble', 'comentario', 'fecha_creacion')
    list_filter = ('fecha_creacion', 'inmueble')
    search_fields = ('comentario', 'inmueble__nombre_inmueble')
    readonly_fields = ('fecha_creacion',)

@admin.register(ProgramaIPC)
class ProgramaIPCAdmin(admin.ModelAdmin):
    list_display = ('inmueble', 'inm_pipc', 'fecha_inm', 'comodante_pipc', 'fecha_comodante', 'plan_emergencia', 'fecha_inicio_plan')
    list_filter = ('inm_pipc', 'comodante_pipc', 'plan_emergencia')
    search_fields = ('inmueble__nombre_inmueble',)


@admin.register(PersonalINM)
class PersonalINMAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'num_empleado', 'estado', 'lugar_asignado', 'tipo_plaza', 'codigo_plaza', 'puesto_especifico', 'jefe_oficina', 'estatus')
    list_filter = ('estado', 'lugar_asignado', 'tipo_plaza', 'jefe_oficina', 'estatus', 'tipo_movimiento')
    search_fields = ('nombre', 'apellido', 'num_empleado', 'codigo_plaza', 'puesto_especifico')


@admin.register(OrganigramaF)
class OrganigramaFAdmin(admin.ModelAdmin):
    list_display = ('estado', 'archivo', 'vigencia')
    list_filter = ('estado', 'vigencia')
    search_fields = ('estado__nombre',)


@admin.register(TipoPlaza)
class TipoPlazaAdmin(admin.ModelAdmin):
    list_display = ('plazaT',)
    search_fields = ('plazaT',)


@admin.register(EstatusPersonal)
class EstatusPersonalAdmin(admin.ModelAdmin):
    list_display = ('estatus',)
    search_fields = ('estatus',)


# --- Vehículos ---

@admin.register(TipoVeh)
class TipoVehAdmin(admin.ModelAdmin):
    list_display = ('tipo_veh',)
    search_fields = ('tipo_veh',)

@admin.register(TipoAsignacionVeh)
class TipoAsignacionVehAdmin(admin.ModelAdmin):
    list_display = ('tipo',)
    search_fields = ('tipo',)

@admin.register(SituacionVeh)
class SituacionVehAdmin(admin.ModelAdmin):
    list_display = ('situacion',)
    search_fields = ('situacion',)

@admin.register(FotosVeh)
class FotosVehAdmin(admin.ModelAdmin):
    list_display = ('id', 'frente', 'lateral', 'trasera')

@admin.register(VehiculosOR)
class VehiculosORAdmin(admin.ModelAdmin):
    list_display = ('marca', 'modelo', 'placa', 'estado', 'inmueble', 'situacion', 'monto')
    list_filter = ('estado', 'tipoVeh', 'asignacion', 'situacion')
    search_fields = ('marca', 'modelo', 'placa', 'no_motor', 'tarjeta_asig')

@admin.register(PrestadoDe)
class PrestadoDeAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'estado', 'inmueble', 'fecha_prestamo')
    list_filter = ('estado', 'fecha_prestamo')
    search_fields = ('vehiculo__placa', 'vehiculo__marca', 'vehiculo__modelo')

@admin.register(CatalogoMotivoBaja)
class CatalogoMotivoBajaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(MotivoBaja)
class MotivoBajaAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'motivo', 'comentario')
    list_filter = ('motivo',)
    search_fields = ('vehiculo__placa', 'comentario')

@admin.register(Siniestros)
class SiniestrosAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'fecha', 'folio')
    list_filter = ('fecha',)
    search_fields = ('vehiculo__placa', 'folio')

@admin.register(Kilometraje)
class KilometrajeAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'fecha', 'odometro', 'tipo')
    list_filter = ('fecha', 'tipo')
    search_fields = ('vehiculo__placa',)

@admin.register(Capufe)
class CapufeAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'fecha_inicio', 'fecha_termino')
    list_filter = ('fecha_inicio', 'fecha_termino')
    search_fields = ('vehiculo__placa',)

@admin.register(CombustibleExt)
class CombustibleExtAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'fecha', 'monto')
    list_filter = ('fecha',)
    search_fields = ('vehiculo__placa',)



