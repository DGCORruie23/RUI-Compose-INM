from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, HoverTool, TapTool, CustomJS, LinearColorMapper, FactorRange, ColumnDataSource, NumeralTickFormatter, RangeTool, DatetimeTickFormatter
from bokeh.layouts import column
from bokeh.embed import components
from bokeh.palettes import Greens256

from .models import (Estado, Nacionalidad, Repatriados, Recibidos, 
                    ExtRescatados, Ingresos, Tramites, Retornados, Inadmitidos, 
                    PuntosInternacionEstacion, CatalogoOR, Encuentros, TipoPRH, 
                    PRHs, Titular, Estudio, GradoAcademico, TelefonoTitular, CorreoTitular, 
                    TipoNombramiento, TrayectoriaLaboral, ExperienciaProfesional, TipoProcendencia,
                    Comodato, FiguraOcupacion, TipoInmueble, SituacionActual, TipoActividad, Inmueble, HistoricoComentarios, TipoOficina,
                    ProgramaIPC, PersonalINM, OrganigramaF, EstatusPersonal, TipoPlaza, TipoDependencia)
from usuarioL.models import usuarioL

from datetime import datetime
import json
import random
import os
import unicodedata
import base64
import openpyxl
import requests
import urllib3

from django.contrib import messages
from django.shortcuts import render, redirect
from django.apps import apps
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import transaction, models
from django.db.models import Sum, Count, Max, Q
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from datetime import date, timedelta
from django.http import JsonResponse


def normalizar_nombre(texto):
    if not texto: return ""
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode("utf-8")
    return str(texto).strip().upper()

def parse_curp_details(curp_str):
    if not curp_str or len(curp_str) < 10:
        return None, None
    
    curp_str = curp_str.strip().upper()
    
    birth_date = None
    try:
        yy_str = curp_str[4:6]
        mm_str = curp_str[6:8]
        dd_str = curp_str[8:10]
        
        # Determine century
        year_prefix = 1900
        if len(curp_str) >= 17:
            century_char = curp_str[16]
            if not(century_char.isdigit()):
                year_prefix = 2000
        else:
            yy_int = int(yy_str)
            if yy_int < 30:
                year_prefix = 2000
                
        year = year_prefix + int(yy_str)
        month = int(mm_str)
        day = int(dd_str)
        
        from datetime import date
        birth_date = date(year, month, day)
    except Exception:
        birth_date = None
        
    gender = None
    if len(curp_str) >= 11:
        g_char = curp_str[10]
        if g_char == 'H':
            gender = 'M' # Masculino
        elif g_char == 'M':
            gender = 'F' # Femenino
            
    return birth_date, gender

def get_user_state(request):
    """Retorna el objeto Estado asociado al usuario o None si es superusuario."""
    if request.user.is_superuser:
        return None
    
    profile = getattr(request.user, 'usuarioL', None)
    if not profile:
        return None
        
    # Mapeo especial para nombres comunes en usuarioL vs Estado
    mapping = {
        'CDMX': 'CIUDAD DE MEXICO',
        'EDOMEX': 'ESTADO DE MEXICO',
    }
    
    oficina = profile.oficinaR
    target_name = mapping.get(oficina, oficina)
    target_name = normalizar_nombre(target_name)
    
    try:
        return Estado.objects.get(nombre__iexact=target_name)
    except Estado.DoesNotExist:
        # Intento de búsqueda por normalización si falla el iexact
        for edo in Estado.objects.all():
            if normalizar_nombre(edo.nombre) == target_name:
                return edo
    return None

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

    # Agrupar y resumir datos en una sola consulta por modelo
    rep_raw = Repatriados.objects.filter(fecha__range=[start, end]) \
        .values('estado_id') \
        .annotate(
            total=Sum('mex_rep'),
            adultos=Sum('adultos'),
            menores=Sum('menores'),
            nna_solo=Sum('nna_solo'),
            nna_acom=Sum('nna_acom'),
            terrestres=Sum('terrestres'),
            vuelos=Sum('vuelos')
        )
    rep_map = {item['estado_id']: item for item in rep_raw}

    rec_raw = Recibidos.objects.filter(fecha__range=[start, end]) \
        .values('estado_id') \
        .annotate(
            total=Sum('ext_rec'),
            adultos=Sum('adultos'),
            menores=Sum('menores')
        )
    rec_map = {item['estado_id']: item for item in rec_raw}

    res_raw = ExtRescatados.objects.filter(fecha__range=[start, end]) \
        .values('estado_id') \
        .annotate(
            total=Sum('rescatados'),
            una_vez=Sum('una_vez'),
            reincidente=Sum('reincidente'),
            estacion=Sum('estacion'),
            dif=Sum('dif'),
            conduccion=Sum('conduccion')
        )
    res_map = {item['estado_id']: item for item in res_raw}

    ing_raw = Ingresos.objects.filter(fecha__range=[start, end]) \
        .values('estado_id') \
        .annotate(
            total=Sum('ingresos_total'),
            aereos=Sum('aereos'),
            maritimos=Sum('maritimos'),
            terrestres=Sum('terrestres')
        )
    ing_map = {item['estado_id']: item for item in ing_raw}

    tra_raw = Tramites.objects.filter(fecha__range=[start, end]) \
        .values('estado_id') \
        .annotate(
            total=Sum('total_documentos'),
            res_perm=Sum('residente_permanente'),
            res_temp=Sum('residente_temporal'),
            res_est=Sum('residente_temp_estudio'),
            vis_hum=Sum('visitante_humanitario'),
            vis_adop=Sum('visitante_adopcion'),
            vis_reg=Sum('visitante_regional'),
            vis_trab=Sum('visitante_trabajador')
        )
    tra_map = {item['estado_id']: item for item in tra_raw}

    ret_raw = Retornados.objects.filter(fecha__range=[start, end]) \
        .values('estado_id') \
        .annotate(
            total=Sum('retornados_total'),
            deportado=Sum('deportado'),
            retornado=Sum('retornado')
        )
    ret_map = {item['estado_id']: item for item in ret_raw}

    ina_raw = Inadmitidos.objects.filter(fecha__range=[start, end]) \
        .values('estado_id') \
        .annotate(
            total=Sum('inadmitidos_total')
        )
    ina_map = {item['estado_id']: item for item in ina_raw}

    for edo in estados:
        key = normalizar_nombre(edo.nombre)
        edo_id = edo.id
        
        rep = rep_map.get(edo_id, {})
        rec = rec_map.get(edo_id, {})
        res = res_map.get(edo_id, {})
        ing = ing_map.get(edo_id, {})
        tra = tra_map.get(edo_id, {})
        ret = ret_map.get(edo_id, {})
        ina = ina_map.get(edo_id, {})

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
    from .models import Repatriados, Recibidos, ExtRescatados, Ingresos, Tramites, Retornados, Inadmitidos
    
    models_to_check = [
        Repatriados, Recibidos, ExtRescatados, Ingresos, 
        Tramites, Retornados, Inadmitidos
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
    if not request.user.is_authenticated:
        return redirect('/log-in/?next=%s' % request.path)
    
    user_state = get_user_state(request)
    if not request.user.is_superuser and not user_state:
        return render(request, 'base/error404.html')

    fecha_act = get_global_update_date() or date.today()

    CS_START = date(2024, 10, 1)
    DT_START = date(2025, 1, 20)

    totals_cs = get_totals_by_period(CS_START, fecha_act)
    totals_dt = get_totals_by_period(DT_START, fecha_act)
    
    # --- Capa de Instrucciones (Consolidado desde API externa) ---
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    api_instrucciones = {}
    try:
        api_res = requests.get('https://172.16.16.167/api/mapa-datos/', verify=False, timeout=2.5)
        if api_res.status_code == 200:
            api_instrucciones = api_res.json()
    except Exception as e:
        print(f"Error al obtener instrucciones de la API: {str(e)}")

    instrucciones_avance = {}
    instrucciones_totales_dict = {}
    
    for edo in Estado.objects.all():
        edo_key = normalizar_nombre(edo.nombre)
        api_key = None
        for key in api_instrucciones.keys():
            if normalizar_nombre(key) == edo_key:
                api_key = key
                break
        
        visits = api_instrucciones.get(api_key, []) if api_key else []
        active_visits = [v for v in visits if v.get('pendiente', 0) > 0]
        
        if active_visits:
            avg_avance = sum(v.get('avance', 0) for v in active_visits) // len(active_visits)
            total_pendientes = sum(v.get('pendiente', 0) for v in visits)
            total_atendidos = sum(v.get('atendido', 0) for v in visits)
            total_acuerdos = sum(v.get('total', 0) for v in visits)
            
            instrucciones_avance[edo_key] = avg_avance
            instrucciones_totales_dict[edo_key] = {
                'avance': avg_avance,
                'pendiente': total_pendientes,
                'atendido': total_atendidos,
                'total': total_acuerdos,
                'has_pending': True
            }
        else:
            if visits:
                total_atendidos = sum(v.get('atendido', 0) for v in visits)
                total_acuerdos = sum(v.get('total', 0) for v in visits)
                instrucciones_avance[edo_key] = 100
                instrucciones_totales_dict[edo_key] = {
                    'avance': 100,
                    'pendiente': 0,
                    'atendido': total_atendidos,
                    'total': total_acuerdos,
                    'has_pending': False
                }
            else:
                instrucciones_avance[edo_key] = 100
                instrucciones_totales_dict[edo_key] = {
                    'avance': 100,
                    'pendiente': 0,
                    'atendido': 0,
                    'total': 0,
                    'has_pending': False
                }

    estados_para_rankear = [item for item in instrucciones_totales_dict.items() if item[1]['has_pending']]
    estados_ordenados = sorted(estados_para_rankear, key=lambda x: x[1]['avance'])
    
    instrucciones_color_rank = {}
    for rank, (edo_key, data_val) in enumerate(estados_ordenados, start=1):
        instrucciones_color_rank[edo_key] = rank
    
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
        'recibidos_total': 'Recibidos',
        'instrucciones': 'Supervision'
    }

    # --- Recopilación de Infraestructura y Titulares ---
    infra_raw = PuntosInternacionEstacion.objects.values('estado__nombre', 'tipo').annotate(total=Count('id'))
    titulares_raw = Titular.objects.all().select_related('estado', 'tipo_nombramiento')
    
    infra_data = {}
    # Estructura base para todos los estados
    for edo in Estado.objects.all():
        infra_data[normalizar_nombre(edo.nombre)] = {
            'estado_id': edo.id,
            'AEREO': 0, 'MARITIMO': 0, 'TERRESTRE': 0, 'ESTACION': 0,
            'PRH': 0,
            'personal_total': 0,
            'personal_activo': 0,
            'personal_vacante': 0,
            'subrep_federal': 0,
            'subrep_local': 0,
            'rep_local': 0,
            'titular': 'Sin titular asignado',
            'titular_id': None,
            'foto': None,
            'tipo_nombramiento': None
        }
    
    # Población con datos reales
    for item in infra_raw:
        edo_name = normalizar_nombre(item['estado__nombre'])
        if edo_name in infra_data:
            infra_data[edo_name][item['tipo']] = item['total']
            
    for t in titulares_raw:
        edo_name = normalizar_nombre(t.estado.nombre)
        if edo_name in infra_data:
            infra_data[edo_name]['titular'] = f"{t.nombre} {t.apellido_paterno} {t.apellido_materno}"
            infra_data[edo_name]['titular_id'] = t.id
            infra_data[edo_name]['tipo_nombramiento'] = t.tipo_nombramiento.nombre if t.tipo_nombramiento else None
            if t.fotografia:
                infra_data[edo_name]['foto'] = t.fotografia.url

    # PRHs por estado
    prh_raw = PRHs.objects.values('estado__nombre').annotate(total=Count('id'))
    for item in prh_raw:
        edo_name = normalizar_nombre(item['estado__nombre'])
        if edo_name in infra_data:
            infra_data[edo_name]['PRH'] = item['total']

    # Personal por estado
    personal_qs = PersonalINM.objects.all().select_related('estado', 'estatus', 'tipo_plaza')
    for p in personal_qs:
        if not p.estado:
            continue
        
        tipo_plaza = (p.tipo_plaza.plazaT if p.tipo_plaza else '').upper()
        if tipo_plaza not in ['BASE', 'CONFIANZA']:
            continue

        edo_name = normalizar_nombre(p.estado.nombre)
        if edo_name in infra_data:
            infra_data[edo_name]['personal_total'] += 1
            estatus_name = (p.estatus.estatus if p.estatus else '').upper()
            if estatus_name == 'ACTIVO':
                infra_data[edo_name]['personal_activo'] += 1
            elif estatus_name == 'VACANTE':
                infra_data[edo_name]['personal_vacante'] += 1
            
            puesto_clean = normalizar_nombre(p.puesto_especifico)
            if 'SUB REPRESENTACION FEDERAL' in puesto_clean:
                infra_data[edo_name]['subrep_federal'] += 1
            elif 'SUB REPRESENTACION LOCAL' in puesto_clean:
                infra_data[edo_name]['subrep_local'] += 1
            elif 'REPRESENTACION LOCAL' in puesto_clean:
                infra_data[edo_name]['rep_local'] += 1

    # Totales Nacionales
    subrep_federal_nat = 0
    subrep_local_nat = 0
    rep_local_nat = 0
    for key, val in infra_data.items():
        subrep_federal_nat += val.get('subrep_federal', 0)
        subrep_local_nat += val.get('subrep_local', 0)
        rep_local_nat += val.get('rep_local', 0)

    infra_data[LABEL_NACIONAL] = {
        'estado_id': None,
        'AEREO': PuntosInternacionEstacion.objects.filter(tipo='AEREO').count(),
        'MARITIMO': PuntosInternacionEstacion.objects.filter(tipo='MARITIMO').count(),
        'TERRESTRE': PuntosInternacionEstacion.objects.filter(tipo='TERRESTRE').count(),
        'ESTACION': PuntosInternacionEstacion.objects.filter(tipo='ESTACION').count(),
        'PRH': PRHs.objects.count(),
        'personal_total': PersonalINM.objects.count(),
        'personal_activo': PersonalINM.objects.filter(estatus__estatus__iexact='ACTIVO').count(),
        'personal_vacante': PersonalINM.objects.filter(estatus__estatus__iexact='VACANTE').count(),
        'subrep_federal': subrep_federal_nat,
        'subrep_local': subrep_local_nat,
        'rep_local': rep_local_nat,
        'titular': 'Datos Nacionales',
        'foto': None,
        'tipo_nombramiento': None
    }


    # Valores por defecto para estados sin datos
    default_vals = {
        'todos': 0, 'color_t': 32, 'color_rep': 32, 'color_rec': 32, 'color_res': 32, 'color_ing': 32, 'color_tra': 32, 'color_ret': 32, 'color_ina': 32,
        'repatriados': 0, 'rep_adultos': 0, 'rep_menores': 0, 'rep_nna_solo': 0, 'rep_nna_acom': 0, 'rep_terrestres': 0, 'rep_vuelos': 0,
        'recibidos': 0, 'rec_adultos': 0, 'rec_menores': 0,
        'rescatados': 0, 'res_una_vez': 0, 'res_reincidente': 0, 'res_estacion': 0, 'res_dif': 0, 'res_conduccion': 0,
        'ingresos': 0, 'ing_aereos': 0, 'ing_maritimos': 0, 'ing_terrestres': 0,
        'tramites': 0, 'tra_res_perm': 0, 'tra_res_temp': 0, 'tra_res_est': 0, 'tra_vis_hum': 0, 'tra_vis_adop': 0, 'tra_vis_reg': 0, 'tra_vis_trab': 0,
        'retornados': 0, 'ret_deportado': 0, 'ret_retornado': 0, 'inadmitidos': 0,
        'instrucciones': 0, 'color_ins': 32
    }

    # Ruta al archivo geojson descargado
    geojson_path = os.path.join(settings.BASE_DIR, 'mapa', 'static', 'mapa', 'data', 'inegi_latlon_mexico.geojson')
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geo_data = json.load(f)

    # Filtrar el GeoJSON por estado si el usuario no es superusuario
    if user_state:
        user_state_name_normalized = normalizar_nombre(user_state.nombre)
        geo_data['features'] = [
            f for f in geo_data['features']
            if normalizar_nombre(f['properties']['name']) == user_state_name_normalized
        ]
    # Inyectar datos reales en cada estado
    for feature in geo_data['features']:
        name_normalized = normalizar_nombre(feature['properties']['name'])
        
        cs = totals_cs.get(name_normalized, default_vals).copy()
        dt = totals_dt.get(name_normalized, default_vals).copy()
        
        # Inyectar datos de instrucciones calculados
        ins_val = instrucciones_totales_dict.get(name_normalized, {'avance': 100, 'has_pending': False})
        ins_rank = instrucciones_color_rank.get(name_normalized, 32)
        
        cs['instrucciones'] = ins_val['avance']
        cs['color_ins'] = ins_rank
        dt['instrucciones'] = ins_val['avance']
        dt['color_ins'] = ins_rank
        
        # Inyectar en GeoJSON (usamos prefijos cs_, dt_ y pe_)
        for k in default_vals:
            feature['properties'][f'cs_{k}'] = cs[k]
            feature['properties'][f'dt_{k}'] = dt[k]
            feature['properties'][f'pe_{k}'] = cs[k] # Inicializar PE con valores de CS
        
        # Cadenas formateadas para el Tooltip Dinámico
        for k in ['todos', 'repatriados', 'recibidos', 'rescatados', 'ingresos', 'tramites', 'retornados', 'inadmitidos', 'instrucciones']:
            if k == 'instrucciones':
                feature['properties'][f'cs_str_{k}'] = f"{cs[k]}%"
                feature['properties'][f'dt_str_{k}'] = f"{dt[k]}%"
                feature['properties'][f'pe_str_{k}'] = f"{cs[k]}%"
            else:
                feature['properties'][f'cs_str_{k}'] = f"{cs[k]:,}"
                feature['properties'][f'dt_str_{k}'] = f"{dt[k]:,}"
                feature['properties'][f'pe_str_{k}'] = f"{cs[k]:,}"
        
    # --- Capa de Infraestructura (Iconos SVG) ---
    infra_points_objs = PuntosInternacionEstacion.objects.all()
    if user_state:
        infra_points_objs = infra_points_objs.filter(estado=user_state)
    infra_pts_data = []
    for pt in infra_points_objs:
        icon_file = 'terrestre2.svg' # Default
        if pt.tipo == 'AEREO': icon_file = 'aereo2.svg'
        elif pt.tipo == 'MARITIMO': icon_file = 'maritimo2.svg'
        elif pt.tipo == 'ESTACION': icon_file = 'estacion2.svg'
        
        infra_pts_data.append({
            'x': float(pt.longitud) if pt.longitud else 0,
            'y': float(pt.latitud) if pt.latitud else 0,
            'nombre': pt.nombre,
            'estado': normalizar_nombre(pt.estado.nombre),
            'tipo': pt.tipo,
            'url': f"{settings.STATIC_URL}mapa/icons/{icon_file}"
        })

    # --- Capa de Puntos de Rescate Humano (PRH) ---
    prh_points = PRHs.objects.all().select_related('modalidad')
    if user_state:
        prh_points = prh_points.filter(estado=user_state)
    prh_pts_data = []
    for pt in prh_points:
        icon = 'agente_activo2.svg' if pt.activo else 'agente_inactivo2.svg'
        prh_pts_data.append({
            'x': float(pt.longitud) if pt.longitud else 0,
            'y': float(pt.latitud) if pt.latitud else 0,
            'nombre': pt.nombre,
            'estado': normalizar_nombre(pt.estado.nombre),
            'modalidad': pt.modalidad.nombre,
            'status': 'Activo' if pt.activo else 'Inactivo',
            'url': f"{settings.STATIC_URL}mapa/icons/{icon}"
        })

    # --- Capa de Inmuebles (Icono OR_ACTIVO) ---
    inmuebles_objs = Inmueble.objects.all().prefetch_related('tipo_oficina')
    if user_state:
        inmuebles_objs = inmuebles_objs.filter(estado=user_state)
    inmuebles_pts_data = []
    for pt in inmuebles_objs:
        inmuebles_pts_data.append({
            'id': pt.id,
            'x': float(pt.longitud) if pt.longitud else 0,
            'y': float(pt.latitud) if pt.latitud else 0,
            'nombre': pt.nombre_inmueble,
            'estado': normalizar_nombre(pt.estado.nombre),
            'tipo': 'INMUEBLE',
            'tipo_oficina': [normalizar_nombre(to.nombre) for to in pt.tipo_oficina.all()],
            'url': f"{settings.STATIC_URL}mapa/icons/OR_ACTIVO.svg"
        })

    total_national_acuerdos = sum(s['total'] for s in instrucciones_totales_dict.values())
    total_national_atendidos = sum(s['atendido'] for s in instrucciones_totales_dict.values())
    national_avance = (total_national_atendidos * 100 // total_national_acuerdos) if total_national_acuerdos > 0 else 100

    if user_state:
        # Totales del estado del usuario
        user_state_key = normalizar_nombre(user_state.nombre)
        ins_val = instrucciones_totales_dict.get(user_state_key, {'avance': 100, 'has_pending': False})
        
        cs = totals_cs.get(user_state_key, default_vals).copy()
        dt = totals_dt.get(user_state_key, default_vals).copy()
        cs['instrucciones'] = ins_val['avance']
        dt['instrucciones'] = ins_val['avance']
        
        national_data = {
            'name': user_state.nombre.upper(),
            'cs': cs,
            'dt': dt,
            'pe': cs
        }
    else:
        national_data = {
            'name': LABEL_NACIONAL,
            'cs': calc_national(totals_cs),
            'dt': calc_national(totals_dt),
            'pe': calc_national(totals_cs)
        }
        national_data['cs']['instrucciones'] = national_avance
        national_data['dt']['instrucciones'] = national_avance
        national_data['pe']['instrucciones'] = national_avance
    
    context = {
        'geo_data_json': json.dumps(geo_data),
        'national_data_json': json.dumps(national_data),
        'infra_data_json': json.dumps(infra_data),
        'infra_pts_data_json': json.dumps(infra_pts_data),
        'prh_pts_data_json': json.dumps(prh_pts_data),
        'inmuebles_pts_data_json': json.dumps(inmuebles_pts_data),
        'label_nacional': LABEL_NACIONAL,
        'metric_labels': METRIC_LABELS,
        'metric_labels_json': json.dumps(METRIC_LABELS),
        'fecha_actualizacion': fecha_act,
        'instrucciones_api_json': json.dumps(api_instrucciones),
        'is_superuser': request.user.is_superuser,
        'user_state_name': user_state.nombre if user_state else '',
        'user_state_name_normalized': normalizar_nombre(user_state.nombre) if user_state else '',
    }
    
    return render(request, 'mapa/informacion.html', context)

def carga_datos(request):
    if not request.user.is_authenticated:
        return redirect('/log-in/?next=%s' % request.path)
    
    user_state = get_user_state(request)
    if not request.user.is_superuser and not user_state:
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
                        if user_state and estado_obj != user_state:
                            errors.append(f"Fila {row_idx}: No tiene permisos para modificar datos del estado '{estado_nombre}'.")
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
                        if user_state and estado_obj != user_state:
                            errors.append(f"Fila {row_idx}: No tiene permisos para modificar datos del estado '{estado_nombre}'.")
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

    user_state = get_user_state(request)
    
    if user_state:
        estados_list = [user_state]
        titulares_list = Titular.objects.filter(estado=user_state).order_by('nombre')
    else:
        estados_list = Estado.objects.all().order_by('nombre')
        titulares_list = Titular.objects.all().order_by('nombre')

    update_dates = get_all_update_dates()
    return render(request, 'mapa/carga_datos.html', {
        'models': models_available.keys(),
        'update_dates': update_dates,
        'estados_list': Estado.objects.all().order_by('nombre'),
    })

def titulares_list(request):
    """Vista para la gestión independiente de expedientes de titulares."""
    if not request.user.is_authenticated:
        return redirect('/log-in/?next=%s' % request.path)
    user_state = get_user_state(request)
    
    if user_state:
        estados_list = [user_state]
        titulares_list = Titular.objects.filter(estado=user_state).order_by('estado__nombre', 'nombre')
    else:
        estados_list = Estado.objects.all().order_by('nombre')
        titulares_list = Titular.objects.all().order_by('estado__nombre', 'nombre')

    return render(request, 'mapa/titulares.html', {
        'estados_list': estados_list,
        'nacionalidades_list': Nacionalidad.objects.all().order_by('nombre'),
        'grados_academicos': GradoAcademico.objects.all().order_by('nombre'),
        'tipos_nombramiento': TipoNombramiento.objects.all().order_by('nombre'),
        'procedencias_list': TipoProcendencia.objects.all().order_by('institucion'),
        'titulares_list': titulares_list,
    })

def api_get_titular(request, titular_id):
    """Retorna los datos de un titular en formato JSON para edición."""
    try:
        user_state = get_user_state(request)
        titular = Titular.objects.get(id=titular_id)
        
        # Validación de seguridad
        if user_state and titular.estado != user_state:
            return JsonResponse({'status': 'error', 'message': 'Sin permisos'}, status=403)
            
        data = {
            'id': titular.id,
            'nombre': titular.nombre,
            'apellido_paterno': titular.apellido_paterno,
            'apellido_materno': titular.apellido_materno,
            'curp': titular.curp,
            'fecha_nacimiento': titular.fecha_nacimiento.isoformat() if titular.fecha_nacimiento else None,
            'sexo': titular.sexo,
            'nivel': titular.nivel,
            'codigo_plaza': titular.codigo_plaza,
            'tipo_nombramiento': titular.tipo_nombramiento.nombre if titular.tipo_nombramiento else None,
            'tipo_nombramiento_id': titular.tipo_nombramiento_id,
            'procedencia': titular.procedencia.institucion if titular.procedencia else None,
            'procedencia_id': titular.procedencia_id,
            'estado': titular.estado.nombre,
            'estado_id': titular.estado_id,
            'nacionalidad_id': titular.nacionalidad_id,
            'foto_url': titular.fotografia.url if titular.fotografia else None,
            'telefonos': list(titular.telefonos.values('tipo', 'numero')),
            'correos': list(titular.correos.values('tipo', 'correo')),
            'estudios': [
                {
                    'grado': e.grado.nombre if e.grado else 'Sin grado',
                    'grado_id': e.grado_id,
                    'carrera': e.carrera
                } for e in titular.estudios.all()
            ],
            'trayectoria': list(titular.trayectoria.values('puesto', 'area', 'fecha_inicio', 'fecha_fin', 'actual')),
            'experiencia': list(titular.experiencia_externa.values('institucion', 'cargo', 'fecha_inicio', 'fecha_fin', 'descripcion')),
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@transaction.atomic
def eliminar_titular(request, titular_id):
    """Elimina un titular y todos sus datos relacionados."""
    try:
        user_state = get_user_state(request)
        titular = Titular.objects.get(id=titular_id)
        
        # Validación de seguridad
        if user_state and titular.estado != user_state:
            messages.error(request, "No tienes permisos para eliminar este registro.")
            return redirect('titulares_list')
            
        nombre = titular.nombre
        titular.delete()
        messages.success(request, f"Expediente de {nombre} eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar titular: {str(e)}")
    
    return redirect('titulares_list')


def personal_list(request):
    """Vista para la gestión independiente del Personal INM con paginación y filtros en el servidor."""
    if not request.user.is_authenticated:
        return redirect('/log-in/?next=%s' % request.path)
    user_state = get_user_state(request)
    
    # 1. Obtener filtros de la solicitud GET
    nombre_query = request.GET.get('nombre', '').strip()
    estado_id_query = request.GET.get('estado_id', '').strip()
    puesto_query = request.GET.get('puesto', '').strip()
    page_number = request.GET.get('page', 1)
    
    # 2. Filtrar queryset de personal
    personal_qs = PersonalINM.objects.all().select_related('estado', 'lugar_asignado')
    
    if user_state:
        personal_qs = personal_qs.filter(estado=user_state)
        estados_list_all = [user_state]
    else:
        estados_list_all = Estado.objects.all().order_by('nombre')
        if estado_id_query:
            personal_qs = personal_qs.filter(estado_id=estado_id_query)
            
    if nombre_query:
        from django.db.models import Q
        personal_qs = personal_qs.filter(
            Q(nombre__icontains=nombre_query) | 
            Q(apellido__icontains=nombre_query) | 
            Q(num_empleado__icontains=nombre_query) |
            Q(codigo_plaza__icontains=nombre_query)
        )
        
    if puesto_query:
        personal_qs = personal_qs.filter(puesto_especifico__icontains=puesto_query)
        
    personal_qs = personal_qs.order_by('estado__nombre', 'nombre')
    total_matched = personal_qs.count()
    
    # 3. Paginación de resultados (50 por página)
    from django.core.paginator import Paginator
    paginator = Paginator(personal_qs, 50)
    page_obj = paginator.get_page(page_number)
    
    # 4. Listados para formularios de creación/edición
    if user_state:
        estados_list = [user_state]
        inmuebles_list = Inmueble.objects.filter(estado=user_state).order_by('nombre_inmueble')
    else:
        estados_list = Estado.objects.all().order_by('nombre')
        inmuebles_list = Inmueble.objects.all().order_by('nombre_inmueble')
        
    return render(request, 'mapa/personal_list.html', {
        'estados_list': estados_list,
        'estados_list_all': estados_list_all,
        'actividades_list': TipoDependencia.objects.all().order_by('nombre'),
        'inmuebles_list': inmuebles_list,
        'personal_list': page_obj,
        'total_matched': total_matched,
        'nombre_query': nombre_query,
        'estado_id_query': estado_id_query,
        'puesto_query': puesto_query,
        'estatus_list': EstatusPersonal.objects.all().order_by('estatus'),
        'tipo_plaza_list': TipoPlaza.objects.all().order_by('plazaT'),
    })


def api_get_personal(request, personal_id):
    """Retorna los datos de un personal en formato JSON para edición."""
    try:
        user_state = get_user_state(request)
        personal = PersonalINM.objects.get(id=personal_id)
        
        # Validación de seguridad
        if user_state and personal.estado != user_state:
            return JsonResponse({'status': 'error', 'message': 'Sin permisos'}, status=403)
            
        data = {
            'id': personal.id,
            'estado_id': personal.estado_id,
            'estatus_id': personal.estatus_id or '',
            'tipo_plaza_id': personal.tipo_plaza_id or '',
            'codigo_plaza': personal.codigo_plaza,
            'nivel': personal.nivel,
            'num_empleado': personal.num_empleado or '',
            'nombre': personal.nombre or '',
            'apellido': personal.apellido or '',
            'curp': personal.curp or '',
            'fecha_nacimiento': personal.fecha_nacimiento.isoformat() if personal.fecha_nacimiento else '',
            'sexo': personal.sexo or '',
            'tipo_movimiento': personal.tipo_movimiento,
            'fecha_ingreso_inm': personal.fecha_ingreso_inm.isoformat() if personal.fecha_ingreso_inm else None,
            'fecha_ingreso_plaza': personal.fecha_ingreso_plaza.isoformat() if personal.fecha_ingreso_plaza else None,
            'vig_inicio_mov': personal.vig_inicio_mov.isoformat() if personal.vig_inicio_mov else None,
            'vig_termino_mov': personal.vig_termino_mov.isoformat() if personal.vig_termino_mov else None,
            'puesto_especifico': personal.puesto_especifico,
            'sueldo_bruto': personal.sueldo_bruto,
            'sueldo_neto': personal.sueldo_neto,
            'actividad_ids': list(personal.actividad.values_list('id', flat=True)),
            'jefe_oficina': personal.jefe_oficina,
            'lugar_asignado_id': personal.lugar_asignado_id or '',
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@transaction.atomic
def eliminar_personal(request, personal_id):
    """Elimina un registro de personal."""
    try:
        user_state = get_user_state(request)
        personal = PersonalINM.objects.get(id=personal_id)
        
        # Validación de seguridad
        if user_state and personal.estado != user_state:
            messages.error(request, "No tienes permisos para eliminar este registro.")
            return redirect('personal_list')
            
        nombre = f"{personal.nombre or ''} {personal.apellido or ''}"
        personal.delete()
        messages.success(request, f"Registro de {nombre} eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar registro: {str(e)}")
    
    return redirect('personal_list')


@transaction.atomic
def guardar_personal(request):
    if request.method != 'POST':
        return redirect('personal_list')
    
    user_state = get_user_state(request)
    
    try:
        personal_id = request.POST.get('personal_id')
        estado_id = request.POST.get('estado_id')
        
        # Validación de seguridad: el estado enviado debe coincidir con el del usuario
        if user_state and str(user_state.id) != str(estado_id):
            raise PermissionError("No tienes permisos para registrar personal en este estado.")

        # Parsear floats y fechas opcionales
        sueldo_bruto = request.POST.get('sueldo_bruto') or None
        if sueldo_bruto:
            sueldo_bruto = float(sueldo_bruto)
            
        sueldo_neto = request.POST.get('sueldo_neto') or None
        if sueldo_neto:
            sueldo_neto = float(sueldo_neto)

        curp = request.POST.get('curp', '').strip().upper() or None
        fecha_nacimiento = request.POST.get('fecha_nacimiento') or None
        sexo = request.POST.get('sexo') or None
        
        # Derivar fecha_nacimiento y sexo si hay CURP pero no se enviaron
        if curp and (not fecha_nacimiento or not sexo):
            derived_dob, derived_sex = parse_curp_details(curp)
            if not fecha_nacimiento:
                fecha_nacimiento = derived_dob
            if not sexo:
                sexo = derived_sex

        defaults = {
            'estado_id': estado_id,
            'estatus_id': request.POST.get('estatus_id') or None,
            'tipo_plaza_id': request.POST.get('tipo_plaza_id') or None,
            'codigo_plaza': request.POST.get('codigo_plaza', '').strip().upper(),
            'nivel': request.POST.get('nivel', '').strip().upper(),
            'num_empleado': request.POST.get('num_empleado', '').strip().upper() or None,
            'nombre': normalizar_nombre(request.POST.get('nombre', '')),
            'apellido': normalizar_nombre(request.POST.get('apellido', '')),
            'curp': curp,
            'fecha_nacimiento': fecha_nacimiento,
            'sexo': sexo,
            'tipo_movimiento': request.POST.get('tipo_movimiento') == 'on',
            'fecha_ingreso_inm': request.POST.get('fecha_ingreso_inm') or None,
            'fecha_ingreso_plaza': request.POST.get('fecha_ingreso_plaza') or None,
            'vig_inicio_mov': request.POST.get('vig_inicio_mov') or None,
            'vig_termino_mov': request.POST.get('vig_termino_mov') or None,
            'puesto_especifico': normalizar_nombre(request.POST.get('puesto_especifico', '')),
            'sueldo_bruto': sueldo_bruto,
            'sueldo_neto': sueldo_neto,
            'jefe_oficina': request.POST.get('jefe_oficina') == 'on',
            'lugar_asignado_id': request.POST.get('lugar_asignado_id') or None,
        }

        actividad_ids = request.POST.getlist('actividad_ids[]')
        # También aceptar actividad_ids como campo único separado por comas (fallback)
        if not actividad_ids:
            raw = request.POST.get('actividad_ids', '')
            actividad_ids = [v.strip() for v in raw.split(',') if v.strip()]

        if personal_id:
            personal = PersonalINM.objects.get(id=personal_id)
            if user_state and personal.estado != user_state:
                raise PermissionError("No tienes permisos para modificar este registro.")
            for key, val in defaults.items():
                setattr(personal, key, val)
            personal.save()
            personal.actividad.set(actividad_ids)
            messages.success(request, "Registro de personal actualizado correctamente.")
        else:
            personal = PersonalINM.objects.create(**defaults)
            personal.actividad.set(actividad_ids)
            messages.success(request, "Nuevo personal registrado correctamente.")
            
    except Exception as e:
        messages.error(request, f"Error al guardar personal: {str(e)}")
        
    return redirect('personal_list')


@transaction.atomic
def carga_rapida_personal(request):
    if request.method != 'POST':
        return redirect('personal_list')
        
    user_state = get_user_state(request)
    
    # Check if request is JSON (AJAX chunks)
    is_json = False
    if request.content_type == 'application/json':
        try:
            import json
            payload = json.loads(request.body)
            is_json = payload.get('is_ajax_chunk', False)
        except Exception:
            is_json = False
            
    try:
        if is_json:
            headers = payload.get('headers', [])
            rows_data = payload.get('rows', [])
        else:
            excel_file = request.FILES.get('excel_file')
            if not excel_file:
                messages.error(request, "No se ha proporcionado ningún archivo.")
                return redirect('personal_list')
                
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                messages.error(request, "El archivo debe ser un Excel (.xlsx o .xls).")
                return redirect('personal_list')
                
            wb = openpyxl.load_workbook(excel_file, data_only=True)
            sheet = wb.active
            
            # Encontrar la fila de encabezados. Buscaremos la primera fila que contenga 'STATUS' o 'CODIGO-PLAZA'
            headers = []
            header_row_idx = None
            
            for r in range(1, 21):
                row_vals = [str(cell.value or '').strip().upper() for cell in sheet[r]]
                if 'STATUS' in row_vals or 'CODIGO-PLAZA\nNUEVO' in row_vals or 'CODIGO-PLAZA NUEVO' in row_vals or 'CODIGO-PLAZA' in row_vals:
                    headers = [str(cell.value or '').strip() for cell in sheet[r]]
                    header_row_idx = r
                    break
                    
            if not header_row_idx:
                header_row_idx = 8
                headers = [str(cell.value or '').strip() for cell in sheet[8]]
                
            rows_data = []
            for r in range(header_row_idx + 1, sheet.max_row + 1):
                row_cells = list(sheet[r])
                if not any(cell.value for cell in row_cells):
                    continue
                row_vals = [cell.value for cell in row_cells]
                rows_data.append(row_vals)

        # Normalizar nombres de columnas a claves consistentes
        col_mapping = {}
        for idx, h in enumerate(headers):
            h_norm = normalizar_nombre(h).replace('\n', ' ').strip()
            if 'STATUS' in h_norm:
                col_mapping['status'] = idx
                # print(f"status {idx}")
            elif 'TIPO DE PLAZA' in h_norm:
                col_mapping['tipo_plaza'] = idx
            elif 'ADSCRIPCION' in h_norm or 'ESTADO' in h_norm:
                col_mapping['adscripcion'] = idx
            elif 'CODIGO' in h_norm:
                col_mapping['codigo_plaza'] = idx
                # print(f"codigo_plaza {idx}")
            elif 'NIVEL' in h_norm:
                col_mapping['nivel'] = idx
            elif 'NUM EMP' in h_norm or 'NUM_EMP' in h_norm or 'EMPLEADO' in h_norm:
                col_mapping['num_empleado'] = idx
            elif 'CURP' in h_norm:
                col_mapping['curp'] = idx
            elif 'NOMBRE' in h_norm:
                col_mapping['nombre'] = idx
            elif 'MOVIMIENTO' in h_norm:
                col_mapping['tipo_movimiento'] = idx
            elif 'FECHA DE ING. INM' in h_norm or 'FECHA ING INM' in h_norm or 'ING. INM' in h_norm:
                col_mapping['fecha_ingreso_inm'] = idx
                # print(f"fecha_ingreso_inm {idx}")
            elif 'FECHA DE ING A LA PLAZA' in h_norm or 'FECHA ING PLAZA' in h_norm or 'ING A LA PLAZA' in h_norm or 'FECHA_INGRESO_PLAZA' in h_norm or 'FECHA INGRESO PLAZA' in h_norm:
                col_mapping['fecha_ingreso_plaza'] = idx
                # print(f"fecha_ingreso_plaza {idx}")
            elif 'VIG. DE INICIO' in h_norm or 'INICIO MOV' in h_norm:
                col_mapping['vig_inicio_mov'] = idx
                # print(f"vig_inicio_mov {idx}")
            elif 'VIG. DE TERMINO' in h_norm or 'TERMINO MOV' in h_norm:
                col_mapping['vig_termino_mov'] = idx
                # print(f"vig_termino_mov {idx}")
            elif 'PUESTO' in h_norm:
                col_mapping['puesto_especifico'] = idx
            elif 'SUELDO BRUTO' in h_norm:
                col_mapping['sueldo_bruto'] = idx
            elif 'SUELDO NETO' in h_norm:
                col_mapping['sueldo_neto'] = idx
            elif 'JEFE' in h_norm:
                col_mapping['jefe_oficina'] = idx
            elif 'LUGAR' in h_norm or 'INMUEBLE' in h_norm or 'UBICACION' in h_norm or 'ASIGNADO' in h_norm:
                col_mapping['lugar_asignado'] = idx
                
        if 'codigo_plaza' not in col_mapping:
            if is_json:
                from django.http import JsonResponse
                return JsonResponse({'status': 'error', 'message': 'No se encontró la columna de Código de Plaza en el Excel.'}, status=400)
            messages.error(request, "No se encontró la columna de Código de Plaza en el Excel.")
            return redirect('personal_list')
            
        # Helpers para limpiar y parsear datos de celda
        def parse_str(val):
            if val is None: return None
            val_s = str(val).strip()
            if val_s in ('...', '..', '-', '', 'None'): return None
            return val_s
            
        def parse_date(val):
            if not val: return None
            if isinstance(val, (datetime, date)):
                return val if isinstance(val, date) else val.date()
            val_s = str(val).strip()
            if val_s in ('...', '..', '-', '', 'None'): return None
            if 'T' in val_s:
                val_s = val_s.split('T')[0]
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
                try:
                    return datetime.strptime(val_s, fmt).date()
                except ValueError:
                    continue
            return None
            
        def parse_float(val):
            if val is None: return None
            val_s = str(val).strip()
            if val_s in ('...', '..', '-', '', 'None'): return None
            try:
                return float(val_s)
            except ValueError:
                return None

        # Pre-cargar Estados para optimizar
        estados_dict = {normalizar_nombre(e.nombre): e for e in Estado.objects.all()}
        
        def find_estado(adscripcion_val):
            if not adscripcion_val: return None
            clean = adscripcion_val.strip().upper()
            for prefix in ["O.R. ", "O.R.", "OR.", "OR "]:
                if clean.startswith(prefix):
                    clean = clean[len(prefix):].strip()
            if clean in ("DISTRITO FEDERAL", "DF"):
                clean = "CIUDAD DE MEXICO"
            clean_norm = normalizar_nombre(clean)
            if clean_norm in estados_dict:
                return estados_dict[clean_norm]
            for est_norm, est in estados_dict.items():
                if est_norm in clean_norm or clean_norm in est_norm:
                    return est
            return None

        # Pre-cargar Estatus y Plazas para optimizar y validar
        estatus_dict = {normalizar_nombre(ep.estatus): ep for ep in EstatusPersonal.objects.all()}
        plazas_dict = {normalizar_nombre(tp.plazaT): tp for tp in TipoPlaza.objects.all()}
        
        lineas_estatus_incorrectas = []
        lineas_plaza_incorrectas = []

        creados = 0
        actualizados = 0
        omitidos = 0
        
        for idx_row, row_vals in enumerate(rows_data):
            
            def get_cell_val(key):
                if key in col_mapping:
                    idx = col_mapping[key]
                    if idx < len(row_vals):
                        return row_vals[idx]
                return None
                
            codigo_plaza = parse_str(get_cell_val('codigo_plaza'))
            if not codigo_plaza:
                continue
                
            codigo_plaza = codigo_plaza.upper()
            
            adscripcion = parse_str(get_cell_val('adscripcion'))
            row_estado = find_estado(adscripcion)
            
            if user_state:
                if row_estado and row_estado != user_state:
                    omitidos += 1
                    continue
                row_estado = user_state
            
            if not row_estado:
                omitidos += 1
                continue
                
            # Estatus matching database EstatusPersonal
            estatus_val = None
            estatus_raw = parse_str(get_cell_val('status'))
            if estatus_raw:
                estatus_norm = normalizar_nombre(estatus_raw)
                if estatus_norm in estatus_dict:
                    estatus_val = estatus_dict[estatus_norm]
                else:
                    sheet_row_num = (header_row_idx + 1 + idx_row) if not is_json else (idx_row + 2)
                    lineas_estatus_incorrectas.append(sheet_row_num)
                    
            # Tipo Plaza matching database TipoPlaza
            tipo_plaza_val = None
            tipo_plaza_raw = parse_str(get_cell_val('tipo_plaza'))
            if tipo_plaza_raw:
                tipo_plaza_norm = normalizar_nombre(tipo_plaza_raw)
                if tipo_plaza_norm in plazas_dict:
                    tipo_plaza_val = plazas_dict[tipo_plaza_norm]
                else:
                    sheet_row_num = (header_row_idx + 1 + idx_row) if not is_json else (idx_row + 2)
                    lineas_plaza_incorrectas.append(sheet_row_num)
                
            nivel = parse_str(get_cell_val('nivel')) or 'N/A'
            nivel = nivel.upper()
            
            puesto_especifico = parse_str(get_cell_val('puesto_especifico')) or 'SIN PUESTO'
            puesto_especifico = normalizar_nombre(puesto_especifico)
            
            sueldo_bruto = parse_float(get_cell_val('sueldo_bruto'))
            sueldo_neto = parse_float(get_cell_val('sueldo_neto'))
            
            num_empleado = None
            nombre = None
            apellido = None
            curp = None
            fecha_nacimiento = None
            sexo = None
            tipo_movimiento = None
            fecha_ingreso_inm = None
            fecha_ingreso_plaza = None
            vig_inicio_mov = None
            vig_termino_mov = None
            
            is_vacant = (estatus_val and estatus_val.estatus.strip().upper() == 'VACANTE')
            if not is_vacant:
                num_empleado = parse_str(get_cell_val('num_empleado'))
                
                full_name = parse_str(get_cell_val('nombre'))
                if full_name:
                    parts = full_name.split()
                    if len(parts) >= 3:
                        apellido = " ".join(parts[:2])
                        nombre = " ".join(parts[2:])
                    elif len(parts) == 2:
                        apellido = parts[0]
                        nombre = parts[1]
                    else:
                        nombre = full_name
                        apellido = ""
                    nombre = normalizar_nombre(nombre)
                    apellido = normalizar_nombre(apellido)
                
                curp = parse_str(get_cell_val('curp'))
                if curp:
                    curp = curp.strip().upper()
                    fecha_nacimiento, sexo = parse_curp_details(curp)

                mov_raw = parse_str(get_cell_val('tipo_movimiento'))
                if mov_raw:
                    mov_norm = mov_raw.strip().upper()
                    if mov_norm == 'DEFINITIVO':
                        tipo_movimiento = True
                    elif mov_norm == 'INTERINO':
                        tipo_movimiento = False
                    else:
                        tipo_movimiento = None
                else:
                    tipo_movimiento = None
                    
                fecha_ingreso_inm = parse_date(get_cell_val('fecha_ingreso_inm'))
                fecha_ingreso_plaza = parse_date(get_cell_val('fecha_ingreso_plaza'))
                vig_inicio_mov = parse_date(get_cell_val('vig_inicio_mov'))
                vig_termino_mov = parse_date(get_cell_val('vig_termino_mov'))
                
            # jefe_oficina se mantiene siempre en False por solicitud del usuario
            jefe_oficina = False
            
            # lugar_asignado (Inmueble) se mantiene siempre en None (blank) por solicitud del usuario
            lugar_asignado = None

            defaults = {
                'estado': row_estado,
                'estatus': estatus_val,
                'tipo_plaza': tipo_plaza_val,
                'nivel': nivel,
                'num_empleado': num_empleado,
                'nombre': nombre,
                'apellido': apellido,
                'curp': curp,
                'fecha_nacimiento': fecha_nacimiento,
                'sexo': sexo,
                'tipo_movimiento': tipo_movimiento,
                'fecha_ingreso_inm': fecha_ingreso_inm,
                'fecha_ingreso_plaza': fecha_ingreso_plaza,
                'vig_inicio_mov': vig_inicio_mov,
                'vig_termino_mov': vig_termino_mov,
                'puesto_especifico': puesto_especifico,
                'sueldo_bruto': sueldo_bruto,
                'sueldo_neto': sueldo_neto,
                'jefe_oficina': jefe_oficina,
                'lugar_asignado': lugar_asignado,
            }
            
            personal_obj, created = PersonalINM.objects.update_or_create(
                codigo_plaza=codigo_plaza,
                defaults=defaults
            )
            
            if created:
                creados += 1
            else:
                actualizados += 1
                
        if is_json:
            from django.http import JsonResponse
            return JsonResponse({
                'status': 'success',
                'creados': creados,
                'actualizados': actualizados,
                'omitidos': omitidos,
                'lineas_estatus_incorrectas': lineas_estatus_incorrectas,
                'lineas_plaza_incorrectas': lineas_plaza_incorrectas,
            })
            
        msg = f"Carga rápida completada: {creados} creados, {actualizados} actualizados, {omitidos} omitidos."
        messages.success(request, msg)
        if lineas_estatus_incorrectas:
            messages.warning(request, f"Líneas con Estatus incorrecto (se guardaron como NULL): {', '.join(map(str, lineas_estatus_incorrectas))}")
        if lineas_plaza_incorrectas:
            messages.warning(request, f"Líneas con Tipo de Plaza incorrecto (se guardaron como NULL): {', '.join(map(str, lineas_plaza_incorrectas))}")
            
    except Exception as e:
        if is_json:
            from django.http import JsonResponse
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        messages.error(request, f"Error al procesar el archivo Excel: {str(e)}")
        
    return redirect('personal_list')


@transaction.atomic
def guardar_titular(request):
    if request.method != 'POST':
        return redirect('carga_datos')
    
    user_state = get_user_state(request)
    
    try:
        curp = request.POST.get('curp', '').strip().upper()
        if not curp:
            raise ValueError("La CURP es obligatoria.")
        
        # Validación de seguridad: el estado enviado debe coincidir con el del usuario
        estado_id = request.POST.get('estado_id')
        if user_state and str(user_state.id) != str(estado_id):
            raise PermissionError("No tienes permisos para registrar titulares en este estado.")

        titular, created = Titular.objects.update_or_create(
            curp=curp,
            defaults={
                'nombre': normalizar_nombre(request.POST.get('nombre', '')),
                'apellido_paterno': normalizar_nombre(request.POST.get('apellido_paterno', '')),
                'apellido_materno': normalizar_nombre(request.POST.get('apellido_materno', '')),
                'fecha_nacimiento': request.POST.get('fecha_nacimiento'),
                'sexo': request.POST.get('sexo'),
                'nivel': request.POST.get('nivel', '').strip().upper(),
                'codigo_plaza': request.POST.get('codigo_plaza', '').strip().upper() or None,
                'tipo_nombramiento_id': request.POST.get('tipo_nombramiento_id') or None,
                'procedencia_id': request.POST.get('procedencia_id') or None,
                'estado_id': request.POST.get('estado_id'),
                'nacionalidad_id': request.POST.get('nacionalidad_id') or None,
            }
        )

        if 'fotografia' in request.FILES:
            titular.fotografia = request.FILES['fotografia']
            titular.save()
        
        # Procesar imagen recortada (Base64)
        cropped_data = request.POST.get('cropped_image')
        if cropped_data and ';base64,' in cropped_data:
            format, imgstr = cropped_data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f"titular_{titular.curp}.{ext}")
            titular.fotografia = data
            titular.save()

        # 2. Teléfonos
        tels_tipo = request.POST.getlist('tel_tipo[]')
        tels_num = request.POST.getlist('tel_numero[]')
        TelefonoTitular.objects.filter(titular=titular).delete()
        for t, n in zip(tels_tipo, tels_num):
            if n.strip():
                TelefonoTitular.objects.create(titular=titular, tipo=t, numero=n.strip())

        # 3. Correos
        emails_tipo = request.POST.getlist('email_tipo[]')
        emails_val = request.POST.getlist('email_valor[]')
        CorreoTitular.objects.filter(titular=titular).delete()
        for t, v in zip(emails_tipo, emails_val):
            if v.strip():
                CorreoTitular.objects.create(titular=titular, tipo=t, correo=v.strip())

        # 4. Estudios
        edu_grados = request.POST.getlist('edu_grado[]')
        edu_carreras = request.POST.getlist('edu_carrera[]')
        Estudio.objects.filter(titular=titular).delete()
        for g, c in zip(edu_grados, edu_carreras):
            if c.strip():
                Estudio.objects.create(titular=titular, grado_id=g, carrera=normalizar_nombre(c))

        # 5. Trayectoria Institucional (INM)
        tray_puestos = request.POST.getlist('tray_puesto[]')
        tray_areas = request.POST.getlist('tray_area[]')
        tray_inicios = request.POST.getlist('tray_inicio[]')
        tray_fins = request.POST.getlist('tray_fin[]')
        tray_actual_idx = request.POST.get('tray_actual_index')
        
        TrayectoriaLaboral.objects.filter(titular=titular).delete()
        for idx, (p, a, i, f) in enumerate(zip(tray_puestos, tray_areas, tray_inicios, tray_fins)):
            if p.strip() and a.strip() and i:
                is_actual = str(idx) == tray_actual_idx
                TrayectoriaLaboral.objects.create(
                    titular=titular, 
                    puesto=normalizar_nombre(p), 
                    area=normalizar_nombre(a), 
                    fecha_inicio=i,
                    fecha_fin=f if f else None,
                    actual=is_actual
                )

        # 6. Experiencia Profesional Previa
        exp_insts = request.POST.getlist('exp_inst[]')
        exp_cargos = request.POST.getlist('exp_cargo[]')
        exp_inicios = request.POST.getlist('exp_inicio[]')
        exp_fins = request.POST.getlist('exp_fin[]')
        exp_descs = request.POST.getlist('exp_desc[]')
        ExperienciaProfesional.objects.filter(titular=titular).delete()
        for inst, cargo, ini, fin, desc in zip(exp_insts, exp_cargos, exp_inicios, exp_fins, exp_descs):
            if inst.strip() and cargo.strip() and ini:
                ExperienciaProfesional.objects.create(
                    titular=titular,
                    institucion=normalizar_nombre(inst),
                    cargo=normalizar_nombre(cargo),
                    fecha_inicio=ini,
                    fecha_fin=fin if fin else None,
                    descripcion=desc.strip()
                )

        messages.success(request, f"Expediente de {titular.nombre} {'creado' if created else 'actualizado'} correctamente.")
    except Exception as e:
        messages.error(request, f"Error al guardar expediente: {str(e)}")
    
    return redirect('titulares_list')

def api_periodo_custom(request):
    """API para obtener datos en un rango de fechas personalizado."""
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Acceso denegado'}, status=403)

    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()

        # Restricciones de Rango
        MIN_DATE = date(2024, 10, 1)
        MAX_DATE = get_global_update_date() or date.today()

        if start_date < MIN_DATE:
            start_date = MIN_DATE
        if end_date > MAX_DATE:
            end_date = MAX_DATE
        if start_date > end_date:
            start_date = end_date

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
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)
        
    user_state = get_user_state(request)
    if not request.user.is_superuser and not user_state:
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
                        if user_state and estado_obj != user_state:
                            errors.append(f"Reg {row_idx}: No tiene permisos para modificar datos del estado '{estado_nombre}'.")
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
                        if user_state and estado_obj != user_state:
                            errors.append(f"Reg {row_idx}: No tiene permisos para modificar datos del estado '{estado_nombre}'.")
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
    if not request.user.is_authenticated:
        return redirect('/log-in/?next=%s' % request.path)
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

def mapa_ejemplo(request):
    """Vista de ejemplo para MapLibre GL JS."""
    return render(request, 'mapa/mapa_ejemplo.html')


# -------------------------------------------------------
# --- -------  --- VIEW MAPA DR --- ------ ------- ------
# -------------------------------------------------------

def mapa_interactivo(request):
    if not request.user.is_authenticated:
        return redirect('/log-in/?next=%s' % request.path)
    
    user_state = get_user_state(request)
    if not request.user.is_superuser and not user_state:
        return render(request, 'base/error404.html')

    fecha_act = get_global_update_date() or date.today()

    # No database queries for periods to avoid delays
    totals_cs = {}
    totals_dt = {}
    
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    api_instrucciones = {}
    try:
        api_res = requests.get('https://172.16.16.167/api/mapa-datos/', verify=False, timeout=2.5)
        if api_res.status_code == 200:
            api_instrucciones = api_res.json()
    except Exception as e:
        print(f"Error al obtener instrucciones de la API: {str(e)}")
    
    instrucciones_avance = {}
    instrucciones_totales_dict = {}
    instrucciones_color_rank = {}

    LABEL_NACIONAL = "Total Nacional"

    METRIC_LABELS = {
        'todos': 'Todos'
    }

    # --- Recopilación de Infraestructura y Titulares ---
    infra_raw = PuntosInternacionEstacion.objects.values('estado__nombre', 'tipo').annotate(total=Count('id'))
    titulares_raw = Titular.objects.all().select_related('estado', 'tipo_nombramiento')
    
    infra_data = {}
    # Estructura base para todos los estados
    for edo in Estado.objects.all():
        infra_data[normalizar_nombre(edo.nombre)] = {
            'estado_id': edo.id,
            'AEREO': 0, 'MARITIMO': 0, 'TERRESTRE': 0, 'ESTACION': 0,
            'PRH': 0,
            'personal_total': 0,
            'personal_activo': 0,
            'personal_vacante': 0,
            'subrep_federal': 0,
            'subrep_local': 0,
            'rep_local': 0,
            'titular': 'Sin titular asignado',
            'titular_id': None,
            'foto': None,
            'tipo_nombramiento': None
        }
    
    for item in infra_raw:
        edo_name = normalizar_nombre(item['estado__nombre'])
        if edo_name in infra_data:
            infra_data[edo_name][item['tipo']] = item['total']
            
    for t in titulares_raw:
        edo_name = normalizar_nombre(t.estado.nombre)
        if edo_name in infra_data:
            infra_data[edo_name]['titular'] = f"{t.nombre} {t.apellido_paterno} {t.apellido_materno}"
            infra_data[edo_name]['titular_id'] = t.id
            infra_data[edo_name]['tipo_nombramiento'] = t.tipo_nombramiento.nombre if t.tipo_nombramiento else None
            if t.fotografia:
                infra_data[edo_name]['foto'] = t.fotografia.url

    # PRHs por estado
    prh_raw = PRHs.objects.values('estado__nombre').annotate(total=Count('id'))
    for item in prh_raw:
        edo_name = normalizar_nombre(item['estado__nombre'])
        if edo_name in infra_data:
            infra_data[edo_name]['PRH'] = item['total']

    # Personal por estado
    personal_qs = PersonalINM.objects.all().select_related('estado', 'estatus', 'tipo_plaza')
    for p in personal_qs:
        if not p.estado:
            continue
        
        tipo_plaza = (p.tipo_plaza.plazaT if p.tipo_plaza else '').upper()
        if tipo_plaza not in ['BASE', 'CONFIANZA']:
            continue

        edo_name = normalizar_nombre(p.estado.nombre)
        if edo_name in infra_data:
            infra_data[edo_name]['personal_total'] += 1
            estatus_name = (p.estatus.estatus if p.estatus else '').upper()
            if estatus_name == 'ACTIVO':
                infra_data[edo_name]['personal_activo'] += 1
            elif estatus_name == 'VACANTE':
                infra_data[edo_name]['personal_vacante'] += 1
            
            puesto_clean = normalizar_nombre(p.puesto_especifico)
            if 'SUB REPRESENTACION FEDERAL' in puesto_clean:
                infra_data[edo_name]['subrep_federal'] += 1
            elif 'SUB REPRESENTACION LOCAL' in puesto_clean:
                infra_data[edo_name]['subrep_local'] += 1
            elif 'REPRESENTACION LOCAL' in puesto_clean:
                infra_data[edo_name]['rep_local'] += 1

    # Totales Nacionales
    subrep_federal_nat = 0
    subrep_local_nat = 0
    rep_local_nat = 0
    for key, val in infra_data.items():
        subrep_federal_nat += val.get('subrep_federal', 0)
        subrep_local_nat += val.get('subrep_local', 0)
        rep_local_nat += val.get('rep_local', 0)

    infra_data[LABEL_NACIONAL] = {
        'estado_id': None,
        'AEREO': PuntosInternacionEstacion.objects.filter(tipo='AEREO').count(),
        'MARITIMO': PuntosInternacionEstacion.objects.filter(tipo='MARITIMO').count(),
        'TERRESTRE': PuntosInternacionEstacion.objects.filter(tipo='TERRESTRE').count(),
        'ESTACION': PuntosInternacionEstacion.objects.filter(tipo='ESTACION').count(),
        'PRH': PRHs.objects.count(),
        'personal_total': PersonalINM.objects.count(),
        'personal_activo': PersonalINM.objects.filter(estatus__estatus__iexact='ACTIVO').count(),
        'personal_vacante': PersonalINM.objects.filter(estatus__estatus__iexact='VACANTE').count(),
        'subrep_federal': subrep_federal_nat,
        'subrep_local': subrep_local_nat,
        'rep_local': rep_local_nat,
        'titular': 'Datos Nacionales',
        'foto': None,
        'tipo_nombramiento': None
    }

    # Valores por defecto para estados sin datos
    default_vals = {
        'todos': 0, 'color_t': 32
    }

    # Ruta al archivo geojson descargado
    geojson_path = os.path.join(settings.BASE_DIR, 'mapa', 'static', 'mapa', 'data', 'inegi_latlon_mexico.geojson')
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geo_data = json.load(f)

    # Filtrar el GeoJSON por estado si el usuario no es superusuario
    if user_state:
        user_state_name_normalized = normalizar_nombre(user_state.nombre)
        geo_data['features'] = [
            f for f in geo_data['features']
            if normalizar_nombre(f['properties']['name']) == user_state_name_normalized
        ]
        
    for feature in geo_data['features']:
        name_normalized = normalizar_nombre(feature['properties']['name'])
        cs = default_vals.copy()
        dt = default_vals.copy()
        
        for k in default_vals:
            feature['properties'][f'cs_{k}'] = cs[k]
            feature['properties'][f'dt_{k}'] = dt[k]
            feature['properties'][f'pe_{k}'] = cs[k]
        
        feature['properties']['cs_str_todos'] = '0'
        feature['properties']['dt_str_todos'] = '0'
        feature['properties']['pe_str_todos'] = '0'
        
    # --- Capa de Infraestructura (Iconos SVG) ---
    infra_points_objs = PuntosInternacionEstacion.objects.all()
    if user_state:
        infra_points_objs = infra_points_objs.filter(estado=user_state)
    infra_pts_data = []
    for pt in infra_points_objs:
        icon_file = 'terrestre2.svg' # Default
        if pt.tipo == 'AEREO': icon_file = 'aereo2.svg'
        elif pt.tipo == 'MARITIMO': icon_file = 'maritimo2.svg'
        elif pt.tipo == 'ESTACION': icon_file = 'estacion2.svg'
        
        infra_pts_data.append({
            'x': float(pt.longitud) if pt.longitud else 0,
            'y': float(pt.latitud) if pt.latitud else 0,
            'nombre': pt.nombre,
            'estado': normalizar_nombre(pt.estado.nombre),
            'tipo': pt.tipo,
            'url': f"{settings.STATIC_URL}mapa/icons/{icon_file}"
        })

    # --- Capa de Puntos de Rescate Humano (PRH) ---
    prh_points = PRHs.objects.all().select_related('modalidad')
    if user_state:
        prh_points = prh_points.filter(estado=user_state)
    prh_pts_data = []
    for pt in prh_points:
        icon = 'agente_activo2.svg' if pt.activo else 'agente_inactivo2.svg'
        prh_pts_data.append({
            'x': float(pt.longitud) if pt.longitud else 0,
            'y': float(pt.latitud) if pt.latitud else 0,
            'nombre': pt.nombre,
            'estado': normalizar_nombre(pt.estado.nombre),
            'modalidad': pt.modalidad.nombre,
            'status': 'Activo' if pt.activo else 'Inactivo',
            'url': f"{settings.STATIC_URL}mapa/icons/{icon}"
        })

    # --- Capa de Inmuebles (Icono OR_ACTIVO) ---
    inmuebles_objs = Inmueble.objects.all().prefetch_related('tipo_oficina')
    if user_state:
        inmuebles_objs = inmuebles_objs.filter(estado=user_state)
    inmuebles_pts_data = []
    for pt in inmuebles_objs:
        inmuebles_pts_data.append({
            'id': pt.id,
            'x': float(pt.longitud) if pt.longitud else 0,
            'y': float(pt.latitud) if pt.latitud else 0,
            'nombre': pt.nombre_inmueble,
            'estado': normalizar_nombre(pt.estado.nombre),
            'tipo': 'INMUEBLE',
            'tipo_oficina': [normalizar_nombre(to.nombre) for to in pt.tipo_oficina.all()],
            'url': f"{settings.STATIC_URL}mapa/icons/OR_ACTIVO.svg"
        })

    national_data = {
        'name': LABEL_NACIONAL,
        'cs': default_vals.copy(),
        'dt': default_vals.copy(),
        'pe': default_vals.copy()
    }
    
    context = {
        'geo_data_json': json.dumps(geo_data),
        'national_data_json': json.dumps(national_data),
        'infra_data_json': json.dumps(infra_data),
        'infra_pts_data_json': json.dumps(infra_pts_data),
        'prh_pts_data_json': json.dumps(prh_pts_data),
        'inmuebles_pts_data_json': json.dumps(inmuebles_pts_data),
        'label_nacional': LABEL_NACIONAL,
        'metric_labels': METRIC_LABELS,
        'metric_labels_json': json.dumps(METRIC_LABELS),
        'fecha_actualizacion': fecha_act,
        'instrucciones_api_json': json.dumps(api_instrucciones),
        'is_superuser': request.user.is_superuser,
        'user_state_name': user_state.nombre if user_state else '',
        'user_state_name_normalized': normalizar_nombre(user_state.nombre) if user_state else '',
    }
    
    return render(request, 'mapa/mapa_activo.html', context)


# =====================================================================
# GESTIÓN DE INMUEBLES
# =====================================================================

def inmuebles_list(request):
    """Muestra la lista de inmuebles y gestiona sus catálogos."""
    if not request.user.is_authenticated:
        return redirect('/log-in/?next=%s' % request.path)
    user_state = get_user_state(request)
    
    if request.user.is_superuser:
        inmuebles_list = Inmueble.objects.all().order_by('estado__nombre', 'nombre_inmueble')
        estados_list = Estado.objects.all().order_by('nombre')
    elif user_state:
        inmuebles_list = Inmueble.objects.filter(estado=user_state).order_by('nombre_inmueble')
        estados_list = [user_state]
    else:
        inmuebles_list = Inmueble.objects.none()
        estados_list = []
        
    return render(request, 'mapa/inmuebles.html', {
        'inmuebles_list': inmuebles_list,
        'estados_list': estados_list,
        'tipos_inmueble': TipoInmueble.objects.all().order_by('nombre'),
        'situaciones_actuales': SituacionActual.objects.all().order_by('nombre'),
        'tipos_actividad': TipoActividad.objects.all().order_by('nombre'),
        'tipos_oficina': TipoOficina.objects.all().order_by('nombre'),
        'figuras_ocupacion': FiguraOcupacion.objects.all().order_by('tipo'),
        'comodatos_list': Comodato.objects.all().order_by('nombre'),
    })


@transaction.atomic
def guardar_inmueble(request):
    if request.method != 'POST':
        return redirect('inmuebles_list')
        
    user_state = get_user_state(request)
    
    try:
        inmueble_id = request.POST.get('inmueble_id')
        estado_id = request.POST.get('estado_id')
        
        # Validación de seguridad: el estado enviado debe coincidir con el del usuario
        if not request.user.is_superuser:
            if not user_state or str(user_state.id) != str(estado_id):
                raise PermissionError("No tienes permisos para registrar inmuebles en este estado.")
        
        # Obtener o crear objeto Comodato si viene
        comodato_id = request.POST.get('comodato_id') or None
        
        # Campos de superficie
        try:
            sup_total = float(request.POST.get('superficie_total') or 0)
            sup_const = float(request.POST.get('superficie_construida') or 0)
            sup_util = float(request.POST.get('superficie_utilizada') or 0)
        except ValueError:
            raise ValueError("Las superficies deben ser valores numéricos válidos.")

        # Coordenadas
        try:
            lat = float(request.POST.get('latitud') or 0)
            lng = float(request.POST.get('longitud') or 0)
        except ValueError:
            raise ValueError("La latitud y longitud deben ser coordenadas numéricas válidas.")

        # Fechas
        fecha_ocup = request.POST.get('fecha_ocupacion') or None
        anio_const = request.POST.get('anio_construccion') or None

        # Monto Renta
        monto_renta = request.POST.get('monto_renta') or None
        if monto_renta:
            monto_renta = monto_renta.replace('$', '').replace(',', '').strip()
            if not monto_renta:
                monto_renta = None

        defaults = {
            'estado_id': estado_id,
            'nombre_inmueble': normalizar_nombre(request.POST.get('nombre_inmueble', '')),
            'calle': normalizar_nombre(request.POST.get('calle', '')),
            'numero_exterior': request.POST.get('numero_exterior', '').strip(),
            'numero_interior': request.POST.get('numero_interior', '').strip(),
            'colonia': normalizar_nombre(request.POST.get('colonia', '')),
            'municipio': normalizar_nombre(request.POST.get('municipio', '')),
            'codigo_postal': request.POST.get('codigo_postal', '').strip(),
            'latitud': lat,
            'longitud': lng,
            'situacion_actual_id': request.POST.get('situacion_actual_id') or None,
            'tipo_inmueble_id': request.POST.get('tipo_inmueble_id') or None,
            'superficie_total': sup_total,
            'superficie_construida': sup_const,
            'superficie_utilizada': sup_util,
            'numero_de_niveles': int(request.POST.get('numero_de_niveles') or 0),
            'anio_construccion': anio_const,
            'fecha_ocupacion': fecha_ocup,
            'figura_ocupacion_id': request.POST.get('figura_ocupacion_id') or None,
            'monto_renta': monto_renta,
            'comodato_id': comodato_id,
        }

        if inmueble_id:
            inmueble = Inmueble.objects.get(id=inmueble_id)
            # Validación adicional de seguridad para edición
            if not request.user.is_superuser and inmueble.estado != user_state:
                raise PermissionError("No tienes permisos para modificar este inmueble.")
            for key, val in defaults.items():
                setattr(inmueble, key, val)
            inmueble.save()
            created = False
        else:
            inmueble = Inmueble.objects.create(**defaults)
            created = True

        # Guardar/Actualizar ProgramaIPC
        programa_ipc, _ = ProgramaIPC.objects.get_or_create(inmueble=inmueble)
        programa_ipc.inm_pipc = request.POST.get('inm_pipc') == 'on'
        programa_ipc.fecha_inm = request.POST.get('fecha_inm') or None
        programa_ipc.comodante_pipc = request.POST.get('comodante_pipc') == 'on'
        programa_ipc.fecha_comodante = request.POST.get('fecha_comodante') or None
        programa_ipc.plan_emergencia = request.POST.get('plan_emergencia') == 'on'
        programa_ipc.fecha_inicio_plan = request.POST.get('fecha_inicio_plan') or None
        programa_ipc.save()

        # Guardar ManyToMany tipo_actividad
        tipo_actividades_ids = request.POST.getlist('tipo_actividad[]')
        inmueble.tipo_actividad.set(tipo_actividades_ids)

        # Guardar ManyToMany tipo_oficina
        tipo_oficina_ids = request.POST.getlist('tipo_oficina[]')
        inmueble.tipo_oficina.set(tipo_oficina_ids)

        # Guardar nuevo comentario en el histórico si existe
        comentario_texto = request.POST.get('observaciones', '').strip()
        if comentario_texto:
            HistoricoComentarios.objects.create(
                inmueble=inmueble,
                comentario=comentario_texto
            )

        messages.success(request, f"Inmueble '{inmueble.nombre_inmueble}' {'creado' if created else 'actualizado'} correctamente.")
    except Exception as e:
        messages.error(request, f"Error al guardar inmueble: {str(e)}")
        
    return redirect('inmuebles_list')


@transaction.atomic
def eliminar_inmueble(request, inmueble_id):
    """Elimina un inmueble si tiene permisos por estado."""
    try:
        user_state = get_user_state(request)
        inmueble = Inmueble.objects.get(id=inmueble_id)
        
        # Validación de seguridad
        if not request.user.is_superuser:
            if not user_state or inmueble.estado != user_state:
                messages.error(request, "No tienes permisos para eliminar este registro.")
                return redirect('inmuebles_list')
                
        nombre = inmueble.nombre_inmueble
        inmueble.delete()
        messages.success(request, f"Inmueble '{nombre}' eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar inmueble: {str(e)}")
        
    return redirect('inmuebles_list')


def api_get_inmueble(request, inmueble_id):
    """Retorna los datos de un inmueble en formato JSON."""
    try:
        user_state = get_user_state(request)
        inmueble = Inmueble.objects.get(id=inmueble_id)
        
        # Validación de seguridad
        if not request.user.is_superuser:
            if not user_state or inmueble.estado != user_state:
                return JsonResponse({'status': 'error', 'message': 'Sin permisos'}, status=403)
                
        data = {
            'id': inmueble.id,
            'nombre_inmueble': inmueble.nombre_inmueble,
            'estado_id': inmueble.estado_id,
            'calle': inmueble.calle,
            'numero_exterior': inmueble.numero_exterior,
            'numero_interior': inmueble.numero_interior,
            'colonia': inmueble.colonia,
            'municipio': inmueble.municipio,
            'codigo_postal': inmueble.codigo_postal,
            'latitud': inmueble.latitud,
            'longitud': inmueble.longitud,
            'situacion_actual_id': inmueble.situacion_actual_id,
            'tipo_inmueble_id': inmueble.tipo_inmueble_id,
            'superficie_total': inmueble.superficie_total,
            'superficie_construida': inmueble.superficie_construida,
            'superficie_utilizada': inmueble.superficie_utilizada,
            'numero_de_niveles': inmueble.numero_de_niveles,
            'anio_construccion': inmueble.anio_construccion.isoformat() if inmueble.anio_construccion else None,
            'fecha_ocupacion': inmueble.fecha_ocupacion.isoformat() if inmueble.fecha_ocupacion else None,
            'figura_ocupacion_id': inmueble.figura_ocupacion_id,
            'monto_renta': float(inmueble.monto_renta) if inmueble.monto_renta else None,
            'comodato_id': inmueble.comodato_id,
            'inm_pipc': inmueble.pipc.first().inm_pipc if inmueble.pipc.exists() else False,
            'fecha_inm': inmueble.pipc.first().fecha_inm.isoformat() if inmueble.pipc.exists() and inmueble.pipc.first().fecha_inm else None,
            'comodante_pipc': inmueble.pipc.first().comodante_pipc if inmueble.pipc.exists() else False,
            'fecha_comodante': inmueble.pipc.first().fecha_comodante.isoformat() if inmueble.pipc.exists() and inmueble.pipc.first().fecha_comodante else None,
            'plan_emergencia': inmueble.pipc.first().plan_emergencia if inmueble.pipc.exists() else False,
            'fecha_inicio_plan': inmueble.pipc.first().fecha_inicio_plan.isoformat() if inmueble.pipc.exists() and inmueble.pipc.first().fecha_inicio_plan else None,
            'comentarios': [
                {
                    'id': c.id,
                    'comentario': c.comentario,
                    'fecha_creacion': c.fecha_creacion.strftime('%d/%m/%Y %H:%M')
                }
                for c in inmueble.comentarios.all().order_by('-fecha_creacion')
            ],
            'tipo_actividad_ids': list(inmueble.tipo_actividad.values_list('id', flat=True)),
            'tipo_oficina_ids': list(inmueble.tipo_oficina.values_list('id', flat=True)),
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@transaction.atomic
def api_guardar_comodato(request):
    """Crea un nuevo comodato mediante petición AJAX y lo retorna."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
    try:
        nombre = request.POST.get('nombre', '').strip().upper()
        if not nombre:
            return JsonResponse({'status': 'error', 'message': 'El nombre es obligatorio.'}, status=400)
            
        comodato, created = Comodato.objects.get_or_create(nombre=nombre)
        return JsonResponse({'status': 'success', 'data': {'id': comodato.id, 'nombre': comodato.nombre}})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def organigramas_list(request):
    """Vista para la gestión de Organigramas por Estado."""
    if not request.user.is_authenticated:
        return redirect('/log-in/?next=%s' % request.path)
    user_state = get_user_state(request)
    
    if user_state:
        estados_list = [user_state]
        organigramas = OrganigramaF.objects.filter(estado=user_state).order_by('estado__nombre')
    else:
        estados_list = Estado.objects.all().order_by('nombre')
        organigramas = OrganigramaF.objects.all().order_by('estado__nombre')

    return render(request, 'mapa/organigramas.html', {
        'estados_list': estados_list,
        'organigramas_list': organigramas,
    })


@transaction.atomic
def guardar_organigrama(request):
    """Crea o actualiza la Estructura Orgánica para un Estado."""
    if request.method != 'POST':
        return redirect('organigramas_list')
        
    user_state = get_user_state(request)
    
    try:
        estado_id = request.POST.get('estado_id')
        vigencia = request.POST.get('vigencia') or None
        archivo = request.FILES.get('archivo')
        
        # Seguridad: verificar que coincida con el estado del usuario si no es superusuario
        if user_state and str(user_state.id) != str(estado_id):
            raise PermissionError("No tienes permisos para registrar la Estructura Orgánica en este estado.")
            
        defaults = {
            'vigencia': vigencia,
        }
        if archivo:
            defaults['archivo'] = archivo
            
        OrganigramaF.objects.update_or_create(
            estado_id=estado_id,
            defaults=defaults
        )
        
        messages.success(request, "Estructura Orgánica guardada correctamente.")
    except Exception as e:
        messages.error(request, f"Error al guardar la Estructura Orgánica: {str(e)}")
        
    return redirect('organigramas_list')


@transaction.atomic
def eliminar_organigrama(request, org_id):
    """Elimina la Estructura Orgánica de un Estado."""
    try:
        user_state = get_user_state(request)
        org = OrganigramaF.objects.get(id=org_id)
        
        if user_state and org.estado != user_state:
            messages.error(request, "No tienes permisos para eliminar este registro.")
            return redirect('organigramas_list')
            
        estado_nombre = org.estado.nombre
        org.delete()
        messages.success(request, f"Estructura Orgánica de {estado_nombre} eliminada correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar registro: {str(e)}")
        
    return redirect('organigramas_list')


def api_get_organigrama(request, estado_id):
    """Retorna la información del organigrama de un estado en formato JSON."""
    try:
        org = OrganigramaF.objects.get(estado_id=estado_id)
        return JsonResponse({
            'status': 'success',
            'data': {
                'pdf_url': org.archivo.url if org.archivo else '',
                'vigencia': org.vigencia.strftime('%d/%m/%Y') if org.vigencia else 'Sin vigencia'
            }
        })
    except OrganigramaF.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'No hay organigrama cargado para este estado.'
        })


def api_get_inmueble_detalle(request, inmueble_id):
    """Retorna toda la información detallada de un inmueble en formato JSON para el modal interactivo."""
    try:
        inmueble = Inmueble.objects.select_related('estado', 'figura_ocupacion', 'comodato').get(id=inmueble_id)
        
        # 1. Jefe de Oficina
        jefe = PersonalINM.objects.filter(lugar_asignado=inmueble, jefe_oficina=True).first()
        if jefe:
            nombre_jefe = f"{jefe.nombre or ''} {jefe.apellido or ''}".strip()
            if not nombre_jefe:
                nombre_jefe = "S/A"
        else:
            nombre_jefe = "S/A"
            
        # 2. Personal conteo
        personal_qs = PersonalINM.objects.filter(lugar_asignado=inmueble)
        total_personal = personal_qs.count()
        activos = personal_qs.filter(estatus__estatus__iexact='ACTIVO').count()
        inactivos = personal_qs.filter(estatus__estatus__iexact='VACANTE').count()
        
        # 3. PIPC (Programa IPC)
        pipc = inmueble.pipc.first()
        fecha_inm_str = "sin programa"
        fecha_comodante_str = "sin programa"
        fecha_inicio_plan_str = "sin programa"
        
        if pipc:
            if pipc.inm_pipc and pipc.fecha_inm:
                fecha_inm_str = pipc.fecha_inm.strftime('%d/%m/%Y')
            if pipc.comodante_pipc and pipc.fecha_comodante:
                fecha_comodante_str = pipc.fecha_comodante.strftime('%d/%m/%Y')
            if pipc.plan_emergencia and pipc.fecha_inicio_plan:
                fecha_inicio_plan_str = pipc.fecha_inicio_plan.strftime('%d/%m/%Y')

        # 4. Dirección completa
        num_ext = f"No. {inmueble.numero_exterior}" if inmueble.numero_exterior else "S/N"
        num_int = f" Int. {inmueble.numero_interior}" if inmueble.numero_interior and inmueble.numero_interior.strip() != "" else ""
        colonia = f", Col. {inmueble.colonia}" if inmueble.colonia else ""
        municipio = f", {inmueble.municipio}" if inmueble.municipio else ""
        cp = f", C.P. {inmueble.codigo_postal}" if inmueble.codigo_postal else ""
        estado_nombre = inmueble.estado.nombre
        
        direccion_completa = f"{inmueble.calle or ''} {num_ext}{num_int}{colonia}{municipio}{cp}, {estado_nombre}".strip()
        
        # 5. General info
        superficie_util = inmueble.superficie_utilizada if inmueble.superficie_utilizada else 0.0
        niveles = inmueble.numero_de_niveles if inmueble.numero_de_niveles is not None else 0
        anio_const = inmueble.anio_construccion.strftime('%Y') if inmueble.anio_construccion else "S/D"
        fecha_ocu = inmueble.fecha_ocupacion.strftime('%d/%m/%Y') if inmueble.fecha_ocupacion else "S/D"
        
        # 6. Figura de Ocupación
        figura_tipo = inmueble.figura_ocupacion.tipo.upper() if inmueble.figura_ocupacion else ""
        
        arrendado_activo = "ARRENDADO" in figura_tipo
        propio_activo = "PROPIO" in figura_tipo
        terreno_activo = "TERRENO" in figura_tipo
        comodato_activo = "COMODATO" in figura_tipo
        
        # 7. Renta
        renta_str = "S/D"
        if arrendado_activo and inmueble.monto_renta is not None:
            renta_str = f"${inmueble.monto_renta:,.2f}"
            
        # 8. Tipos de Oficina (las que tiene asignadas el inmueble)
        oficinas_asignadas = list(inmueble.tipo_oficina.values_list('nombre', flat=True))
        
        # 9. Actividades (todas y marcar activas)
        actividades_all = TipoActividad.objects.all().order_by('nombre')
        actividades_data = []
        for act in actividades_all:
            is_active = inmueble.tipo_actividad.filter(id=act.id).exists()
            actividades_data.append({
                'id': act.id,
                'nombre': act.nombre,
                'activo': is_active
            })
            
        data = {
            'id': inmueble.id,
            'nombre_inmueble': inmueble.nombre_inmueble,
            'estado_nombre': estado_nombre,
            'estado_id': inmueble.estado.id,
            'nombre_jefe': nombre_jefe,
            'personal': {
                'total': total_personal,
                'activos': activos,
                'inactivos': inactivos
            },
            'vehiculos': {
                'total': "S/D",
                'activos': "S/D",
                'inactivos': "S/D"
            },
            'pipc': {
                'fecha_inm': fecha_inm_str,
                'fecha_comodante': fecha_comodante_str,
                'fecha_inicio_plan': fecha_inicio_plan_str
            },
            'direccion_completa': direccion_completa,
            'superficie_utilizada': f"{superficie_util:,.2f}" if superficie_util else "0.00",
            'numero_de_niveles': niveles,
            'anio_construccion': anio_const,
            'fecha_ocupacion': fecha_ocu,
            'figura_ocupacion': {
                'tipo': figura_tipo,
                'arrendado_activo': arrendado_activo,
                'propio_activo': propio_activo,
                'terreno_activo': terreno_activo,
                'comodato_activo': comodato_activo
            },
            'renta': renta_str,
            'oficinas_asignadas': oficinas_asignadas,
            'actividades': actividades_data
        }
        
        return JsonResponse({
            'status': 'success',
            'data': data
        })
    except Inmueble.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'El inmueble solicitado no existe.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def api_get_estado_detalle(request, estado_id):
    """Retorna la información agregada de todos los inmuebles de un estado en formato JSON para el modal interactivo de estado."""
    try:
        if estado_id == 0:
            inmuebles = Inmueble.objects.all()
            inmuebles_ids = list(inmuebles.values_list('id', flat=True))
            inmueble_count = inmuebles.count()
            
            # 1. Personal
            personal_qs = PersonalINM.objects.filter(lugar_asignado_id__in=inmuebles_ids)
            total_personal = personal_qs.count()
            activos = personal_qs.filter(estatus__estatus__iexact='ACTIVO').count()
            inactivos = personal_qs.filter(estatus__estatus__iexact='VACANTE').count()
            
            # 2. PIPC (Programa IPC)
            from .models import ProgramaIPC
            pipc_qs = ProgramaIPC.objects.filter(inmueble_id__in=inmuebles_ids)
            count_inm_pipc = pipc_qs.filter(inm_pipc=True).count()
            count_comodante_pipc = pipc_qs.filter(comodante_pipc=True).count()
            count_plan_emergencia = pipc_qs.filter(plan_emergencia=True).count()
            
            inm_pipc_list = list(Inmueble.objects.filter(id__in=list(pipc_qs.filter(inm_pipc=True).values_list('inmueble_id', flat=True))).values('id', 'nombre_inmueble'))
            comodante_pipc_list = list(Inmueble.objects.filter(id__in=list(pipc_qs.filter(comodante_pipc=True).values_list('inmueble_id', flat=True))).values('id', 'nombre_inmueble'))
            plan_emergencia_list = list(Inmueble.objects.filter(id__in=list(pipc_qs.filter(plan_emergencia=True).values_list('inmueble_id', flat=True))).values('id', 'nombre_inmueble'))
            
            # 3. Tipos de Oficina
            from django.db.models import Count
            from .models import TipoOficina
            oficinas_conteo = TipoOficina.objects.filter(inmueble__isnull=False).annotate(total=Count('inmueble')).filter(total__gt=0).order_by('-total')
            oficinas_data = []
            for of in oficinas_conteo:
                inms_list = list(Inmueble.objects.filter(tipo_oficina=of).values('id', 'nombre_inmueble'))
                oficinas_data.append({
                    'nombre': of.nombre,
                    'total': of.total,
                    'inmuebles': inms_list
                })
                
            # 4. Actividades
            from .models import TipoActividad
            actividades_conteo = TipoActividad.objects.filter(inmueble__isnull=False).annotate(total=Count('inmueble')).filter(total__gt=0).order_by('-total')
            actividades_data = []
            for act in actividades_conteo:
                inms_list = list(Inmueble.objects.filter(tipo_actividad=act).values('id', 'nombre_inmueble'))
                actividades_data.append({
                    'nombre': act.nombre,
                    'total': act.total,
                    'inmuebles': inms_list
                })
                
            # 5. Superficies y Renta
            from django.db.models import Sum
            sums = inmuebles.aggregate(
                total_construida=Sum('superficie_construida'),
                total_utilizada=Sum('superficie_utilizada'),
                total_renta=Sum('monto_renta')
            )
            
            superficie_const = sums['total_construida'] or 0.0
            superficie_util = sums['total_utilizada'] or 0.0
            total_renta = sums['total_renta'] or 0.0
            
            # 6. Figura de Ocupación
            from .models import FiguraOcupacion
            figuras_conteo = FiguraOcupacion.objects.filter(inmueble__isnull=False).annotate(total=Count('inmueble')).filter(total__gt=0)
            figuras_dict = {
                'ARRENDADO': 0,
                'PROPIO': 0,
                'TERRENO': 0,
                'COMODATO': 0
            }
            for fig in figuras_conteo:
                fig_tipo = fig.tipo.upper()
                if 'ARRENDADO' in fig_tipo:
                    figuras_dict['ARRENDADO'] += fig.total
                elif 'PROPIO' in fig_tipo:
                    figuras_dict['PROPIO'] += fig.total
                elif 'TERRENO' in fig_tipo:
                    figuras_dict['TERRENO'] += fig.total
                elif 'COMODATO' in fig_tipo:
                    figuras_dict['COMODATO'] += fig.total
                    
            data = {
                'estado_nombre': 'TOTAL NACIONAL',
                'inmueble_count': inmueble_count,
                'personal': {
                    'total': total_personal,
                    'activos': activos,
                    'inactivos': inactivos
                },
                'vehiculos': {
                    'total': "S/D",
                    'activos': "S/D",
                    'inactivos': "S/D"
                },
                'pipc': {
                    'inm_pipc_count': count_inm_pipc,
                    'inm_pipc_inmuebles': inm_pipc_list,
                    'comodante_pipc_count': count_comodante_pipc,
                    'comodante_pipc_inmuebles': comodante_pipc_list,
                    'plan_emergencia_count': count_plan_emergencia,
                    'plan_emergencia_inmuebles': plan_emergencia_list
                },
                'superficie_construida': f"{superficie_const:,.2f}" if superficie_const else "0.00",
                'superficie_utilizada': f"{superficie_util:,.2f}" if superficie_util else "0.00",
                'figura_ocupacion': figuras_dict,
                'figura_ocupacion_inmuebles': {
                    'ARRENDADO': list(Inmueble.objects.filter(figura_ocupacion__tipo__icontains='ARRENDADO').values('id', 'nombre_inmueble')),
                    'PROPIO': list(Inmueble.objects.filter(figura_ocupacion__tipo__icontains='PROPIO').values('id', 'nombre_inmueble')),
                    'TERRENO': list(Inmueble.objects.filter(figura_ocupacion__tipo__icontains='TERRENO').values('id', 'nombre_inmueble')),
                    'COMODATO': list(Inmueble.objects.filter(figura_ocupacion__tipo__icontains='COMODATO').values('id', 'nombre_inmueble')),
                },
                'renta': f"${total_renta:,.2f}" if total_renta else "S/D",
                'oficinas': oficinas_data,
                'actividades': actividades_data
            }
            
            return JsonResponse({
                'status': 'success',
                'data': data
            })

        estado = Estado.objects.get(id=estado_id)
        
        # Inmuebles en este estado
        inmuebles = Inmueble.objects.filter(estado=estado)
        inmuebles_ids = list(inmuebles.values_list('id', flat=True))
        inmueble_count = inmuebles.count()
        
        # 1. Personal
        personal_qs = PersonalINM.objects.filter(lugar_asignado_id__in=inmuebles_ids)
        total_personal = personal_qs.count()
        activos = personal_qs.filter(estatus__estatus__iexact='ACTIVO').count()
        inactivos = personal_qs.filter(estatus__estatus__iexact='VACANTE').count()
        
        # 2. PIPC (Programa IPC) - Cuenta de inmuebles con programas activos y sus listados
        from .models import ProgramaIPC
        pipc_qs = ProgramaIPC.objects.filter(inmueble_id__in=inmuebles_ids)
        count_inm_pipc = pipc_qs.filter(inm_pipc=True).count()
        count_comodante_pipc = pipc_qs.filter(comodante_pipc=True).count()
        count_plan_emergencia = pipc_qs.filter(plan_emergencia=True).count()
        
        inm_pipc_list = list(Inmueble.objects.filter(estado=estado, id__in=list(pipc_qs.filter(inm_pipc=True).values_list('inmueble_id', flat=True))).values('id', 'nombre_inmueble'))
        comodante_pipc_list = list(Inmueble.objects.filter(estado=estado, id__in=list(pipc_qs.filter(comodante_pipc=True).values_list('inmueble_id', flat=True))).values('id', 'nombre_inmueble'))
        plan_emergencia_list = list(Inmueble.objects.filter(estado=estado, id__in=list(pipc_qs.filter(plan_emergencia=True).values_list('inmueble_id', flat=True))).values('id', 'nombre_inmueble'))
        
        # 3. Tipos de Oficina (Suma de inmuebles por tipo de oficina)
        from django.db.models import Count
        from .models import TipoOficina
        oficinas_conteo = TipoOficina.objects.filter(inmueble__estado=estado).annotate(total=Count('inmueble')).filter(total__gt=0).order_by('-total')
        oficinas_data = []
        for of in oficinas_conteo:
            inms_list = list(Inmueble.objects.filter(estado=estado, tipo_oficina=of).values('id', 'nombre_inmueble'))
            oficinas_data.append({
                'nombre': of.nombre,
                'total': of.total,
                'inmuebles': inms_list
            })
            
        # 4. Actividades (Suma de inmuebles por tipo de actividad)
        from .models import TipoActividad
        actividades_conteo = TipoActividad.objects.filter(inmueble__estado=estado).annotate(total=Count('inmueble')).filter(total__gt=0).order_by('-total')
        actividades_data = []
        for act in actividades_conteo:
            inms_list = list(Inmueble.objects.filter(estado=estado, tipo_actividad=act).values('id', 'nombre_inmueble'))
            actividades_data.append({
                'nombre': act.nombre,
                'total': act.total,
                'inmuebles': inms_list
            })
            
        # 5. Superficies y Renta
        from django.db.models import Sum
        sums = inmuebles.aggregate(
            total_construida=Sum('superficie_construida'),
            total_utilizada=Sum('superficie_utilizada'),
            total_renta=Sum('monto_renta')
        )
        
        superficie_const = sums['total_construida'] or 0.0
        superficie_util = sums['total_utilizada'] or 0.0
        total_renta = sums['total_renta'] or 0.0
        
        # 6. Figura de Ocupación (Conteo por figura de ocupación)
        from .models import FiguraOcupacion
        figuras_conteo = FiguraOcupacion.objects.filter(inmueble__estado=estado).annotate(total=Count('inmueble')).filter(total__gt=0)
        figuras_dict = {
            'ARRENDADO': 0,
            'PROPIO': 0,
            'TERRENO': 0,
            'COMODATO': 0
        }
        for fig in figuras_conteo:
            fig_tipo = fig.tipo.upper()
            if 'ARRENDADO' in fig_tipo:
                figuras_dict['ARRENDADO'] += fig.total
            elif 'PROPIO' in fig_tipo:
                figuras_dict['PROPIO'] += fig.total
            elif 'TERRENO' in fig_tipo:
                figuras_dict['TERRENO'] += fig.total
            elif 'COMODATO' in fig_tipo:
                figuras_dict['COMODATO'] += fig.total
                
        data = {
            'estado_nombre': estado.nombre,
            'inmueble_count': inmueble_count,
            'personal': {
                'total': total_personal,
                'activos': activos,
                'inactivos': inactivos
            },
            'vehiculos': {
                'total': "S/D",
                'activos': "S/D",
                'inactivos': "S/D"
            },
            'pipc': {
                'inm_pipc_count': count_inm_pipc,
                'inm_pipc_inmuebles': inm_pipc_list,
                'comodante_pipc_count': count_comodante_pipc,
                'comodante_pipc_inmuebles': comodante_pipc_list,
                'plan_emergencia_count': count_plan_emergencia,
                'plan_emergencia_inmuebles': plan_emergencia_list
            },
            'superficie_construida': f"{superficie_const:,.2f}" if superficie_const else "0.00",
            'superficie_utilizada': f"{superficie_util:,.2f}" if superficie_util else "0.00",
            'figura_ocupacion': figuras_dict,
            'figura_ocupacion_inmuebles': {
                'ARRENDADO': list(Inmueble.objects.filter(estado=estado, figura_ocupacion__tipo__icontains='ARRENDADO').values('id', 'nombre_inmueble')),
                'PROPIO': list(Inmueble.objects.filter(estado=estado, figura_ocupacion__tipo__icontains='PROPIO').values('id', 'nombre_inmueble')),
                'TERRENO': list(Inmueble.objects.filter(estado=estado, figura_ocupacion__tipo__icontains='TERRENO').values('id', 'nombre_inmueble')),
                'COMODATO': list(Inmueble.objects.filter(estado=estado, figura_ocupacion__tipo__icontains='COMODATO').values('id', 'nombre_inmueble')),
            },
            'renta': f"${total_renta:,.2f}" if total_renta else "S/D",
            'oficinas': oficinas_data,
            'actividades': actividades_data
        }
        
        return JsonResponse({
            'status': 'success',
            'data': data
        })
    except Estado.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'El estado solicitado no existe.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def api_get_personal_stats(request, estado_id):
    try:
        from datetime import date
        import unicodedata
        today = date.today()
        
        if estado_id == 0:
            qs_all = PersonalINM.objects.all().select_related('estatus', 'tipo_plaza')
            estado_nombre_display = "TOTAL NACIONAL"
        else:
            estado = Estado.objects.get(id=estado_id)
            
            # Check if filtering by specific inmueble
            inmueble_id = request.GET.get('inmueble_id')
            inmueble = None
            if inmueble_id:
                try:
                    inmueble = Inmueble.objects.get(id=inmueble_id)
                    qs_all = PersonalINM.objects.filter(lugar_asignado=inmueble).select_related('estatus', 'tipo_plaza')
                    estado_nombre_display = f"{estado.nombre} - {inmueble.nombre_inmueble}"
                    if inmueble.estado:
                        estado = inmueble.estado
                except Inmueble.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'El inmueble solicitado no existe.'}, status=404)
            else:
                qs_all = PersonalINM.objects.filter(estado=estado).select_related('estatus', 'tipo_plaza')
                estado_nombre_display = estado.nombre
            
        def clean_text(text):
            if not text:
                return ""
            normalized = unicodedata.normalize('NFD', text)
            cleaned = "".join(c for c in normalized if not unicodedata.combining(c))
            return cleaned.upper().strip()

        MANDOS_MEDIOS_KEYWORDS = [
            ('OFICINA DE REPRESENTACION', 'OFICINA DE REPRESENTACION'),
            ('SUB REPRESENTACION FEDERAL', 'SUB REPRESENTACIÓN FEDERAL'),
            ('SUB REPRESENTACION LOCAL', 'SUB REPRESENTACIÓN LOCAL'),
            ('REPRESENTACION LOCAL', 'REPRESENTACIÓN LOCAL'),
            ('SUBDIRECCION', 'SUBDIRECCIÓN'),
            ('COORDINACION', 'COORDINACIÓN'),
            ('DEPARTAMENTO', 'DEPARTAMENTO'),
            ('DIRECCION', 'DIRECCIÓN'),
        ]

        def get_stats_for_qs(qs):
            total = qs.count()
            
            # Plaza type totals
            base = qs.filter(tipo_plaza__plazaT__iexact='BASE').count()
            confianza = qs.filter(tipo_plaza__plazaT__iexact='CONFIANZA').count()
            eventual = qs.filter(tipo_plaza__plazaT__iexact='EVENTUAL').count()
            
            # Categories lists
            enlace_operativo_groups = {}
            mandos_medios_groups = {}
            
            enlace_levels = {'2', '3', '5', '6', '7', '11', 'P11', 'P12', 'P13'}
            mandos_levels = {'O11', 'O21', 'O23', 'M11', 'M23', 'N11', 'N22', 'M41', 'M43'}
            
            for p in qs:
                lvl = (p.nivel or '').strip().upper()
                puesto_raw = p.puesto_especifico or ''
                puesto_upper = puesto_raw.upper().strip()
                
                # Check if it belongs to Enlace y Operativo
                if lvl in enlace_levels:
                    # Group by puesto_especifico (exact upper text)
                    if puesto_upper not in enlace_operativo_groups:
                        enlace_operativo_groups[puesto_upper] = []
                    enlace_operativo_groups[puesto_upper].append(p)
                    
                # Check if it belongs to Mandos Medios
                elif lvl in mandos_levels:
                    # Find keyword group
                    puesto_clean = clean_text(puesto_raw)
                    group_name = None
                    for kw_clean, kw_display in MANDOS_MEDIOS_KEYWORDS:
                        if kw_clean in puesto_clean:
                            group_name = kw_display
                            break
                    if not group_name:
                        group_name = puesto_upper if puesto_upper else "S/D"
                    
                    if group_name not in mandos_medios_groups:
                        mandos_medios_groups[group_name] = []
                    mandos_medios_groups[group_name].append(p)

                else:
                    # Group by puesto_especifico (exact upper text)
                    if puesto_upper not in enlace_operativo_groups:
                        enlace_operativo_groups[puesto_upper] = []
                    enlace_operativo_groups[puesto_upper].append(p)

            def get_row_stats(group_name, plist):
                t = len(plist)
                b = sum(1 for p in plist if p.tipo_plaza and p.tipo_plaza.plazaT.upper() == 'BASE')
                c = sum(1 for p in plist if p.tipo_plaza and p.tipo_plaza.plazaT.upper() == 'CONFIANZA')
                ev = sum(1 for p in plist if p.tipo_plaza and p.tipo_plaza.plazaT.upper() == 'EVENTUAL')
                
                # Gender breakdown per plaza type
                b_m = sum(1 for p in plist if p.tipo_plaza and p.tipo_plaza.plazaT.upper() == 'BASE' and p.sexo == 'F')
                b_h = sum(1 for p in plist if p.tipo_plaza and p.tipo_plaza.plazaT.upper() == 'BASE' and p.sexo == 'M')
                c_m = sum(1 for p in plist if p.tipo_plaza and p.tipo_plaza.plazaT.upper() == 'CONFIANZA' and p.sexo == 'F')
                c_h = sum(1 for p in plist if p.tipo_plaza and p.tipo_plaza.plazaT.upper() == 'CONFIANZA' and p.sexo == 'M')
                ev_m = sum(1 for p in plist if p.tipo_plaza and p.tipo_plaza.plazaT.upper() == 'EVENTUAL' and p.sexo == 'F')
                ev_h = sum(1 for p in plist if p.tipo_plaza and p.tipo_plaza.plazaT.upper() == 'EVENTUAL' and p.sexo == 'M')
                
                # Puestos especificos breakdown per plaza type
                base_puestos = {}
                confianza_puestos = {}
                eventual_puestos = {}
                for p in plist:
                    puesto = p.puesto_especifico or 'SIN ESPECIFICAR'
                    plaza = p.tipo_plaza.plazaT.upper() if (p.tipo_plaza and p.tipo_plaza.plazaT) else ''
                    if plaza == 'BASE':
                        base_puestos[puesto] = base_puestos.get(puesto, 0) + 1
                    elif plaza == 'CONFIANZA':
                        confianza_puestos[puesto] = confianza_puestos.get(puesto, 0) + 1
                    elif plaza == 'EVENTUAL':
                        eventual_puestos[puesto] = eventual_puestos.get(puesto, 0) + 1
                
                return {
                    'group_name': group_name,
                    'total': t,
                    'base': b,
                    'confianza': c,
                    'eventual': ev,
                    'base_mujeres': b_m,
                    'base_hombres': b_h,
                    'confianza_mujeres': c_m,
                    'confianza_hombres': c_h,
                    'eventual_mujeres': ev_m,
                    'eventual_hombres': ev_h,
                    'base_puestos': base_puestos,
                    'confianza_puestos': confianza_puestos,
                    'eventual_puestos': eventual_puestos,
                }

            enlace_list = [get_row_stats(name, plist) for name, plist in sorted(enlace_operativo_groups.items())]
            mandos_list = [get_row_stats(name, plist) for name, plist in sorted(mandos_medios_groups.items())]
            
            # Age ranges for active staff
            age_ranges = {'18-26': 0, '26-34': 0, '34-42': 0, '42-50': 0, '50-58': 0}
            women_count = sum(1 for p in qs if p.sexo == 'F')
            men_count = sum(1 for p in qs if p.sexo == 'M')
            
            for p in qs:
                if p.fecha_nacimiento:
                    born = p.fecha_nacimiento
                    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
                    if 18 <= age <= 26: age_ranges['18-26'] += 1
                    elif 27 <= age <= 34: age_ranges['26-34'] += 1
                    elif 35 <= age <= 42: age_ranges['34-42'] += 1
                    elif 43 <= age <= 50: age_ranges['42-50'] += 1
                    elif 51 <= age <= 58: age_ranges['50-58'] += 1
                    
            return {
                'total': total,
                'base': base,
                'confianza': confianza,
                'eventual': eventual,
                'enlace_operativo': enlace_list,
                'mandos_medios': mandos_list,
                'mujeres': women_count,
                'hombres': men_count,
                'edades': age_ranges
            }
            
        # Segment querysets
        qs_total = qs_all
        qs_vacantes = qs_all.filter(estatus__estatus__iexact='VACANTE')
        qs_activos = qs_all.filter(estatus__estatus__iexact='ACTIVO')
        
        data = {
            'estado_nombre': estado_nombre_display,
            'total': get_stats_for_qs(qs_total),
            'vacantes': get_stats_for_qs(qs_vacantes),
            'activos': get_stats_for_qs(qs_activos),
        }
        
        return JsonResponse({'status': 'success', 'data': data})
    except Estado.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'El estado solicitado no existe.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def vehiculos_list(request):
    """Vista para la gestión de Vehículos con paginación y filtros en el servidor."""
    if not request.user.is_authenticated:
        return redirect('/log-in/?next=%s' % request.path)
    
    from .models import VehiculosOR, TipoVeh, TipoAsignacionVeh, Estado, Inmueble, SituacionVeh
    
    user_state = get_user_state(request)
    
    # 1. Obtener filtros de la solicitud GET
    placa_query = request.GET.get('placa', '').strip()
    marca_query = request.GET.get('marca', '').strip()
    estado_id_query = request.GET.get('estado_id', '').strip()
    page_number = request.GET.get('page', 1)
    
    # 2. Filtrar queryset de vehículos
    vehiculos_qs = VehiculosOR.objects.all().select_related('tipoVeh', 'asignacion', 'estado', 'inmueble', 'fotografias', 'situacion')
    
    if user_state:
        vehiculos_qs = vehiculos_qs.filter(estado=user_state)
        estados_list_all = [user_state]
    else:
        estados_list_all = Estado.objects.all().order_by('nombre')
        if estado_id_query:
            vehiculos_qs = vehiculos_qs.filter(estado_id=estado_id_query)
            
    if placa_query:
        vehiculos_qs = vehiculos_qs.filter(placa__icontains=placa_query)
        
    if marca_query:
        vehiculos_qs = vehiculos_qs.filter(marca__icontains=marca_query)
        
    vehiculos_qs = vehiculos_qs.order_by('estado__nombre', 'marca', 'modelo')
    total_matched = vehiculos_qs.count()
    
    # 3. Paginación de resultados (50 por página)
    from django.core.paginator import Paginator
    paginator = Paginator(vehiculos_qs, 50)
    page_obj = paginator.get_page(page_number)
    
    # 4. Listados para formularios de creación/edición
    tipo_veh_list = TipoVeh.objects.all().order_by('tipo_veh')
    asignacion_list = TipoAsignacionVeh.objects.all().order_by('tipo')
    situacion_list = SituacionVeh.objects.all().order_by('situacion')
    
    if user_state:
        estados_list = [user_state]
        inmuebles_list = Inmueble.objects.filter(estado=user_state).order_by('nombre_inmueble')
    else:
        estados_list = Estado.objects.all().order_by('nombre')
        inmuebles_list = Inmueble.objects.all().order_by('nombre_inmueble')
        
    return render(request, 'mapa/vehiculos_list.html', {
        'estados_list': estados_list,
        'estados_list_all': estados_list_all,
        'inmuebles_list': inmuebles_list,
        'tipo_veh_list': tipo_veh_list,
        'asignacion_list': asignacion_list,
        'situacion_list': situacion_list,
        'vehiculos_list': page_obj,
        'total_matched': total_matched,
        'placa_query': placa_query,
        'marca_query': marca_query,
        'estado_id_query': estado_id_query,
    })


def guardar_vehiculo(request):
    if not request.user.is_authenticated:
        return redirect('/log-in/')
        
    if request.method != 'POST':
        return redirect('vehiculos_list')
    
    user_state = get_user_state(request)
    from .models import VehiculosOR, FotosVeh
    from django.contrib import messages
    
    try:
        vehiculo_id = request.POST.get('vehiculo_id')
        estado_id = request.POST.get('estado_id')
        
        # Validación de seguridad: el estado enviado debe coincidir con el del usuario
        if user_state and str(user_state.id) != str(estado_id):
            raise PermissionError("No tienes permisos para registrar vehículos en este estado.")
            
        anio_year = request.POST.get('anio') or None
        anio = None
        if anio_year and anio_year.strip().isdigit():
            from datetime import date
            anio = date(int(anio_year), 1, 1)
            
        fecha_disp_comb = request.POST.get('fecha_disp_comb') or None
        
        # Procesar fotos de vehículos
        fotos_id = request.POST.get('fotografias_id') or None
        fotos_obj = None
        
        frente_file = request.FILES.get('foto_frente')
        lateral_file = request.FILES.get('foto_lateral')
        trasera_file = request.FILES.get('foto_trasera')
        
        if frente_file or lateral_file or trasera_file or fotos_id:
            if fotos_id:
                fotos_obj = FotosVeh.objects.get(id=fotos_id)
            else:
                fotos_obj = FotosVeh()
                
            if frente_file:
                fotos_obj.frente = frente_file
            if lateral_file:
                fotos_obj.lateral = lateral_file
            if trasera_file:
                fotos_obj.trasera = trasera_file
                
            fotos_obj.save()
            
        monto_raw = request.POST.get('monto') or '0'
        # Limpiar caracteres como signo de pesos o comas
        monto_raw = monto_raw.replace('$', '').replace(',', '').strip()
        monto = float(monto_raw) if monto_raw else 0.0
            
        defaults = {
            'marca': request.POST.get('marca', '').strip().upper(),
            'modelo': request.POST.get('modelo', '').strip().upper(),
            'anio': anio,
            'placa': request.POST.get('placa', '').strip().upper(),
            'no_motor': request.POST.get('no_motor', '').strip().upper(),
            'tarjeta_asig': request.POST.get('tarjeta_asig', '').strip().upper() or None,
            'fecha_disp_comb': fecha_disp_comb,
            'monto': monto,
            'tipoVeh_id': request.POST.get('tipoVeh_id') or None,
            'asignacion_id': request.POST.get('asignacion_id'),
            'estado_id': estado_id,
            'inmueble_id': request.POST.get('inmueble_id') or None,
            'fotografias': fotos_obj,
            'situacion_id': request.POST.get('situacion_id') or None,
        }
        
        if vehiculo_id:
            vehiculo = VehiculosOR.objects.get(id=vehiculo_id)
            if user_state and vehiculo.estado != user_state:
                raise PermissionError("No tienes permisos para modificar este registro.")
            for key, value in defaults.items():
                setattr(vehiculo, key, value)
            vehiculo.save()
            messages.success(request, "Vehículo actualizado exitosamente.")
        else:
            vehiculo = VehiculosOR.objects.create(**defaults)
            
            # --- REGISTROS INICIALES OPCIONALES ---
            from .models import Kilometraje, PrestadoDe, Siniestros, Capufe, CombustibleExt
            
            # 1. Kilometraje
            init_odometro = request.POST.get('init_odometro')
            if init_odometro:
                tipo_unidad = request.POST.get('init_tipo_unidad', 'KM')
                evidencia = request.FILES.get('init_evidencia')
                Kilometraje.objects.create(
                    vehiculo=vehiculo,
                    fecha=fecha_disp_comb or anio,
                    tipo=tipo_unidad,
                    odometro=float(init_odometro),
                    evidencia=evidencia
                )
                
            # 2. Préstamo
            init_prestado_estado_id = request.POST.get('init_prestado_estado_id')
            if init_prestado_estado_id:
                PrestadoDe.objects.create(
                    vehiculo=vehiculo,
                    estado_id=init_prestado_estado_id,
                    inmueble_id=request.POST.get('init_prestado_inmueble_id') or None,
                    fecha_prestamo=request.POST.get('init_prestado_fecha') or None
                )
                
            # 3. Siniestro
            init_siniestro_fecha = request.POST.get('init_siniestro_fecha')
            if init_siniestro_fecha:
                Siniestros.objects.create(
                    vehiculo=vehiculo,
                    fecha=init_siniestro_fecha,
                    folio=request.POST.get('init_siniestro_folio', '').strip().upper() or None
                )
                
            # 4. Capufe
            init_capufe_fecha_inicio = request.POST.get('init_capufe_fecha_inicio')
            if init_capufe_fecha_inicio:
                Capufe.objects.create(
                    vehiculo=vehiculo,
                    fecha_inicio=init_capufe_fecha_inicio,
                    fecha_termino=request.POST.get('init_capufe_fecha_termino') or None
                )
                
            # 5. Combustible Extra
            init_combustible_monto = request.POST.get('init_combustible_monto')
            if init_combustible_monto:
                monto_comb = init_combustible_monto.replace('$', '').replace(',', '').strip()
                if monto_comb:
                    CombustibleExt.objects.create(
                        vehiculo=vehiculo,
                        fecha=request.POST.get('init_combustible_fecha') or None,
                        monto=float(monto_comb)
                    )
            
            messages.success(request, "Vehículo registrado exitosamente con sus datos iniciales.")
            
    except Exception as e:
        messages.error(request, f"Error al guardar el vehículo: {str(e)}")
        
    return redirect('vehiculos_list')


def eliminar_vehiculo(request, vehiculo_id):
    if not request.user.is_authenticated:
        return redirect('/log-in/')
        
    from .models import VehiculosOR
    from django.contrib import messages
    
    user_state = get_user_state(request)
    
    try:
        vehiculo = VehiculosOR.objects.get(id=vehiculo_id)
        if user_state and vehiculo.estado != user_state:
            raise PermissionError("No tienes permisos para eliminar este registro.")
            
        fotos_obj = vehiculo.fotografias
        vehiculo.delete()
        
        # Eliminar registro de fotos física y de BD si existe
        if fotos_obj:
            fotos_obj.delete()
            
        messages.success(request, "Vehículo eliminado exitosamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar el vehículo: {str(e)}")
        
    return redirect('vehiculos_list')


def api_get_vehiculo(request, vehiculo_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)
        
    from .models import VehiculosOR
    user_state = get_user_state(request)
    
    try:
        vehiculo = VehiculosOR.objects.select_related('fotografias').get(id=vehiculo_id)
        if user_state and vehiculo.estado != user_state:
            return JsonResponse({'status': 'error', 'message': 'Sin permisos'}, status=403)
            
        data = {
            'id': vehiculo.id,
            'marca': vehiculo.marca,
            'modelo': vehiculo.modelo,
            'anio': str(vehiculo.anio.year) if vehiculo.anio else '',
            'placa': vehiculo.placa,
            'no_motor': vehiculo.no_motor,
            'tarjeta_asig': vehiculo.tarjeta_asig or '',
            'fecha_disp_comb': vehiculo.fecha_disp_comb.strftime('%Y-%m-%d') if vehiculo.fecha_disp_comb else '',
            'monto': str(vehiculo.monto),
            'tipoVeh_id': vehiculo.tipoVeh_id or '',
            'asignacion_id': vehiculo.asignacion_id,
            'estado_id': vehiculo.estado_id,
            'inmueble_id': vehiculo.inmueble_id or '',
            'fotografias_id': vehiculo.fotografias_id or '',
            'foto_frente_url': vehiculo.fotografias.frente.url if (vehiculo.fotografias and vehiculo.fotografias.frente) else '',
            'foto_lateral_url': vehiculo.fotografias.lateral.url if (vehiculo.fotografias and vehiculo.fotografias.lateral) else '',
            'foto_trasera_url': vehiculo.fotografias.trasera.url if (vehiculo.fotografias and vehiculo.fotografias.trasera) else '',
            'situacion_id': vehiculo.situacion_id or '',
        }
        return JsonResponse({'status': 'success', 'data': data})
    except VehiculosOR.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Vehículo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def api_get_vehiculo_historial(request, vehiculo_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)
        
    from .models import VehiculosOR, Kilometraje, PrestadoDe, Siniestros, Capufe, CombustibleExt
    user_state = get_user_state(request)
    
    try:
        vehiculo = VehiculosOR.objects.get(id=vehiculo_id)
        if user_state and vehiculo.estado != user_state:
            return JsonResponse({'status': 'error', 'message': 'Sin permisos'}, status=403)
            
        kms = Kilometraje.objects.filter(vehiculo_id=vehiculo_id).order_by('-fecha', '-id')
        prestados = PrestadoDe.objects.filter(vehiculo_id=vehiculo_id).select_related('estado', 'inmueble').order_by('-fecha_prestamo')
        siniestros = Siniestros.objects.filter(vehiculo_id=vehiculo_id).order_by('-fecha')
        capufes = Capufe.objects.filter(vehiculo_id=vehiculo_id).order_by('-fecha_inicio')
        combustibles = CombustibleExt.objects.filter(vehiculo_id=vehiculo_id).order_by('-fecha')
        
        data = {
            'vehiculo': {
                'id': vehiculo.id,
                'placa': vehiculo.placa,
                'marca': vehiculo.marca,
                'modelo': vehiculo.modelo,
            },
            'kilometraje': [{
                'id': k.id,
                'fecha': k.fecha.strftime('%Y-%m-%d') if k.fecha else 'S/F',
                'tipo': k.tipo,
                'odometro': str(k.odometro),
                'evidencia_url': k.evidencia.url if k.evidencia else ''
            } for k in kms],
            'prestados': [{
                'id': p.id,
                'fecha_prestamo': p.fecha_prestamo.strftime('%Y-%m-%d') if p.fecha_prestamo else 'S/F',
                'estado': p.estado.nombre,
                'inmueble': p.inmueble.nombre_inmueble if p.inmueble else 'Sin Asignar'
            } for p in prestados],
            'siniestros': [{
                'id': s.id,
                'fecha': s.fecha.strftime('%Y-%m-%d') if s.fecha else 'S/F',
                'folio': s.folio or 'S/F'
            } for s in siniestros],
            'capufes': [{
                'id': c.id,
                'fecha_inicio': c.fecha_inicio.strftime('%Y-%m-%d') if c.fecha_inicio else 'S/F',
                'fecha_termino': c.fecha_termino.strftime('%Y-%m-%d') if c.fecha_termino else 'S/F'
            } for c in capufes],
            'combustibles': [{
                'id': co.id,
                'fecha': co.fecha.strftime('%Y-%m-%d') if co.fecha else 'S/F',
                'monto': str(co.monto)
            } for co in combustibles],
        }
        return JsonResponse({'status': 'success', 'data': data})
    except VehiculosOR.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Vehículo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def guardar_kilometraje(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
        
    from .models import VehiculosOR, Kilometraje
    user_state = get_user_state(request)
    
    try:
        vehiculo_id = request.POST.get('vehiculo_id')
        vehiculo = VehiculosOR.objects.get(id=vehiculo_id)
        if user_state and vehiculo.estado != user_state:
            return JsonResponse({'status': 'error', 'message': 'Sin permisos'}, status=403)
            
        fecha = request.POST.get('fecha') or None
        tipo = request.POST.get('tipo', 'KM')
        odometro = float(request.POST.get('odometro') or 0.0)
        evidencia = request.FILES.get('evidencia')
        
        Kilometraje.objects.create(
            vehiculo=vehiculo,
            fecha=fecha,
            tipo=tipo,
            odometro=odometro,
            evidencia=evidencia
        )
        return JsonResponse({'status': 'success', 'message': 'Kilometraje registrado exitosamente'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def guardar_prestado(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
        
    from .models import VehiculosOR, PrestadoDe
    user_state = get_user_state(request)
    
    try:
        vehiculo_id = request.POST.get('vehiculo_id')
        vehiculo = VehiculosOR.objects.get(id=vehiculo_id)
        if user_state and vehiculo.estado != user_state:
            return JsonResponse({'status': 'error', 'message': 'Sin permisos'}, status=403)
            
        estado_id = request.POST.get('estado_id')
        inmueble_id = request.POST.get('inmueble_id') or None
        fecha_prestamo = request.POST.get('fecha_prestamo') or None
        
        PrestadoDe.objects.create(
            vehiculo=vehiculo,
            estado_id=estado_id,
            inmueble_id=inmueble_id,
            fecha_prestamo=fecha_prestamo
        )
        return JsonResponse({'status': 'success', 'message': 'Préstamo registrado exitosamente'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def guardar_siniestro(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
        
    from .models import VehiculosOR, Siniestros
    user_state = get_user_state(request)
    
    try:
        vehiculo_id = request.POST.get('vehiculo_id')
        vehiculo = VehiculosOR.objects.get(id=vehiculo_id)
        if user_state and vehiculo.estado != user_state:
            return JsonResponse({'status': 'error', 'message': 'Sin permisos'}, status=403)
            
        fecha = request.POST.get('fecha') or None
        folio = request.POST.get('folio', '').strip().upper() or None
        
        Siniestros.objects.create(
            vehiculo=vehiculo,
            fecha=fecha,
            folio=folio
        )
        return JsonResponse({'status': 'success', 'message': 'Siniestro registrado exitosamente'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def guardar_capufe(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
        
    from .models import VehiculosOR, Capufe
    user_state = get_user_state(request)
    
    try:
        vehiculo_id = request.POST.get('vehiculo_id')
        vehiculo = VehiculosOR.objects.get(id=vehiculo_id)
        if user_state and vehiculo.estado != user_state:
            return JsonResponse({'status': 'error', 'message': 'Sin permisos'}, status=403)
            
        fecha_inicio = request.POST.get('fecha_inicio') or None
        fecha_termino = request.POST.get('fecha_termino') or None
        
        Capufe.objects.create(
            vehiculo=vehiculo,
            fecha_inicio=fecha_inicio,
            fecha_termino=fecha_termino
        )
        return JsonResponse({'status': 'success', 'message': 'Registro de Capufe guardado exitosamente'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def guardar_combustible(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
        
    from .models import VehiculosOR, CombustibleExt
    user_state = get_user_state(request)
    
    try:
        vehiculo_id = request.POST.get('vehiculo_id')
        vehiculo = VehiculosOR.objects.get(id=vehiculo_id)
        if user_state and vehiculo.estado != user_state:
            return JsonResponse({'status': 'error', 'message': 'Sin permisos'}, status=403)
            
        fecha = request.POST.get('fecha') or None
        monto_raw = request.POST.get('monto') or '0'
        monto_raw = monto_raw.replace('$', '').replace(',', '').strip()
        monto = float(monto_raw) if monto_raw else 0.0
        
        CombustibleExt.objects.create(
            vehiculo=vehiculo,
            fecha=fecha,
            monto=monto
        )
        return JsonResponse({'status': 'success', 'message': 'Registro de Combustible guardado exitosamente'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

