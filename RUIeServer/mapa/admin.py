from django.contrib import admin
from .models import (
    Estado, Repatriados, Recibidos, ExtRescatados, 
    Ingresos, Tramites, Retornados, Inadmitidos
)

@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Repatriados)
class RepatriadosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'mex_rep', 'adultos', 'menores')
    list_filter = ('estado', 'fecha')
    search_fields = ('estado__nombre',)

@admin.register(Recibidos)
class RecibidosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'ext_rec', 'adultos', 'menores')
    list_filter = ('estado', 'fecha')
    search_fields = ('estado__nombre',)

@admin.register(ExtRescatados)
class ExtRescatadosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'rescatados', 'una_vez', 'reincidente')
    list_filter = ('estado', 'fecha')
    search_fields = ('estado__nombre',)

@admin.register(Ingresos)
class IngresosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'ingresos_total', 'terrestres')
    list_filter = ('estado', 'fecha')
    search_fields = ('estado__nombre',)

@admin.register(Tramites)
class TramitesAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'total_documentos', 'visitante_humanitario')
    list_filter = ('estado', 'fecha')
    search_fields = ('estado__nombre',)

@admin.register(Retornados)
class RetornadosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'retornados_total', 'deportado')
    list_filter = ('estado', 'fecha')
    search_fields = ('estado__nombre',)

@admin.register(Inadmitidos)
class InadmitidosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'estado', 'inadmitidos_total')
    list_filter = ('estado', 'fecha')
    search_fields = ('estado__nombre',)
