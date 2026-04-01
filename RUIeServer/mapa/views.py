from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Estado, Nacionalidad, Repatriados, Recibidos, ExtRescatados, Ingresos, Tramites, Retornados, Inadmitidos
from django.apps import apps
import openpyxl
from datetime import datetime
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, HoverTool, TapTool, CustomJS, LinearColorMapper
from bokeh.embed import components
import json
import random
import os
from django.conf import settings

from django.db import transaction, models
from django.db.models import Sum
from datetime import date
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

# --- VIEW PRINCIPAL ---

def mapa_informacion(request):
    if not request.user.is_superuser:
        return render(request, 'base/error404.html')

    CS_START = date(2024, 10, 1)
    DT_START = date(2025, 1, 20)
    TODAY = date.today()

    totals_cs = get_totals_by_period(CS_START, TODAY)
    totals_dt = get_totals_by_period(DT_START, TODAY)


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
    
    # Crear figura de Bokeh
    p = figure(
        title="Monitoreo Migratorio por Estado",
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
    from bokeh.palettes import Greens256
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
        hover_fill_color={'field': 'cs_todos', 'transform': color_mapper},
        hover_line_color="#285C4D",
        hover_line_width=2,
        selection_fill_color={'field': 'cs_todos', 'transform': color_mapper},
        selection_line_color="#285C4D",
        selection_line_width=2,
        nonselection_fill_alpha=0.2,
        nonselection_line_alpha=0.2
    )
    
    # Añadir HoverTool inicial configurado a 'Todos' (muestra todas las categorías)
    hover_html = """
        <div style="padding: 8px; min-width: 170px; font-family: Arial, sans-serif;">
            <div style="font-size: 16px; font-weight: 500; margin-bottom: 3px; color: #333;">@name</div>
            <div style="border-bottom: 1px solid #ddd; margin-bottom: 5px;"></div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                <span style="font-size: 12px; color: #333;">Repatriados</span>
                <span style="font-size: 12px; font-weight: 500; color: #333;">@cs_str_repatriados</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 3px;"></div>

            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                <span style="font-size: 12px; color: #333;">Recibidos</span>
                <span style="font-size: 12px; font-weight: 500; color: #333;">@cs_str_recibidos</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 3px;"></div>

            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                <span style="font-size: 12px; color: #333;">Rescatados</span>
                <span style="font-size: 12px; font-weight: 500; color: #333;">@cs_str_rescatados</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 3px;"></div>

            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                <span style="font-size: 12px; color: #333;">Ingresos</span>
                <span style="font-size: 12px; font-weight: 500; color: #333;">@cs_str_ingresos</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 3px;"></div>

            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                <span style="font-size: 12px; color: #333;">Trámites</span>
                <span style="font-size: 12px; font-weight: 500; color: #333;">@cs_str_tramites</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 3px;"></div>

            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                <span style="font-size: 12px; color: #333;">Retornados</span>
                <span style="font-size: 12px; font-weight: 500; color: #333;">@cs_str_retornados</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 3px;"></div>

            <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                <span style="font-size: 12px; color: #333;">Inadmitidos</span>
                <span style="font-size: 12px; font-weight: 500; color: #333;">@cs_str_inadmitidos</span>
            </div>
        </div>
    """
    
    hover = HoverTool(
        renderers=[states],
        tooltips=hover_html
    )
    p.add_tools(hover)
    
    national_data = {
        'name': 'Nacional',
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
        } else {
            window.selectedStateData = national;
        }
        
        if (window.updateInformationPanel) {
            window.updateInformationPanel();
        }
    """)
    p.select(TapTool).callback = tap_js

    script, div = components(p)
    
    context = {
        'map_script': script,
        'map_div': div,
        'national_data_json': json.dumps(national_data),
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

    return render(request, 'mapa/carga_datos.html', {'models': models_available.keys()})

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
