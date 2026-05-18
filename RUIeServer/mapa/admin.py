from django.contrib import admin
from .models import (
    Estado, Nacionalidad, Repatriados, Recibidos, ExtRescatados, 
    Ingresos, Tramites, Retornados, Inadmitidos,
    PuntosInternacionEstacion, CatalogoOR, Encuentros,
    TipoPRH, PRHs, Titular, Estudio, GradoAcademico,
    TelefonoTitular, TrayectoriaLaboral, ExperienciaProfesional,
    CorreoTitular, TipoNombramiento, TipoProcendencia
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
