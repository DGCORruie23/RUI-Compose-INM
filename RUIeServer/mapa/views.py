from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Estado, Repatriados, Recibidos, ExtRescatados, Ingresos, Tramites, Retornados, Inadmitidos
from django.apps import apps
import openpyxl
from datetime import datetime
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, HoverTool, TapTool, CustomJS
from bokeh.embed import components
import json
import random
import os
from django.conf import settings

from django.db.models import Sum
from datetime import date
import unicodedata

def normalize_nome(texto):
    if not texto: return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', str(texto))
        if unicodedata.category(c) != 'Mn'
    ).upper().strip()

def mapa_informacion(request):
    # Restricción de acceso: Solo superusuarios
    if not request.user.is_superuser:
        return render(request, 'base/error404.html')

    # Definición de Periodos
    CS_START = date(2024, 10, 1)
    DT_START = date(2025, 1, 20)
    TODAY = date.today()

    # Función auxiliar para obtener totales por estado en un rango de fechas
    def get_totals_by_period(start, end):
        data_by_state = {}
        estados = Estado.objects.all()
        for edo in estados:
            key = normalize_nome(edo.nombre)
            
            # Agregaciones por modelo
            rep = Repatriados.objects.filter(estado=edo, fecha__range=[start, end]).aggregate(
                total=Sum('mex_rep'), adultos=Sum('adultos'), menores=Sum('menores'),
                nna_solo=Sum('nna_solo'), nna_acom=Sum('nna_acom'),
                terrestres=Sum('terrestres'), vuelos=Sum('vuelos')
            )
            ret = Retornados.objects.filter(estado=edo, fecha__range=[start, end]).aggregate(
                total=Sum('retornados_total'), deportado=Sum('deportado'), retornado=Sum('retornado')
            )
            res = ExtRescatados.objects.filter(estado=edo, fecha__range=[start, end]).aggregate(
                total=Sum('rescatados'), una_vez=Sum('una_vez'), reincidente=Sum('reincidente'),
                estacion=Sum('estacion'), dif=Sum('dif'), conduccion=Sum('conduccion')
            )
            ing = Ingresos.objects.filter(estado=edo, fecha__range=[start, end]).aggregate(
                total=Sum('ingresos_total'), aereos=Sum('aereos'), maritimos=Sum('maritimos'), terrestres=Sum('terrestres')
            )
            tra = Tramites.objects.filter(estado=edo, fecha__range=[start, end]).aggregate(
                total=Sum('total_documentos'),
                res_perm=Sum('residente_permanente'), res_temp=Sum('residente_temporal'),
                res_est=Sum('residente_temp_estudio'), vis_hum=Sum('visitante_humanitario'),
                vis_adop=Sum('visitante_adopcion'), vis_reg=Sum('visitante_regional'),
                vis_trab=Sum('visitante_trabajador')
            )

            data_by_state[key] = {
                'repatriados': rep['total'] or 0,
                'rep_adultos': rep['adultos'] or 0,
                'rep_menores': rep['menores'] or 0,
                'rep_nna_solo': rep['nna_solo'] or 0,
                'rep_nna_acom': rep['nna_acom'] or 0,
                'rep_terrestres': rep['terrestres'] or 0,
                'rep_vuelos': rep['vuelos'] or 0,

                'retornados': ret['total'] or 0,
                'ret_deportado': ret['deportado'] or 0,
                'ret_retornado': ret['retornado'] or 0,

                'rescatados': res['total'] or 0,
                'res_una_vez': res['una_vez'] or 0,
                'res_reincidente': res['reincidente'] or 0,
                'res_estacion': res['estacion'] or 0,
                'res_dif': res['dif'] or 0,
                'res_conduccion': res['conduccion'] or 0,

                'ingresos': ing['total'] or 0,
                'ing_aereos': ing['aereos'] or 0,
                'ing_maritimos': ing['maritimos'] or 0,
                'ing_terrestres': ing['terrestres'] or 0,

                'tramites': tra['total'] or 0,
                'tra_res_perm': tra['res_perm'] or 0,
                'tra_res_temp': tra['res_temp'] or 0,
                'tra_res_est': tra['res_est'] or 0,
                'tra_vis_hum': tra['vis_hum'] or 0,
                'tra_vis_adop': tra['vis_adop'] or 0,
                'tra_vis_reg': tra['vis_reg'] or 0,
                'tra_vis_trab': tra['vis_trab'] or 0,
            }
        return data_by_state

    # Cargar datos para ambos periodos
    totals_cs = get_totals_by_period(CS_START, TODAY)
    totals_dt = get_totals_by_period(DT_START, TODAY)

    # Ruta al archivo geojson descargado
    geojson_path = os.path.join(settings.BASE_DIR, 'mapa', 'static', 'mapa', 'data', 'mexico.geojson')
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geo_data = json.load(f)
          # Inyectar datos reales en cada estado
    for feature in geo_data['features']:
        name_normalized = normalize_nome(feature['properties']['name'])
        
        # Obtener datos de los diccionarios (usar default con ceros para todos los campos nuevos)
        default_vals = {
            'repatriados': 0, 'rep_adultos': 0, 'rep_menores': 0, 'rep_nna_solo': 0, 'rep_nna_acom': 0, 'rep_terrestres': 0, 'rep_vuelos': 0,
            'retornados': 0, 'ret_deportado': 0, 'ret_retornado': 0,
            'rescatados': 0, 'res_una_vez': 0, 'res_reincidente': 0, 'res_estacion': 0, 'res_dif': 0, 'res_conduccion': 0,
            'ingresos': 0, 'ing_aereos': 0, 'ing_maritimos': 0, 'ing_terrestres': 0,
            'tramites': 0, 'tra_res_perm': 0, 'tra_res_temp': 0, 'tra_res_est': 0, 'tra_vis_hum': 0, 'tra_vis_adop': 0, 'tra_vis_reg': 0, 'tra_vis_trab': 0,
        }
        
        cs = totals_cs.get(name_normalized, default_vals)
        dt = totals_dt.get(name_normalized, default_vals)

        # Inyectar en GeoJSON (usamos prefijos cs_ y dt_)
        for k in default_vals:
            feature['properties'][f'cs_{k}'] = cs[k]
            feature['properties'][f'dt_{k}'] = dt[k]
        
        # Compatibilidad con tooltips existentes (usar totales de CS)
        feature['properties']['repatriados'] = f"{cs['repatriados']:,}"
        feature['properties']['retornados'] = f"{cs['retornados']:,}"
        feature['properties']['rescatados'] = f"{cs['rescatados']:,}"
        feature['properties']['ingresos'] = f"{cs['ingresos']:,}"
        feature['properties']['tramites'] = f"{cs['tramites']:,}"
        
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
    
    # Dibujar los estados
    states = p.patches(
        'xs', 'ys', 
        source=geo_source,
        fill_color="#cbd5e1",
        line_color="#ffffff",
        line_width=1,
        fill_alpha=1.0,
        hover_fill_color="#285C4D",
        selection_fill_color="#285C4D",
        nonselection_fill_alpha=0.2,
        nonselection_fill_color="#cbd5e1",
        nonselection_line_alpha=0.2
    )
    
    # Añadir HoverTool con HTML personalizado según imagen (Compacto)
    hover_html = """
        <div style="padding: 8px; min-width: 160px; font-family: Arial, sans-serif;">
            <div style="font-size: 16px; font-weight: 500; margin-bottom: 3px; color: #333;">@name</div>
            <div style="border-bottom: 1px solid #ddd; margin-bottom: 5px;"></div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-size: 12px; color: #333;">Repatriados</span>
                <span style="font-size: 12px; font-weight: 500; color: #333;">@repatriados</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 5px;"></div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-size: 12px; color: #333;">Retornados</span>
                <span style="font-size: 12px; font-weight: 500; color: #333;">@retornados</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 5px;"></div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-size: 12px; color: #333;">Rescatados</span>
                <span style="font-size: 12px; font-weight: 500; color: #333;">@rescatados</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 5px;"></div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-size: 12px; color: #333;">Ingresos</span>
                <span style="font-size: 12px; font-weight: 500; color: #333;">@ingresos</span>
            </div>
            <div style="border-bottom: 1px solid #eee; margin-bottom: 5px;"></div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                <span style="font-size: 12px; color: #333;">Trámites</span>
                <span style="font-size: 12px; font-weight: 500; color: #333;">@tramites</span>
            </div>
        </div>
    """
    
    hover = HoverTool(
        renderers=[states],
        tooltips=hover_html
    )
    p.add_tools(hover)
    
    # Calcular Totales Nacionales
    def calc_national(totals_dict):
        # Usar las mismas claves que el diccionario por estado
        keys = [
            'repatriados', 'rep_adultos', 'rep_menores', 'rep_nna_solo', 'rep_nna_acom', 'rep_terrestres', 'rep_vuelos',
            'retornados', 'ret_deportado', 'ret_retornado',
            'rescatados', 'res_una_vez', 'res_reincidente', 'res_estacion', 'res_dif', 'res_conduccion',
            'ingresos', 'ing_aereos', 'ing_maritimos', 'ing_terrestres',
            'tramites', 'tra_res_perm', 'tra_res_temp', 'tra_res_est', 'tra_vis_hum', 'tra_vis_adop', 'tra_vis_reg', 'tra_vis_trab'
        ]
        national = {k: 0 for k in keys}
        for state_data in totals_dict.values():
            for k in keys:
                if k in state_data:
                    national[k] += state_data[k]
        return national

    national_data = {
        'name': 'Nacional',
        'cs': calc_national(totals_cs),
        'dt': calc_national(totals_dt)
    }

    # Añadir CustomJS para el evento de click (Tap)
    tap_js = CustomJS(args=dict(source=geo_source, national=national_data), code="""
        const indices = source.selected.indices;
        const keys = [
            'repatriados', 'rep_adultos', 'rep_menores', 'rep_nna_solo', 'rep_nna_acom', 'rep_terrestres', 'rep_vuelos',
            'retornados', 'ret_deportado', 'ret_retornado',
            'rescatados', 'res_una_vez', 'res_reincidente', 'res_estacion', 'res_dif', 'res_conduccion',
            'ingresos', 'ing_aereos', 'ing_maritimos', 'ing_terrestres',
            'tramites', 'tra_res_perm', 'tra_res_temp', 'tra_res_est', 'tra_vis_hum', 'tra_vis_adop', 'tra_vis_reg', 'tra_vis_trab'
        ];

        if (indices.length > 0) {
            const index = indices[0];
            const data = source.data;
            
            const newStateData = {
                name: data['name'][index],
                cs: {},
                dt: {}
            };

            keys.forEach(k => {
                newStateData.cs[k] = data[`cs_${k}`][index];
                newStateData.dt[k] = data[`dt_${k}`][index];
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
            
            rows_created = 0
            rows_updated = 0
            
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not any(row): continue
                
                fecha_val = row[0]
                estado_nombre = row[1]
                
                # Convertir fecha si es necesario
                if isinstance(fecha_val, str):
                    fecha_val = datetime.strptime(fecha_val, '%Y-%m-%d').date()
                
                # Normalizar el nombre del estado del Excel para buscarlo
                estado_norm_busqueda = normalize_nome(estado_nombre)
                
                estado_obj = None
                # Buscar entre todos los estados existentes normalizando sus nombres
                for e in Estado.objects.all():
                    if normalize_nome(e.nombre) == estado_norm_busqueda:
                        estado_obj = e
                        break
                
                if not estado_obj:
                    messages.warning(request, f"Estado '{estado_nombre}' no encontrado. Se saltó la fila.")
                    continue

                # Construir diccionario de datos
                data = {'estado': estado_obj}
                # Empezamos desde el índice 2 porque 0 es fecha y 1 es estado
                for i, field_name in enumerate(fields[2:], start=2):
                    if i < len(row):
                        data[field_name] = row[i] if row[i] is not None else 0

                obj, created = model_class.objects.update_or_create(
                    fecha=fecha_val,
                    estado=estado_obj,
                    defaults=data
                )
                
                if created:
                    rows_created += 1
                else:
                    rows_updated += 1

            messages.success(request, f"Carga completada. Creados: {rows_created}, Actualizados: {rows_updated}")
            
        except Exception as e:
            messages.error(request, f"Error al procesar el archivo: {str(e)}")
            
        return redirect('carga_datos')

    return render(request, 'mapa/carga_datos.html', {'models': models_available.keys()})
