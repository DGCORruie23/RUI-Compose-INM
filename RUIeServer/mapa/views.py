from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Estado, Nacionalidad, Repatriados, Recibidos, ExtRescatados, Ingresos, Tramites, Retornados, Inadmitidos, PuntosInternacionEstacion, CatalogoOR, Encuentros, TipoPRH, PRHs
from django.apps import apps
import openpyxl
from datetime import datetime
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, HoverTool, TapTool, CustomJS, LinearColorMapper, FactorRange, ColumnDataSource, NumeralTickFormatter, RangeTool, DatetimeTickFormatter
from bokeh.layouts import column
from bokeh.embed import components
from bokeh.palettes import Greens256
import json
import random
import os
from django.conf import settings

from django.db import transaction, models
from django.db.models import Sum, Count, Max, Q
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from datetime import date, timedelta
import unicodedata

def normalizar_nombre(texto):
    if not texto: return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', str(texto))
        if unicodedata.category(c) != 'Mn'
    ).upper().strip()

# --- FUNCIONES DE AGREGACIÓN (EXTRACTADAS PARA REUTILIZACIÓN) ---

def get_totals_by_period(start, end):
    data_by_state = {}
    estados = Estado.objects.all()

    # Función auxiliar para convertir Decimal a int (necesario para JSON)
    def val_int(d, key):
        return int(d.get(key) or 0)

    datos_rep = {}
    datos_rec = {}
    datos_res = {}
    datos_ing = {}
    datos_tra = {}
    datos_ret = {}
    datos_ina = {}
    datos_t = {}

    for edo in estados:
        key = normalizar_nombre(edo.nombre)
        
        # Agregaciones (convertimos a dict para obtener los valores con .get)
        rep = dict(Repatriados.objects.filter(estado=edo, fecha__range=[start, end]).aggregate(
            total=Sum('mex_rep'), adultos=Sum('adultos'), menores=Sum('menores'),
            nna_solo=Sum('nna_solo'), nna_acom=Sum('nna_acom'),
            terrestres=Sum('terrestres'), vuelos=Sum('vuelos')
        ))
        rec = dict(Recibidos.objects.filter(estado=edo, fecha__range=[start, end]).aggregate(
            total=Sum('ext_rec'), adultos=Sum('adultos'), menores=Sum('menores')
        ))
        res = dict(ExtRescatados.objects.filter(estado=edo, fecha__range=[start, end]).aggregate(
            total=Sum('rescatados'), una_vez=Sum('una_vez'), reincidente=Sum('reincidente'),
            estacion=Sum('estacion'), dif=Sum('dif'), conduccion=Sum('conduccion')
        ))
        ing = dict(Ingresos.objects.filter(estado=edo, fecha__range=[start, end]).aggregate(
            total=Sum('ingresos_total'), aereos=Sum('aereos'), maritimos=Sum('maritimos'), terrestres=Sum('terrestres')
        ))
        tra = dict(Tramites.objects.filter(estado=edo, fecha__range=[start, end]).aggregate(
            total=Sum('total_documentos'),
            res_perm=Sum('residente_permanente'), res_temp=Sum('residente_temporal'),
            res_est=Sum('residente_temp_estudio'), vis_hum=Sum('visitante_humanitario'),
            vis_adop=Sum('visitante_adopcion'), vis_reg=Sum('visitante_regional'),
            vis_trab=Sum('visitante_trabajador')
        ))
        ret = dict(Retornados.objects.filter(estado=edo, fecha__range=[start, end]).aggregate(
            total=Sum('retornados_total'), deportado=Sum('deportado'), retornado=Sum('retornado')
        ))
        ina = dict(Inadmitidos.objects.filter(estado=edo, fecha__range=[start, end]).aggregate(
            total=Sum('inadmitidos_total')
        ))

        datos_rep[key] = val_int(rep, 'total')
        datos_rec[key] = val_int(rec, 'total')
        datos_res[key] = val_int(res, 'total')
        datos_ing[key] = val_int(ing, 'total')
        datos_tra[key] = val_int(tra, 'total')
        datos_ret[key] = val_int(ret, 'total')
        datos_ina[key] = val_int(ina, 'total')

        data_by_state[key] = {
            'todos': val_int(rep, 'total') + val_int(rec, 'total') + val_int(res, 'total') + val_int(ing, 'total') + val_int(tra, 'total') + val_int(ret, 'total') + val_int(ina, 'total'),
            'color_t': 32, 'color_rep': 32, 'color_rec': 32, 'color_res': 32, 'color_ing': 32, 'color_tra': 32, 'color_ret': 32, 'color_ina': 32,
            'repatriados': val_int(rep, 'total'),
            'rep_adultos': val_int(rep, 'adultos'),
            'rep_menores': val_int(rep, 'menores'),
            'rep_nna_solo': val_int(rep, 'nna_solo'),
            'rep_nna_acom': val_int(rep, 'nna_acom'),
            'rep_terrestres': val_int(rep, 'terrestres'),
            'rep_vuelos': val_int(rep, 'vuelos'),
            'recibidos': val_int(rec, 'total'),
            'rec_adultos': val_int(rec, 'adultos'),
            'rec_menores': val_int(rec, 'menores'),
            'rescatados': val_int(res, 'total'),
            'res_una_vez': val_int(res, 'una_vez'),
            'res_reincidente': val_int(res, 'reincidente'),
            'res_estacion': val_int(res, 'estacion'),
            'res_dif': val_int(res, 'dif'),
            'res_conduccion': val_int(res, 'conduccion'),
            'ingresos': val_int(ing, 'total'),
            'ing_aereos': val_int(ing, 'aereos'),
            'ing_maritimos': val_int(ing, 'maritimos'),
            'ing_terrestres': val_int(ing, 'terrestres'),
            'tramites': val_int(tra, 'total'),
            'tra_res_perm': val_int(tra, 'res_perm'),
            'tra_res_temp': val_int(tra, 'res_temp'),
            'tra_res_est': val_int(tra, 'res_est'),
            'tra_vis_hum': val_int(tra, 'vis_hum'),
            'tra_vis_adop': val_int(tra, 'vis_adop'),
            'tra_vis_reg': val_int(tra, 'vis_reg'),
            'tra_vis_trab': val_int(tra, 'vis_trab'),
            'retornados': val_int(ret, 'total'),
            'ret_deportado': val_int(ret, 'deportado'),
            'ret_retornado': val_int(ret, 'retornado'),
            'inadmitidos': val_int(ina, 'total'),
        }

    # Rankings para Mapa de Calor
    ordenados_rep = sorted(datos_rep.items(), key=lambda x: x[1], reverse=True)
    ordenados_rec = sorted(datos_rec.items(), key=lambda x: x[1], reverse=True)
    ordenados_res = sorted(datos_res.items(), key=lambda x: x[1], reverse=True)
    ordenados_ing = sorted(datos_ing.items(), key=lambda x: x[1], reverse=True)
    ordenados_tra = sorted(datos_tra.items(), key=lambda x: x[1], reverse=True)
    ordenados_ret = sorted(datos_ret.items(), key=lambda x: x[1], reverse=True)
    ordenados_ina = sorted(datos_ina.items(), key=lambda x: x[1], reverse=True)

    for rank, (k, value) in enumerate(ordenados_rep, start=1):
        data_by_state[k]['color_rep'] = 32 if value == 0 else rank
    for rank, (k, value) in enumerate(ordenados_rec, start=1):
        data_by_state[k]['color_rec'] = 32 if value == 0 else rank
    for rank, (k, value) in enumerate(ordenados_res, start=1):
        data_by_state[k]['color_res'] = 32 if value == 0 else rank
    for rank, (k, value) in enumerate(ordenados_ing, start=1):
        data_by_state[k]['color_ing'] = 32 if value == 0 else rank
    for rank, (k, value) in enumerate(ordenados_tra, start=1):
        data_by_state[k]['color_tra'] = 32 if value == 0 else rank
    for rank, (k, value) in enumerate(ordenados_ret, start=1):
        data_by_state[k]['color_ret'] = 32 if value == 0 else rank
    for rank, (k, value) in enumerate(ordenados_ina, start=1):
        data_by_state[k]['color_ina'] = 32 if value == 0 else rank

    for edo in estados:
        k = normalizar_nombre(edo.nombre)
        datos_t[k] = data_by_state[k].get('color_rep', 32) + data_by_state[k].get('color_rec', 32) + \
                     data_by_state[k].get('color_res', 32) + data_by_state[k].get('color_ing', 32) + \
                     data_by_state[k].get('color_tra', 32) + data_by_state[k].get('color_ret', 32) + \
                     data_by_state[k].get('color_ina', 32)
    
    ordenados_t = sorted(datos_t.items(), key=lambda x: x[1])
    for rank, (k, value) in enumerate(ordenados_t, start=1):
        if k in data_by_state: data_by_state[k]['color_t'] = rank

    return data_by_state

def calc_national(totals_dict):
    keys = [
        'todos', 'repatriados', 'rep_adultos', 'rep_menores', 'rep_nna_solo', 'rep_nna_acom', 'rep_terrestres', 'rep_vuelos',
        'recibidos', 'rec_adultos', 'rec_menores', 'rescatados', 'res_una_vez', 'res_reincidente', 'res_estacion', 
        'res_dif', 'res_conduccion', 'ingresos', 'ing_aereos', 'ing_maritimos', 'ing_terrestres',
        'tramites', 'tra_res_perm', 'tra_res_temp', 'tra_res_est', 'tra_vis_hum', 'tra_vis_adop', 'tra_vis_reg', 'tra_vis_trab',
        'retornados', 'ret_deportado', 'ret_retornado', 'inadmitidos'
    ]
    national = {k: 0 for k in keys}
    for state_data in totals_dict.values():
        for k in keys:
            if k in state_data: national[k] += state_data[k]
    return national

def get_global_update_date():
    """Calcula el mínimo de los máximos para determinar la fecha de integridad total."""
    from .models import Repatriados, Recibidos, ExtRescatados, Ingresos, Tramites, Retornados, Inadmitidos, Encuentros
    
    models_to_check = [
        Repatriados, Recibidos, ExtRescatados, Ingresos, 
        Tramites, Retornados, Inadmitidos, Encuentros
    ]
    
    max_dates = []
    for model in models_to_check:
        res = model.objects.aggregate(max_f=Max('fecha'))['max_f']
        if res:
            max_dates.append(res)
    
    if not max_dates:
        return None
    
    # Retornamos el Mínimo de los Máximos (Integridad Total)
    return min(max_dates)

def get_all_update_dates():
    """Retorna un diccionario con la última fecha de cada modelo."""
    from .models import Repatriados, Recibidos, ExtRescatados, Ingresos, Tramites, Retornados, Inadmitidos, Encuentros
    models_available = {
        'Repatriados': Repatriados,
        'Recibidos': Recibidos,
        'Rescatados': ExtRescatados,
        'Ingresos': Ingresos,
        'Tramites': Tramites,
        'Retornados': Retornados,
        'Inadmitidos': Inadmitidos,
        'Encuentros': Encuentros,
    }
    
    results = []
    for name, model in models_available.items():
        max_f = model.objects.aggregate(max_f=Max('fecha'))['max_f']
        results.append({
            'name': name,
            'date': max_f
        })
    return results

# --- VIEW PRINCIPAL ---

def mapa_informacion(request):
    if not request.user.is_superuser:
        return render(request, 'base/error404.html')

    fecha_act = get_global_update_date() or date.today()

    CS_START = date(2024, 10, 1)
    DT_START = date(2025, 1, 20)

    totals_cs = get_totals_by_period(CS_START, fecha_act)
    totals_dt = get_totals_by_period(DT_START, fecha_act)
    
    # Etiqueta centralizada para la escala global
    LABEL_NACIONAL = "Total Nacional"

    # Diccionario maestro de etiquetas de métricas
    METRIC_LABELS = {
        'todos': 'Todos',
        'repatriados': 'Mexicanos Recibidos',
        'recibidos': 'Extranjeros Recibidos',
        'rescatados': 'Rescates',
        'ingresos': 'Internaciones',
        'tramites': 'Trámites',
        'retornados': 'Retornados',
        'inadmitidos': 'Inadmitidos',
        'recibidos_total': 'Recibidos'
    }

    # --- Recopilación de Infraestructura y Titulares ---
    infra_raw = PuntosInternacionEstacion.objects.values('estado__nombre', 'tipo').annotate(total=Count('id'))
    titulares_raw = CatalogoOR.objects.all().select_related('estado')
    
    infra_data = {}
    # Estructura base para todos los estados
    for edo in Estado.objects.all():
        infra_data[normalizar_nombre(edo.nombre)] = {
            'AEREO': 0, 'MARITIMO': 0, 'TERRESTRE': 0, 'ESTACION': 0,
            'PRH': 0,
            'titular': 'Sin titular asignado'
        }
    
    # Población con datos reales
    for item in infra_raw:
        edo_name = normalizar_nombre(item['estado__nombre'])
        if edo_name in infra_data:
            infra_data[edo_name][item['tipo']] = item['total']
            
    for t in titulares_raw:
        edo_name = normalizar_nombre(t.estado.nombre)
        if edo_name in infra_data:
            infra_data[edo_name]['titular'] = t.titular

    # PRHs por estado
    prh_raw = PRHs.objects.values('estado__nombre').annotate(total=Count('id'))
    for item in prh_raw:
        edo_name = normalizar_nombre(item['estado__nombre'])
        if edo_name in infra_data:
            infra_data[edo_name]['PRH'] = item['total']

    # Totales Nacionales
    infra_data[LABEL_NACIONAL] = {
        'AEREO': PuntosInternacionEstacion.objects.filter(tipo='AEREO').count(),
        'MARITIMO': PuntosInternacionEstacion.objects.filter(tipo='MARITIMO').count(),
        'TERRESTRE': PuntosInternacionEstacion.objects.filter(tipo='TERRESTRE').count(),
        'ESTACION': PuntosInternacionEstacion.objects.filter(tipo='ESTACION').count(),
        'PRH': PRHs.objects.count(),
        'titular': 'Datos Nacionales'
    }


    # Ruta al archivo geojson descargado
    geojson_path = os.path.join(settings.BASE_DIR, 'mapa', 'static', 'mapa', 'data', 'mexico.geojson')
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geo_data = json.load(f)
          # Inyectar datos reales en cada estado
    for feature in geo_data['features']:
        name_normalized = normalizar_nombre(feature['properties']['name'])
        
        # Obtener datos de los diccionarios (usar default con ceros para todos los campos nuevos)
        default_vals = {
            'todos': 0, 'color_t': 32, 'color_rep': 32, 'color_rec': 32, 'color_res': 32, 'color_ing': 32, 'color_tra': 32, 'color_ret': 32, 'color_ina': 32,
            'repatriados': 0, 'rep_adultos': 0, 'rep_menores': 0, 'rep_nna_solo': 0, 'rep_nna_acom': 0, 'rep_terrestres': 0, 'rep_vuelos': 0,
            'recibidos': 0, 'rec_adultos': 0, 'rec_menores': 0,
            'rescatados': 0, 'res_una_vez': 0, 'res_reincidente': 0, 'res_estacion': 0, 'res_dif': 0, 'res_conduccion': 0,
            'ingresos': 0, 'ing_aereos': 0, 'ing_maritimos': 0, 'ing_terrestres': 0,
            'tramites': 0, 'tra_res_perm': 0, 'tra_res_temp': 0, 'tra_res_est': 0, 'tra_vis_hum': 0, 'tra_vis_adop': 0, 'tra_vis_reg': 0, 'tra_vis_trab': 0,
            'retornados': 0, 'ret_deportado': 0, 'ret_retornado': 0, 'inadmitidos': 0,
        }
        
        cs = totals_cs.get(name_normalized, default_vals)
        dt = totals_dt.get(name_normalized, default_vals)

        # Inyectar en GeoJSON (usamos prefijos cs_, dt_ y pe_)
        for k in default_vals:
            feature['properties'][f'cs_{k}'] = cs[k]
            feature['properties'][f'dt_{k}'] = dt[k]
            feature['properties'][f'pe_{k}'] = cs[k] # Inicializar PE con valores de CS
        
        # Cadenas formateadas para el Tooltip Dinámico
        for k in ['todos', 'repatriados', 'recibidos', 'rescatados', 'ingresos', 'tramites', 'retornados', 'inadmitidos']:
            feature['properties'][f'cs_str_{k}'] = f"{cs[k]:,}"
            feature['properties'][f'dt_str_{k}'] = f"{dt[k]:,}"
            feature['properties'][f'pe_str_{k}'] = f"{cs[k]:,}"
        
    geo_source = GeoJSONDataSource(geojson=json.dumps(geo_data))
    
    # Crear figura de Bokeh restaurando Auto-Range Dinámico para proporciones perfectas
    p = figure(
        title="",
        sizing_mode="scale_both",
        toolbar_location=None,
        tools="tap,pan,wheel_zoom,reset",
        match_aspect=True,
    )
    p.xaxis.visible = False
    p.yaxis.visible = False
    p.grid.grid_line_color = None
    p.outline_line_color = None
    p.min_border = 0
    
    # Configurar el mapa de calor inicial (Todos)
    custom_palette = list(Greens256[:205]) # Cortamos la paleta al 80% aprox
    color_mapper = LinearColorMapper(palette=custom_palette, low=1, high=32)

    # Dibujar los estados
    states = p.patches(
        'xs', 'ys', 
        source=geo_source,
        fill_color={'field': 'cs_todos', 'transform': color_mapper},
        line_color="#ffffff",
        line_width=1,
        fill_alpha=1.0,
        hover_fill_color='#285C4D',
        hover_line_color="#ffffff",
        hover_line_width=2,
        selection_fill_color='#285C4D',
        selection_line_color="#ffffff",
        selection_line_width=2,
        nonselection_fill_alpha=0.2,
        nonselection_line_alpha=0.2
    )

    # --- Capa de Infraestructura (Iconos SVG) ---
    infra_points_objs = PuntosInternacionEstacion.objects.all()
    infra_pts_data = {
        'x': [pt.longitud for pt in infra_points_objs],
        'y': [pt.latitud for pt in infra_points_objs],
        'nombre': [pt.nombre for pt in infra_points_objs],
        'estado': [normalizar_nombre(pt.estado.nombre) for pt in infra_points_objs],
        'tipo': [pt.tipo for pt in infra_points_objs],
        'url': []
    }
    
    for pt in infra_points_objs:
        icon_file = 'terrestre.svg' # Default
        if pt.tipo == 'AEREO': icon_file = 'aereo.svg'
        elif pt.tipo == 'MARITIMO': icon_file = 'maritimo.svg'
        elif pt.tipo == 'ESTACION': icon_file = 'estacion.svg'
        
        # Construir la URL del icono
        icon_url = f"{settings.STATIC_URL}mapa/icons/{icon_file}"
        infra_pts_data['url'].append(icon_url)

    infra_source = ColumnDataSource(infra_pts_data)
    infra_layer = p.image_url(url='url', x='x', y='y', w=0.25, h=0.25, source=infra_source, 
                              anchor="center", name="infra_layer")
    infra_layer.nonselection_glyph = None  # Evitar 404 al intentar renderizar estado "no seleccionado"
    
    # Hover específico para puntos de infraestructura
    infra_hover = HoverTool(
        renderers=[infra_layer],
        name="infra_hover",
        tooltips="""
            <div style="padding: 8px; border-radius: 5px; font-family: Arial, sans-serif;">
                <div style="font-size: 13px; font-weight: bold; color: #333;">@nombre</div>
                <div style="font-size: 11px; color: #666; margin-top: 2px;">Tipo: @tipo</div>
            </div>
        """
    )
    p.add_tools(infra_hover)

    # --- Capa de Puntos de Rescate Humano (PRH) ---
    prh_points = PRHs.objects.all().select_related('modalidad')
    prh_pts_data = {
        'x': [pt.longitud for pt in prh_points],
        'y': [pt.latitud for pt in prh_points],
        'nombre': [pt.nombre for pt in prh_points],
        'estado': [normalizar_nombre(pt.estado.nombre) for pt in prh_points],
        'modalidad': [pt.modalidad.nombre for pt in prh_points],
        'status': ['Activo' if pt.activo else 'Inactivo' for pt in prh_points],
        'url': []
    }
    for pt in prh_points:
        icon = 'agente_activo.svg' if pt.activo else 'agente_inactivo.svg'
        prh_pts_data['url'].append(f"{settings.STATIC_URL}mapa/icons/{icon}")

    prh_source = ColumnDataSource(prh_pts_data)
    prh_layer = p.image_url(url='url', x='x', y='y', w=0.25, h=0.25, source=prh_source, 
                              anchor="center", name="prh_layer")
    prh_layer.nonselection_glyph = None  # Evitar 404 al intentar renderizar estado "no seleccionado"
    
    # Hover específico para PRHs
    prh_hover = HoverTool(
        renderers=[prh_layer],
        name="prh_hover",
        tooltips="""
            <div style="padding: 8px; border-radius: 5px; font-family: Arial, sans-serif;">
                <div style="font-size: 13px; font-weight: bold; color: #7E1D36;">@nombre</div>
                <div style="font-size: 11px; color: #666; margin-top: 2px;"><b>Modalidad:</b> @modalidad</div>
                <div style="font-size: 11px; color: #666;"><b>Estado:</b> @status</div>
            </div>
        """
    )
    p.add_tools(prh_hover)
    
    # Actualizar HoverTool inicial configurado a 'Todos' (muestra todas las categorías dinámicamente)
    hover_items = []
    keys_to_show = ['repatriados', 'recibidos', 'rescatados', 'ingresos', 'tramites', 'retornados', 'inadmitidos']
    
    for k in keys_to_show:
        label = METRIC_LABELS.get(k, k.capitalize())
        hover_items.append(f"""
            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                <span style="font-size: 12px; color: #333;">{label}</span>
                <span style="font-size: 12px; font-weight: 500; color: #333;">@cs_str_{k}</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 3px;"></div>
        """)

    hover_html = f"""
        <div style="padding: 8px; min-width: 170px; font-family: Arial, sans-serif;">
            <div style="font-size: 16px; font-weight: 500; margin-bottom: 3px; color: #333;">@name</div>
            <div style="border-bottom: 1px solid #ddd; margin-bottom: 5px;"></div>
            {"".join(hover_items)}
        </div>
    """
    
    hover = HoverTool(
        renderers=[states],
        name="states_hover",
        tooltips=hover_html
    )
    p.add_tools(hover)
    
    national_data = {
        'name': LABEL_NACIONAL,
        'cs': calc_national(totals_cs),
        'dt': calc_national(totals_dt),
        'pe': calc_national(totals_cs) # Inicializar PE con valores de CS
    }

    # Añadir CustomJS para el evento de click (Tap)
    tap_js = CustomJS(args=dict(source=geo_source, national=national_data), code="""
        const indices = source.selected.indices;
        const keys = [
            'todos',
            'repatriados', 'rep_adultos', 'rep_menores', 'rep_nna_solo', 'rep_nna_acom', 'rep_terrestres', 'rep_vuelos',
            'recibidos', 'rec_adultos', 'rec_menores',
            'rescatados', 'res_una_vez', 'res_reincidente', 'res_estacion', 'res_dif', 'res_conduccion',
            'ingresos', 'ing_aereos', 'ing_maritimos', 'ing_terrestres',
            'tramites', 'tra_res_perm', 'tra_res_temp', 'tra_res_est', 'tra_vis_hum', 'tra_vis_adop', 'tra_vis_reg', 'tra_vis_trab',
            'retornados', 'ret_deportado', 'ret_retornado', 'inadmitidos'
        ];

        if (indices.length > 0) {
            const index = indices[0];
            const data = source.data;
            
            const newStateData = {
                name: data['name'][index],
                cs: {},
                dt: {},
                pe: {}
            };

            keys.forEach(k => {
                newStateData.cs[k] = data[`cs_${k}`][index];
                newStateData.dt[k] = data[`dt_${k}`][index];
                newStateData.pe[k] = data[`pe_${k}`][index];
            });

            window.selectedStateData = newStateData;
            
            // Disparar animación de zoom si la función existe
            if (window.animateToSelectedState) {
                window.animateToSelectedState(index);
            }
        } else {
            window.selectedStateData = national;
            
            // Disparar regreso a vista nacional
            if (window.animateToNationalView) {
                window.animateToNationalView();
            }
        }
        
        if (window.updateInformationPanel) {
            window.updateInformationPanel();
        }
    """)
    p.select(TapTool).callback = tap_js

    # Lógica de Pulsación Larga (Long Press) corregida para Bokeh
    long_press_callback = CustomJS(args=dict(source=geo_source, renderer=states), code="""
        const timer_key = 'bokeh_hold_timer';
        
        if (cb_obj.event_name === 'press') {
            // El evento 'press' de Bokeh ya implica una pulsación mantenida.
            // Para llegar a los 2s aprox, iniciamos un timer adicional.
            const sx = cb_obj.sx;
            const sy = cb_obj.sy;
            
            window[timer_key] = setTimeout(() => {
                const plot_view = Bokeh.index[Object.keys(Bokeh.index)[0]];
                const glyph_view = plot_view.renderer_views[renderer.id];
                const result = glyph_view.hit_test({ type: 'point', sx: sx, sy: sy });
                
                if (result && result.indices.length > 0) {
                    const idx = result.indices[0];
                    const data = {};
                    for (let key in source.data) {
                        data[key] = source.data[key][idx];
                    }
                    if (window.showLongPressMenu) {
                        const canvas = plot_view.canvas_view.canvas_el;
                        const rect = canvas.getBoundingClientRect();
                        const posX = rect.left + sx;
                        const posY = rect.top + sy;
                        window.showLongPressMenu(data, posX, posY);
                    }
                }
            }, 1500); // 1.5s + margen de Bokeh ~ 2s
        } else if (cb_obj.event_name === 'panstart' || cb_obj.event_name === 'tap') {
            // Cancelar si el usuario mueve el mapa o hace un clic rápido
            if (window[timer_key]) {
                clearTimeout(window[timer_key]);
                delete window[timer_key];
            }
        }
    """)
    p.js_on_event('press', long_press_callback)
    p.js_on_event('panstart', long_press_callback)
    p.js_on_event('tap', long_press_callback)

    # --- ESCALADO DINÁMICO DE ICONOS SEGÚN EL ZOOM ---
    scale_icons_js = CustomJS(args=dict(
        x_range=p.x_range,
        infra_glyph=infra_layer.glyph,
        prh_glyph=prh_layer.glyph
    ), code="""
        const range_width = Math.abs(x_range.end - x_range.start);
        
        // --- PARÁMETROS DE ESCALA ---
        // Escala Inicial (Vista Nacional): el icono ocupará ~1.2 grados de ancho
        // Escala Final (Zoom Máximo): el icono se reducirá hasta ~0.01 grados
        const factor = 0.0332; 
        const min_size = 0.001;  // Límite inferior (Zoom máximo)
        const max_size = 0.35;   // Límite superior (Vista Nacional)
        
        let new_size = range_width * factor; 
        
        if (new_size < min_size) new_size = min_size;
        if (new_size > max_size) new_size = max_size;
        
        infra_glyph.w = new_size;
        infra_glyph.h = new_size;
        prh_glyph.w = new_size;
        prh_glyph.h = new_size;
    """)
    p.x_range.js_on_change('start', scale_icons_js)

    script, div = components(p)
    
    context = {
        'map_script': script,
        'map_div': div,
        'national_data_json': json.dumps(national_data),
        'infra_data_json': json.dumps(infra_data),
        'label_nacional': LABEL_NACIONAL,
        'metric_labels': METRIC_LABELS,
        'metric_labels_json': json.dumps(METRIC_LABELS),
        'fecha_actualizacion': fecha_act,
    }
    
    return render(request, 'mapa/informacion.html', context)

def carga_datos(request):
    # Restricción de acceso: Solo superusuarios
    if not request.user.is_superuser:
        return render(request, 'base/error404.html')

    models_available = {
        'Repatriados': Repatriados,
        'Recibidos': Recibidos,
        'Extranjeros Rescatados': ExtRescatados,
        'Ingresos': Ingresos,
        'Tramites': Tramites,
        'Retornados': Retornados,
        'Inadmitidos': Inadmitidos,
        'Encuentros': Encuentros,
    }

    if request.method == 'POST':
        model_name = request.POST.get('model_name')
        excel_file = request.FILES.get('excel_file')

        if not model_name or not excel_file:
            messages.error(request, "Por favor seleccione un modelo y un archivo.")
            return redirect('carga_datos')

        if model_name not in models_available:
            messages.error(request, "Modelo no válido.")
            return redirect('carga_datos')

        try:
            wb = openpyxl.load_workbook(excel_file)
            sheet = wb.active
            model_class = models_available[model_name]
            
            # Obtener campos del modelo (específicos para ignorar id y estado FK inicialmente)
            # El orden del Excel debe ser: fecha, estado (nombre), y luego los campos específicos
            fields = [field.name for field in model_class._meta.fields if field.name not in ['id']]
            
            # Pre-cargar catálogos en memoria para evitar miles de consultas
            estados_dict = {normalizar_nombre(e.nombre): e for e in Estado.objects.all()}
            nacionalidades_dict = {normalizar_nombre(n.nombre): n for n in Nacionalidad.objects.all()}
            
            rows_created = 0
            rows_updated = 0
            errors = []
            
            with transaction.atomic():
                for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                    if not any(row): continue
                    
                    fecha_val = row[0]
                    if model_name == 'Encuentros':
                        # Formato: Fecha(0), Agencia(1), CiudadEU(2), EstadoEU(3), EstadoMex(4), Nacionalidad(5), Total(6)
                        agencia_raw = row[1]
                        ciudad_eu_raw = row[2]
                        estado_eu_raw = row[3]
                        estado_nombre = row[4]
                        nacionalidad_nombre = row[5]
                        
                        agencia_norm = normalizar_nombre(agencia_raw)
                        ciudad_eu_norm = normalizar_nombre(ciudad_eu_raw)
                        estado_eu_norm = normalizar_nombre(estado_eu_raw)
                        
                        nacionalidad_norm = normalizar_nombre(nacionalidad_nombre)
                        nac_obj = nacionalidades_dict.get(nacionalidad_norm)
                        
                        if not nac_obj:
                            errors.append(f"Fila {row_idx}: Nacionalidad '{nacionalidad_nombre}' no encontrada.")
                            continue
                        
                        estado_norm = normalizar_nombre(estado_nombre)
                        estado_obj = estados_dict.get(estado_norm)
                        if not estado_obj:
                            errors.append(f"Fila {row_idx}: Estado '{estado_nombre}' no encontrado.")
                            continue

                        obj, created = Encuentros.objects.update_or_create(
                            fecha=fecha_val,
                            agencia=agencia_norm,
                            ciudadEU=ciudad_eu_norm,
                            estadoEU=estado_eu_norm,
                            estado=estado_obj,
                            nacionalidad=nac_obj,
                            defaults={'encuentros_total': row[6] if len(row) > 6 else 0}
                        )
                    else:
                        estado_nombre = row[1]
                        nacionalidad_nombre = row[2] # Columna C
                        
                        # Normalizar nacionalidad
                        nacionalidad_norm = normalizar_nombre(nacionalidad_nombre)
                        nac_obj = nacionalidades_dict.get(nacionalidad_norm)
                        
                        if not nac_obj:
                            errors.append(f"Fila {row_idx}: La nacionalidad '{nacionalidad_nombre}' no existe en el catálogo.")
                            continue

                        # Convertir fecha si es necesario
                        if isinstance(fecha_val, str):
                            try:
                                fecha_val = datetime.strptime(fecha_val, '%Y-%m-%d').date()
                            except:
                                errors.append(f"Fila {row_idx}: Formato de fecha inválido (esperado YYYY-MM-DD).")
                                continue
                        
                        # Normalizar el nombre del estado
                        estado_norm_busqueda = normalizar_nombre(estado_nombre)
                        estado_obj = estados_dict.get(estado_norm_busqueda)
                        
                        if not estado_obj:
                            errors.append(f"Fila {row_idx}: Estado '{estado_nombre}' no encontrado.")
                            continue

                        # Construir diccionario de datos
                        data = {}
                        fields_to_populate = [f.name for f in model_class._meta.fields if f.name not in ['id', 'fecha', 'estado', 'nacionalidad']]
                        
                        for i, field_name in enumerate(fields_to_populate):
                            excel_idx = i + 3
                            if excel_idx < len(row):
                                val = row[excel_idx]
                                data[field_name] = val if val is not None else 0

                        obj, created = model_class.objects.update_or_create(
                            fecha=fecha_val,
                            estado=estado_obj,
                            nacionalidad=nac_obj,
                            defaults=data
                        )
                    
                    if created:
                        rows_created += 1
                    else:
                        rows_updated += 1

            if errors:
                for error in errors:
                    messages.error(request, error)
            
            if rows_created > 0 or rows_updated > 0:
                messages.success(request, f"Carga completada. Creados: {rows_created}, Actualizados: {rows_updated}")
            
        except Exception as e:
            messages.error(request, f"Error al procesar el archivo: {str(e)}")
            
        return redirect('carga_datos')

    update_dates = get_all_update_dates()
    return render(request, 'mapa/carga_datos.html', {
        'models': models_available.keys(),
        'update_dates': update_dates
    })

from django.http import JsonResponse

from django.http import JsonResponse

def api_periodo_custom(request):
    """API para obtener datos en un rango de fechas personalizado."""
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Acceso denegado'}, status=403)

    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()

        # Restricción: No anterior al 1 de Octubre de 2024
        MIN_DATE = date(2024, 10, 1)
        if start_date < MIN_DATE:
            start_date = MIN_DATE

        # Obtener datos
        totals_custom = get_totals_by_period(start_date, end_date)
        national_custom = calc_national(totals_custom)

        return JsonResponse({
            'status': 'success',
            'data': totals_custom,
            'national': national_custom
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def api_nacionalidad_ranking(request):
    """API para obtener el ranking de nacionalidades por estado y métrica."""
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Acceso denegado'}, status=403)

    estado_norm = request.GET.get('estado')
    metric = request.GET.get('metric')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    if not all([estado_norm, metric, start_str, end_str]):
        return JsonResponse({'status': 'error', 'message': 'Faltan parámetros'}, status=400)

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()

        # Mapeo de métricas a modelos y campos de total
        metric_map = {
            'repatriados': (Repatriados, 'mex_rep'),
            'recibidos': (Recibidos, 'ext_rec'),
            'rescatados': (ExtRescatados, 'rescatados'),
            'ingresos': (Ingresos, 'ingresos_total'),
            'tramites': (Tramites, 'total_documentos'),
            'retornados': (Retornados, 'retornados_total'),
            'inadmitidos': (Inadmitidos, 'inadmitidos_total'),
        }

        if metric not in metric_map:
            return JsonResponse({'status': 'error', 'message': 'Métrica no válida'}, status=400)

        model_class, total_field = metric_map[metric]
        
        # Buscar el estado por nombre normalizado
        estados = Estado.objects.all()
        target_estado = None
        for edo in estados:
            if normalizar_nombre(edo.nombre) == estado_norm:
                target_estado = edo
                break
        
        if not target_estado:
            return JsonResponse({'status': 'error', 'message': 'Estado no encontrado'}, status=404)

        # Agregación por Nacionalidad
        ranking = model_class.objects.filter(
            estado=target_estado,
            fecha__range=[start_date, end_date]
        ).values('nacionalidad__nombre').annotate(
            total=Sum(total_field)
        ).order_by('-total')[:12] # Top 12 nacionalidades

        data = []
        for item in ranking:
            nombre_nac = item['nacionalidad__nombre']
            if not nombre_nac: continue # Saltar si no hay nacionalidad

            data.append({
                'name': nombre_nac,
                'value': int(item['total'] or 0)
            })

        return JsonResponse({
            'status': 'success',
            'data': data,
            'state_name': target_estado.nombre
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def api_reporte_nacionalidades(request):
    """API para obtener el ranking de nacionalidades por rubro en un periodo."""
    rubro = request.GET.get('rubro', 'Encuentros')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    if not all([start_str, end_str]):
        return JsonResponse({'status': 'error', 'message': 'Faltan fechas'}, status=400)

    try:
        # Convertir timestamps de JS (ms) o strings ISO a date
        if start_str.isdigit():
            start_date = datetime.fromtimestamp(int(start_str)/1000.0).date()
            end_date = datetime.fromtimestamp(int(end_str)/1000.0).date()
        else:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()

        data = []
        if rubro == 'Encuentros':
            ranking = Encuentros.objects.filter(
                fecha__range=[start_date, end_date]
            ).values('nacionalidad__nombre').annotate(
                total=Sum('encuentros_total')
            ).order_by('-total')[:10]
        elif rubro == 'Rescatados':
            ranking = ExtRescatados.objects.filter(
                fecha__range=[start_date, end_date]
            ).values('nacionalidad__nombre').annotate(
                total=Sum('rescatados')
            ).order_by('-total')[:10]
        else: # Recibidos
            # Combinar total de Repatriados (México) con el ranking de Recibidos
            res_rec = Recibidos.objects.filter(
                fecha__range=[start_date, end_date]
            ).values('nacionalidad__nombre').annotate(
                total=Sum('ext_rec')
            ).order_by('-total')[:10]
            
            # Obtener total de mexicanos
            mex_total = Repatriados.objects.filter(
                fecha__range=[start_date, end_date]
            ).aggregate(total=Sum('mex_rep'))['total'] or 0
            
            data.append({'name': 'MÉXICO', 'value': int(mex_total)})
            for item in res_rec:
                data.append({'name': item['nacionalidad__nombre'], 'value': int(item['total'] or 0)})
            
            # Ordenar de nuevo por si algún país superó a México (poco probable pero posible)
            data = sorted(data, key=lambda x: x['value'], reverse=True)[:10]
            return JsonResponse({'status': 'success', 'data': data})

        for item in ranking:
            data.append({
                'name': item['nacionalidad__nombre'] or 'DESCONOCIDA',
                'value': int(item['total'] or 0)
            })

        return JsonResponse({'status': 'success', 'data': data})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def carga_datos_batch(request):
    # Restricción de acceso: Solo superusuarios
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Acceso denegado'}, status=403)

    if request.method == 'POST':
        try:
            import json
            payload = json.loads(request.body)
            model_name = payload.get('model_name')
            rows = payload.get('data', [])

            models_available = {
                'Repatriados': Repatriados,
                'Recibidos': Recibidos,
                'Extranjeros Rescatados': ExtRescatados,
                'Ingresos': Ingresos,
                'Tramites': Tramites,
                'Retornados': Retornados,
                'Inadmitidos': Inadmitidos,
                'Encuentros': Encuentros,
            }

            if model_name not in models_available:
                return JsonResponse({'status': 'error', 'message': 'Modelo no válido'}, status=400)

            model_class = models_available[model_name]
            
            # Pre-cargar catálogos en memoria
            estados_dict = {normalizar_nombre(e.nombre): e for e in Estado.objects.all()}
            nacionalidades_dict = {normalizar_nombre(n.nombre): n for n in Nacionalidad.objects.all()}
            
            rows_created = 0
            rows_updated = 0
            errors = []
            
            # Campos del modelo a poblar dinámicamente
            fields_to_populate = [f.name for f in model_class._meta.fields if f.name not in ['id', 'fecha', 'estado', 'nacionalidad']]

            with transaction.atomic():
                for row_idx, row in enumerate(rows):
                    if not any(row): continue
                    
                    fecha_val = row[0]
                    if model_name == 'Encuentros':
                        # Formato: Fecha(0), Agencia(1), CiudadEU(2), EstadoEU(3), EstadoMex(4), Nacionalidad(5), Total(6)
                        agencia_raw = row[1]
                        ciudad_eu_raw = row[2]
                        estado_eu_raw = row[3]
                        estado_nombre = row[4]
                        nacionalidad_nombre = row[5]
                        
                        agencia_norm = normalizar_nombre(agencia_raw)
                        ciudad_eu_norm = normalizar_nombre(ciudad_eu_raw)
                        estado_eu_norm = normalizar_nombre(estado_eu_raw)
                        
                        nacionalidad_norm = normalizar_nombre(nacionalidad_nombre)
                        nac_obj = nacionalidades_dict.get(nacionalidad_norm)
                        
                        if not nac_obj:
                            errors.append(f"Reg {row_idx}: Nacionalidad '{nacionalidad_nombre}' no existe.")
                            continue
                        
                        estado_norm = normalizar_nombre(estado_nombre)
                        estado_obj = estados_dict.get(estado_norm)
                        if not estado_obj:
                            errors.append(f"Reg {row_idx}: Estado '{estado_nombre}' no encontrado.")
                            continue

                        data_dict = {'encuentros_total': row[6] if len(row) > 6 else 0}

                        obj, created = Encuentros.objects.update_or_create(
                            fecha=fecha_val,
                            agencia=agencia_norm,
                            ciudadEU=ciudad_eu_norm,
                            estadoEU=estado_eu_norm,
                            estado=estado_obj,
                            nacionalidad=nac_obj,
                            defaults=data_dict
                        )
                    else:
                        estado_nombre = row[1]
                        nacionalidad_nombre = row[2]
                        
                        # Normalizar nacionalidad
                        nacionalidad_norm = normalizar_nombre(nacionalidad_nombre)
                        nac_obj = nacionalidades_dict.get(nacionalidad_norm)
                        
                        if not nac_obj:
                            errors.append(f"Reg {row_idx}: Nacionalidad '{nacionalidad_nombre}' no existe.")
                            continue

                        # Normalizar estado
                        estado_norm_busqueda = normalizar_nombre(estado_nombre)
                        estado_obj = estados_dict.get(estado_norm_busqueda)
                        
                        if not estado_obj:
                            errors.append(f"Reg {row_idx}: Estado '{estado_nombre}' no encontrado.")
                            continue

                        # Preparar datos
                        data_dict = {}
                        for i, field_name in enumerate(fields_to_populate):
                            excel_idx = i + 3
                            val = row[excel_idx] if excel_idx < len(row) else 0
                            data_dict[field_name] = val if val is not None else 0

                        obj, created = model_class.objects.update_or_create(
                            fecha=fecha_val,
                            estado=estado_obj,
                            nacionalidad=nac_obj,
                            defaults=data_dict
                        )
                    
                    if created:
                        rows_created += 1
                    else:
                        rows_updated += 1

            return JsonResponse({
                'status': 'success',
                'created': rows_created,
                'updated': rows_updated,
                'errors': errors
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def carga_nacionalidades(request):
    if not request.user.is_superuser:
        return render(request, 'base/error404.html')

    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, "Por favor seleccione un archivo Excel.")
            return redirect('carga_datos')

        try:
            wb = openpyxl.load_workbook(excel_file)
            sheet = wb.active
            
            created_count = 0
            for row in sheet.iter_rows(min_row=1, values_only=True):
                nombre_raw = row[0]
                if not nombre_raw: continue
                
                nombre_norm = normalizar_nombre(str(nombre_raw))
                if nombre_norm:
                    obj, created = Nacionalidad.objects.get_or_create(nombre=nombre_norm)
                    if created:
                        created_count += 1
            
            messages.success(request, f"Catálogo actualizado. Se agregaron {created_count} nuevas nacionalidades.")
        except Exception as e:
            messages.error(request, f"Error al procesar el catálogo: {str(e)}")
            
    return redirect('carga_datos')

def carga_oficinas(request):
    if not request.user.is_superuser:
        return render(request, 'base/error404.html')

    if request.method == 'POST':
        model_name = request.POST.get('model_name')
        excel_file = request.FILES.get('excel_file')
        tipo_punto = request.POST.get('tipo', '').upper()

        if not model_name or not excel_file:
            messages.error(request, "Por favor seleccione un modelo y un archivo.")
            return redirect('carga_datos')

        try:
            wb = openpyxl.load_workbook(excel_file)
            sheet = wb.active
            
            # Pre-cargar catálogos para eficiencia
            estados_dict = {normalizar_nombre(e.nombre): e for e in Estado.objects.all()}
            tipos_prh_dict = {normalizar_nombre(t.nombre): t for t in TipoPRH.objects.all()}
            
            created_count = 0
            updated_count = 0
            updated_rows = []
            errors = []

            with transaction.atomic():
                for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                    if not any(row): continue
                    
                    estado_raw = row[0]
                    estado_norm = normalizar_nombre(estado_raw)
                    estado_obj = estados_dict.get(estado_norm)

                    if not estado_obj:
                        errors.append(f"Fila {row_idx}: Estado '{estado_raw}' no encontrado.")
                        continue

                    if model_name == 'PuntosInternacionEstacion':
                        if not tipo_punto:
                            messages.error(request, "Debe seleccionar un tipo para Puntos de Internación.")
                            return redirect('carga_datos')
                        
                        nombre_raw = row[1]
                        lat = row[2]
                        lon = row[3]
                        
                        # Normalizar Nombre
                        nombre_norm = normalizar_nombre(nombre_raw)

                        obj, created = PuntosInternacionEstacion.objects.update_or_create(
                            nombre=nombre_norm,
                            tipo=tipo_punto,
                            defaults={
                                'estado': estado_obj,
                                'latitud': float(lat) if lat is not None else 0.0,
                                'longitud': float(lon) if lon is not None else 0.0
                            }
                        )
                        if created: 
                            created_count += 1
                        else: 
                            updated_count += 1
                            updated_rows.append(str(row_idx))

                    elif model_name == 'CatalogoOR':
                        titular_raw = row[1]
                        domicilio_raw = row[2]
                        correo_raw = row[3]

                        # Normalizar campos de texto
                        titular_norm = normalizar_nombre(titular_raw)
                        domicilio_norm = normalizar_nombre(domicilio_raw)
                        correo_norm = str(correo_raw).strip().lower() # Correo se mantiene con formato, pero sin espacios

                        obj, created = CatalogoOR.objects.update_or_create(
                            titular=titular_norm,
                            defaults={
                                'estado': estado_obj,
                                'domicilio': domicilio_norm,
                                'correo': correo_norm
                            }
                        )
                        if created: 
                            created_count += 1
                        else: 
                            updated_count += 1
                            updated_rows.append(str(row_idx))

                    elif model_name == 'PRHs':
                        # Formato: Estado(0), Nombre(1), Modalidad(2), Activo(3), Coordenadas(4), Lat(5), Lon(6)
                        if len(row) < 7:
                            errors.append(f"Fila {row_idx}: Faltan columnas (se requieren 7).")
                            continue

                        nombre_raw = row[1]
                        modalidad_raw = row[2]
                        activo_raw = str(row[3]).strip().upper()
                        coordenadas_raw = row[4]
                        lat = row[5]
                        lon = row[6]

                        # Normalizar campos
                        nombre_norm = normalizar_nombre(nombre_raw)
                        modalidad_norm = normalizar_nombre(modalidad_raw)
                        coordenadas_norm = normalizar_nombre(coordenadas_raw)

                        # Validar Modalidad
                        tipo_obj = tipos_prh_dict.get(modalidad_norm)
                        if not tipo_obj:
                            errors.append(f"Fila {row_idx}: Modalidad '{modalidad_raw}' no existe en el catálogo.")
                            continue

                        # Convertir Activo a Boolean
                        activo_bool = True if activo_raw == "ACTIVO" else False

                        obj, created = PRHs.objects.update_or_create(
                            nombre=nombre_norm,
                            estado=estado_obj,
                            modalidad=tipo_obj,
                            defaults={
                                'activo': activo_bool,
                                'coordenadasTexto': coordenadas_norm,
                                'latitud': float(lat) if lat is not None else 0.0,
                                'longitud': float(lon) if lon is not None else 0.0
                            }
                        )
                        if created: 
                            created_count += 1
                        else: 
                            updated_count += 1
                            updated_rows.append(str(row_idx))

            if errors:
                for err in errors: messages.warning(request, err)
            
            res_msg = f"Carga de oficinas completada. Creados: {created_count}, Actualizados: {updated_count}"
            if updated_rows:
                res_msg += f" (Filas: {', '.join(updated_rows)})"
            
            messages.success(request, res_msg)
        except Exception as e:
            messages.error(request, f"Error al procesar el archivo: {str(e)}")
            
    return redirect('carga_datos')

def reportes(request):
    """Vista para el tablero de reportes con datos reales y gráficas Bokeh."""
    if not request.user.is_superuser:
        return render(request, 'base/error404.html')

    rubro = request.GET.get('rubro', 'Encuentros')
    fecha_max = get_global_update_date() or date.today()
    
    # Periodos Definidos
    CSP_START = date(2024, 10, 1)
    TRUMP_START = date(2025, 1, 20)
    SEMANA_START = fecha_max - timedelta(days=6)
    INICIO_2026 = date(2026, 1, 1)

    # Función auxiliar para obtener totales
    def get_data(start, end):
        if rubro == 'Encuentros':
            val = Encuentros.objects.filter(fecha__range=[start, end]).aggregate(t=Sum('encuentros_total'))['t'] or 0
            return val, None, None
        elif rubro == 'Rescatados':
            val = ExtRescatados.objects.filter(fecha__range=[start, end]).aggregate(t=Sum('rescatados'))['t'] or 0
            return val, None, None
        elif rubro == 'Recibidos':
            mex = Repatriados.objects.filter(fecha__range=[start, end]).aggregate(t=Sum('mex_rep'))['t'] or 0
            ext = Recibidos.objects.filter(fecha__range=[start, end]).aggregate(t=Sum('ext_rec'))['t'] or 0
            return mex + ext, mex, ext
        return 0, 0, 0

    # Texto del rubro
    rubro_text = "Encuentros" if rubro == 'Encuentros' else ("Recibidos" if rubro == 'Recibidos' else "Rescatados")

    # Cálculos para tarjetas
    def build_card(start, end, label):
        if rubro == 'Encuentros':
            qs_period = Encuentros.objects.filter(fecha__range=[start, end])
            total = qs_period.aggregate(total=Sum('encuentros_total'))['total'] or 0
            
            # Intentar identificar mexicanos por nombre (MEXICO, MEXICA, etc.)
            mex = qs_period.filter(
                Q(nacionalidad__nombre__icontains='MEXICO') | 
                Q(nacionalidad__nombre__icontains='MEXICA')
            ).aggregate(total=Sum('encuentros_total'))['total'] or 0
            ext = total - mex
            
            p_mex = round((mex / total * 100)) if total > 0 else 0
            p_ext = 100 - p_mex if total > 0 else 0
        elif rubro == 'Rescatados':
            total = ExtRescatados.objects.filter(fecha__range=[start, end]).aggregate(total=Sum('rescatados'))['total'] or 0
            mex, ext, p_mex, p_ext = 0, total, 0, 100 # Rescatados suele ser solo para extranjeros en este modelo
        else: # Recibidos
            mex = Repatriados.objects.filter(fecha__range=[start, end]).aggregate(total=Sum('mex_rep'))['total'] or 0
            ext = Recibidos.objects.filter(fecha__range=[start, end]).aggregate(total=Sum('ext_rec'))['total'] or 0
            total = mex + ext
            p_mex = round((mex / total * 100)) if total > 0 else 0
            p_ext = 100 - p_mex if total > 0 else 0

        days = (end - start).days + 1
        avg = round(total / days) if days > 0 else 0
        
        # Formatear periodo
        if label == "Semana":
            fmt_periodo = f"del {start.strftime('%d')} al {end.strftime('%d de %b.')} de {end.year}"
        else:
            fmt_periodo = f"{start.strftime('%d/%b/%y')} a {end.strftime('%d/%b/%y')}"

        return {
            'total': f"{total:,}",
            'promedio': f"{avg:,}",
            'periodo': fmt_periodo,
            'subtitulo': f"{rubro}",
            'mex': f"{mex:,}",
            'ext': f"{ext:,}",
            'p_mex': p_mex,
            'p_ext': p_ext
        }

    card_semana = build_card(SEMANA_START, fecha_max, "Semana")
    card_csp = build_card(CSP_START, fecha_max, "CSP")
    card_trump = build_card(TRUMP_START, fecha_max, "Trump")

    # --- GRÁFICA DE BARRAS (EVOLUCIÓN DIARIA) ---
    # Obtenemos datos agrupados por día
    if rubro == 'Encuentros':
        qs = Encuentros.objects.filter(fecha__range=[CSP_START, fecha_max]) \
            .annotate(day=TruncDay('fecha')) \
            .values('day') \
            .annotate(total=Sum('encuentros_total')) \
            .order_by('day')
    elif rubro == 'Rescatados':
        qs = ExtRescatados.objects.filter(fecha__range=[CSP_START, fecha_max]) \
            .annotate(day=TruncDay('fecha')) \
            .values('day') \
            .annotate(total=Sum('rescatados')) \
            .order_by('day')
    else: # Recibidos
        rep_qs = Repatriados.objects.filter(fecha__range=[CSP_START, fecha_max]) \
            .annotate(day=TruncDay('fecha')) \
            .values('day') \
            .annotate(total=Sum('mex_rep'))
        rec_qs = Recibidos.objects.filter(fecha__range=[CSP_START, fecha_max]) \
            .annotate(day=TruncDay('fecha')) \
            .values('day') \
            .annotate(total=Sum('ext_rec'))
        
        combined = {}
        for item in rep_qs:
            combined[item['day']] = item['total']
        for item in rec_qs:
            combined[item['day']] = combined.get(item['day'], 0) + item['total']
        
        qs = [{'day': d, 'total': combined[d]} for d in sorted(combined.keys())]

    x_data = []
    y_data = []
    for d in qs:
        day_val = d['day'] if isinstance(d, dict) else d.day
        if isinstance(day_val, date) and not isinstance(day_val, datetime):
            day_val = datetime.combine(day_val, datetime.min.time())
        x_data.append(day_val)
        y_data.append(d['total'] if isinstance(d, dict) else d.total)

    source_bar = ColumnDataSource(data=dict(x=x_data, y=y_data))

    # Normalizar fechas a datetime para comparaciones seguras
    def to_datetime(d):
        if isinstance(d, date) and not isinstance(d, datetime):
            return datetime.combine(d, datetime.min.time())
        return d

    dt_fecha_max = to_datetime(fecha_max)
    dt_csp_start = to_datetime(CSP_START)
    
    # Determinar rango inicial para p1 (últimos 180 días)
    initial_range_start = dt_fecha_max - timedelta(days=180)
    if x_data and x_data[0] > initial_range_start:
        initial_range_start = x_data[0]
    elif not x_data:
        initial_range_start = dt_csp_start

    p1_opts = {
        'height': 300, 
        'sizing_mode': "stretch_width",
        'x_axis_type': "datetime",
        'x_axis_location': "above",
        'x_range': (initial_range_start, dt_fecha_max),
        'toolbar_location': "right", 
        'tools': "pan,box_zoom,xwheel_zoom,reset,tap",
        'background_fill_color': "#efefef",
        'border_fill_color': None,
        'outline_line_color': "#666666"
    }
    
    p1 = figure(**p1_opts)
    p1.y_range.start = 0
    p1.line(x='x', y='y', line_width=2, color="#285C4D", source=source_bar)
    
    p1.xgrid.grid_line_color = "#ffffff"
    p1.ygrid.grid_line_color = "#ffffff"
    p1.yaxis.visible = True
    p1.yaxis.major_label_text_font_size = "9pt"
    p1.yaxis.formatter = NumeralTickFormatter(format="0a")
    p1.xaxis.major_label_text_font_size = "9pt"
    p1.xaxis.formatter = DatetimeTickFormatter(
        days="%d %b",
        months="%b %Y",
        years="%Y"
    )
    
    hover_bar = HoverTool(tooltips=[("Fecha", "@x{%d/%b/%y}"), ("Valor", "@y{0,0}")], formatters={'@x': 'datetime'})
    p1.add_tools(hover_bar)
    
    # --- GRÁFICA DE SELECCIÓN (NAVIGATOR) ---
    select = figure(
        title="Arrastra el recuadro para navegar por el tiempo",
        height=100, sizing_mode="stretch_width",
        x_axis_type="datetime", y_axis_type=None,
        tools="", toolbar_location=None, 
        background_fill_color="#f9f9f9",
        outline_line_color="#e5e7eb"
    )
    
    select.line(x='x', y='y', color="#285C4D", alpha=0.5, source=source_bar)
    select.ygrid.grid_line_color = None
    select.xgrid.grid_line_color = None
    select.xaxis.major_label_text_font_size = "7pt"
    
    range_tool = RangeTool(x_range=p1.x_range)
    range_tool.overlay.fill_color = "#285C4D"
    range_tool.overlay.fill_alpha = 0.2
    select.add_tools(range_tool)
    
    # Empaquetamos ambas en una columna
    layout_p1 = column(p1, select, sizing_mode="stretch_width")

    tap_bar_js = CustomJS(args=dict(source=source_bar), code="""
        const indices = source.selected.indices;
        if (indices.length > 0) {
            const idx = indices[0];
            const date = new Date(source.data['x'][idx]);
            const period = date.toLocaleDateString('es-MX', {day: 'numeric', month: 'short', year: 'numeric'});
            const val = source.data['y'][idx];
            const valFmt = new Intl.NumberFormat('en-US').format(val);
            if (window.showTouchToast) window.showTouchToast(period, valFmt);
        }
    """)
    source_bar.selected.js_on_change('indices', tap_bar_js)

    # --- GRÁFICA DE LÍNEAS (SEMANAL 2026) ---
    if rubro == 'Encuentros':
        qs_w = Encuentros.objects.filter(fecha__range=[INICIO_2026, fecha_max]) \
            .annotate(week=TruncWeek('fecha')) \
            .values('week') \
            .annotate(total=Sum('encuentros_total')) \
            .order_by('week')
    elif rubro == 'Rescatados':
        qs_w = ExtRescatados.objects.filter(fecha__range=[INICIO_2026, fecha_max]) \
            .annotate(week=TruncWeek('fecha')) \
            .values('week') \
            .annotate(total=Sum('rescatados')) \
            .order_by('week')
    else: # Recibidos
        rep_w = Repatriados.objects.filter(fecha__range=[INICIO_2026, fecha_max]) \
            .annotate(week=TruncWeek('fecha')) \
            .values('week') \
            .annotate(total=Sum('mex_rep'))
        rec_w = Recibidos.objects.filter(fecha__range=[INICIO_2026, fecha_max]) \
            .annotate(week=TruncWeek('fecha')) \
            .values('week') \
            .annotate(total=Sum('ext_rec'))
        
        combined_w = {}
        for item in rep_w: combined_w[item['week']] = item['total']
        for item in rec_w: combined_w[item['week']] = combined_w.get(item['week'], 0) + item['total']
        
        qs_w = [{'week': w, 'total': combined_w[w]} for w in sorted(combined_w.keys())]

    x_line = []
    y_line = []
    for d in qs_w:
        w_date = d['week'] if isinstance(d, dict) else d['week']
        x_line.append(w_date.strftime('%d-%m'))
        y_line.append(d['total'])

    source_line = ColumnDataSource(data=dict(x=x_line, y=y_line))

    # P2 usa FactorRange, si x_line está vacío, Bokeh puede fallar.
    p2_args = {
        'height': 300, 
        'sizing_mode': "stretch_width",
        'toolbar_location': None,
        'tools': "tap",
        'background_fill_color': None,
        'border_fill_color': None,
        'outline_line_color': None
    }
    if x_line:
        p2_args['x_range'] = x_line
    
    p2 = figure(**p2_args)
    p2.line(x='x', y='y', line_width=2, color="#86895D", source=source_line)
    p2.scatter(x='x', y='y', size=8, color="#86895D", fill_color="white", source=source_line)
    
    p2.xgrid.grid_line_color = None
    p2.ygrid.grid_line_color = None
    p2.yaxis.visible = False
    p2.xaxis.major_label_orientation = 1.5708
    p2.xaxis.major_label_text_font_size = "7pt"

    hover_line = HoverTool(tooltips=[("Semana", "@x"), ("Total", "@y{0,0}")])
    p2.add_tools(hover_line)

    # Total 2026 para el footer
    total_2026 = sum(y_line)

    # === GRÁFICA TOP 10 NACIONALIDADES DINÁMICA ===
    start_init = initial_range_start.date() if isinstance(initial_range_start, datetime) else initial_range_start
    end_init = fecha_max
    
    if rubro == 'Encuentros':
        ranking = Encuentros.objects.filter(fecha__range=[start_init, end_init]).values('nacionalidad__nombre').annotate(total=Sum('encuentros_total')).order_by('-total')[:10]
        top_names = [item['nacionalidad__nombre'] or 'OTRO' for item in ranking][::-1]
        top_values = [int(item['total'] or 0) for item in ranking][::-1]
    elif rubro == 'Rescatados':
        ranking = ExtRescatados.objects.filter(fecha__range=[start_init, end_init]).values('nacionalidad__nombre').annotate(total=Sum('rescatados')).order_by('-total')[:10]
        top_names = [item['nacionalidad__nombre'] or 'OTRO' for item in ranking][::-1]
        top_values = [int(item['total'] or 0) for item in ranking][::-1]
    else: # Recibidos
        res_rec = Recibidos.objects.filter(fecha__range=[start_init, end_init]).values('nacionalidad__nombre').annotate(total=Sum('ext_rec')).order_by('-total')[:10]
        mex_total = Repatriados.objects.filter(fecha__range=[start_init, end_init]).aggregate(total=Sum('mex_rep'))['total'] or 0
        r_list = [{'n': 'MÉXICO', 'v': int(mex_total)}]
        for item in res_rec:
            r_list.append({'n': item['nacionalidad__nombre'], 'v': int(item['total'] or 0)})
        r_sorted = sorted(r_list, key=lambda x: x['v'], reverse=True)[:10]
        top_names = [item['n'] for item in r_sorted][::-1]
        top_values = [item['v'] for item in r_sorted][::-1]

    source_top = ColumnDataSource(data=dict(names=top_names, values=top_values))
    p_top = figure(y_range=top_names, height=450, title=None,
                   toolbar_location=None, tools="", sizing_mode="stretch_width")
    p_top.hbar(y='names', right='values', height=0.7, color="#285C4D", source=source_top)
    p_top.x_range.start = 0
    p_top.xaxis.formatter = NumeralTickFormatter(format="0a")
    p_top.outline_line_color = None
    p_top.grid.grid_line_color = None
    p_top.yaxis.major_label_text_font_size = "9pt"
    p_top.yaxis.major_label_text_font_style = "bold"
    
    h_top = HoverTool(tooltips=[("País", "@names"), ("Total", "@values{0,0}")])
    p_top.add_tools(h_top)

    # Callback JS para actualizar Top 10 cuando cambia el rango de p1
    update_top10_js = CustomJS(args=dict(source=source_top, y_range=p_top.y_range, rubro=rubro), code="""
        const start = cb_obj.start;
        const end = cb_obj.end;
        if (window.top10Timeout) clearTimeout(window.top10Timeout);
        window.top10Timeout = setTimeout(() => {
            fetch(`/mapa/api/reporte-nacionalidades?rubro=${rubro}&start=${Math.round(start)}&end=${Math.round(end)}`)
                .then(response => response.json())
                .then(res => {
                    if (res.status === 'success') {
                        const new_names = res.data.map(d => d.name).reverse();
                        const new_values = res.data.map(d => d.value).reverse();
                        source.data = { names: new_names, values: new_values };
                        y_range.factors = new_names;
                        source.change.emit();
                    }
                });
        }, 400);
    """)
    p1.x_range.js_on_change('start', update_top10_js)

    plot_script, plot_divs = components((layout_p1, p2, p_top))
    plot_bar_div, plot_line_div, plot_top_div = plot_divs

    context = {
        'rubro': rubro,
        'card_semana': card_semana,
        'card_csp': card_csp,
        'card_trump': card_trump,
        'plot_script': plot_script,
        'plot_bar_div': plot_bar_div,
        'plot_line_div': plot_line_div,
        'plot_top_div': plot_top_div,
        'total_2026': f"{total_2026:,}",
    }

    return render(request, 'mapa/reportes.html', context)
