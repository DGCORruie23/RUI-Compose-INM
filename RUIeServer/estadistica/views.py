from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from collections import Counter
from django.views.decorators.csrf import csrf_exempt

from usuarioL.models import usuarioL
from usuario.models import RescatePunto, EstadoFuerza, PuntosInternacion, Municipios, Paises, Usuario, Inadmitido

from openpyxl import Workbook
from openpyxl import load_workbook


from weasyprint import HTML
from datetime import *
import os

ors_str = [
    "AGUASCALIENTES",
    "BAJA CALIFORNIA",
    "BAJA CALIFORNIA SUR",
    "CAMPECHE",
    "COAHUILA",
    "COLIMA",
    "CHIHUAHUA",
    "CDMX",
    "DURANGO",
    "GUANAJUATO",
    "GUERRERO",
    "HIDALGO",
    "JALISCO",
    "EDOMEX",
    "MICHOACÁN",
    "MORELOS",
    "NAYARIT",
    "NUEVO LEÓN",
    "OAXACA",
    "PUEBLA",
    "QUERÉTARO",
    "QUINTANA ROO",
    "SAN LUIS POTOSÍ",
    "SINALOA",
    "SONORA",
    "TABASCO",
    "TAMAULIPAS",
    "TLAXCALA",
    "VERACRUZ",
    "YUCATÁN",
    "ZACATECAS",
        ]
# Create your views here.
@login_required
def estadistica(request):
    if request.method == 'GET':
        contex = {
            'hoy': date.today().isoformat(),
        }
        return render(request, "estadistica/indexE.html", contex)
    
@login_required
def busqueda(request):
    if request.method == 'GET':
        contex = {
            'hoy': date.today().isoformat(),
        }
        return render(request, "estadistica/buscar.html", contex)
    
@login_required
def reincidencia(request):
    if request.method == 'GET':
        return render(request, "estadistica/reincidentes.html")
    
@login_required
def reincidentes_xdia_ajax(request):
    if request.method == 'GET' and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':

        fecha = request.GET.get('fecha', '')

        # Convertir el formato de llegada a formato de hora
        try:
            fechaIN = datetime.strptime(f"{fecha}", "%Y-%m-%d")
        except ValueError:
            return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)

        array_fechasDia = [(fechaIN + timedelta(days=d)).strftime("%d-%m-%y") for d in range((fechaIN - fechaIN).days + 1)]

        # Rescates por dia de las OR sin chiapas y tabasco (NOTA: tabasco no se excluye en original, solo chiapas)
        rescates_por_dia = RescatePunto.objects.filter(fecha__in= array_fechasDia).exclude(oficinaRepre__in=["CHIAPAS"]) \
            .values('nombre', 'apellidos', 'iso3', 'puntoEstra', 'oficinaRepre', 'fecha', 'sexo', 'fechaNacimiento') \
            .order_by('iso3')

        datosORs = list(rescates_por_dia)

        # Rescates por dia de la OR CHIS
        rescates_por_dia_CHIS = RescatePunto.objects.filter(fecha__in=array_fechasDia, oficinaRepre="CHIAPAS") \
            .values('nombre', 'apellidos', 'iso3', 'puntoEstra', 'oficinaRepre', 'fecha', 'sexo', 'fechaNacimiento') \
            .order_by('iso3')
        
        datosCHIS = list(rescates_por_dia_CHIS)
        total_dia = len(datosORs) + len(datosCHIS)

        # OPTIMIZACION: Extraer solo los nombres, apellidos e iso3 de las personas rescatadas HOY
        # para no tener que buscar duplicados sobre toda la base de datos completa.
        personas_hoy = set()
        for dato in datosORs + datosCHIS:
            # Utilizamos los campos exactos con los que haremos match
            personas_hoy.add((dato['nombre'], dato['apellidos'], dato['iso3']))

        valores_duplicados1year = {}
        
        if personas_hoy:
            # Crear predicados OR para filtrar sólo a este pequeño grupo de personas
            from django.db.models import Q
            query = Q()
            for nombre, apellidos, iso3 in personas_hoy:
                query |= Q(nombre=nombre, apellidos=apellidos, iso3=iso3)

            # Buscar coincidencias exactas y contar cuántas veces han sido rescatadas
            # sólo evaluamos a las personas del día actual
            valores_duplicados = RescatePunto.objects.filter(query) \
                .values('nombre', 'apellidos', 'iso3') \
                .annotate(veces=Count('idRescate')) \
                .filter(veces__gt=1)

            for valor in valores_duplicados:
                valores_duplicados1year[(valor['nombre'], valor['apellidos'], valor['iso3'])] = valor['veces']

        reincidentesOR = []
        rescatesNuevos = []
        
        # Procesamiento unificado de las ORs y Chiapas
        for dato in datosORs + datosCHIS:
            clave = (dato['nombre'], dato['apellidos'], dato['iso3'])
            # Las veces que el ORM encontró coincidencia histórica
            veces = valores_duplicados1year.get(clave, 0)
            
            if veces > 1:
                # Si tiene más de 1 rescate en el histórico, es reincidente
                reincidentesOR.append({**dato, 'veces': veces})
            else:
                # Es primera vez o los datos no empatan (0 o 1 rescate)
                rescatesNuevos.append({**dato, 'veces': 0})

        conteo = len(reincidentesOR)
        
        data = [
            {
                'fecha': fecha,
                'reincidentesOR': reincidentesOR,
                'total_r': total_dia,
                'conteo': conteo,
                'rescatesNuevos': rescatesNuevos,
            }
        ]
        return JsonResponse({'data': data}, safe=False)
    
    return JsonResponse({'error': 'Petición inválida'}, status=400)
    
@login_required
def reincidentes_xfechas_ajax(request):
    if request.method == 'GET' and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':

        fecha1 = request.GET.get('fechaI', '')
        fecha2 = request.GET.get('fechaF', '')

        # Convertir el formato de llegada a formato de hora
        fechaIN = datetime.strptime(f"{fecha1}", "%Y-%m-%d")
        fechaFIN = datetime.strptime(f"{fecha2}", "%Y-%m-%d")

        fechas = f"{fecha1}--{fecha2}"

         # Descomentar para una fecha especifica
        array_fechasDia = [(fechaIN + timedelta(days=d)).strftime("%d-%m-%y") for d in range((fechaFIN - fechaIN).days + 1)]

        # Rescates por dia de las OR sin chiapas y tabasco
        rescates_por_dia = RescatePunto.objects.filter(fecha__in= array_fechasDia).exclude(oficinaRepre__in=["CHIAPAS"]) \
            .values('nombre', 'apellidos', 'nacionalidad', 'puntoEstra', 'oficinaRepre', 'fecha', 'sexo', 'fechaNacimiento', 'numFamilia') \
            .order_by('nacionalidad')

        datosORs = list(rescates_por_dia)

        # Rescates por dia de la OR CHIS
        rescates_por_dia_CHIS = RescatePunto.objects.filter(fecha__in=array_fechasDia, oficinaRepre="CHIAPAS") \
            .values('nombre', 'apellidos', 'nacionalidad', 'puntoEstra', 'oficinaRepre', 'fecha', 'sexo', 'fechaNacimiento', 'numFamilia') \
            .order_by('nacionalidad')
        
        total_dia = rescates_por_dia.count() + rescates_por_dia_CHIS.count()

        datosCHIS = list(rescates_por_dia_CHIS)

    # Valores duplicados desde un año atras
        valores_duplicados = RescatePunto.objects.all() \
            .values('nombre', 'apellidos', 'nacionalidad') \
            .annotate(veces=Count('idRescate')) \
            .filter(veces__gt=1) \
            .order_by('-veces')
        
        # print(valores_duplicados.count())

        valores_duplicados1year = {
            (valor['nombre'], valor['apellidos'], valor['nacionalidad']): valor['veces']
            for valor in valores_duplicados
        }

        # Comparar cada entrada de datos1 con valores_unicos y obtener el valor de veces si existe
        reincidentesOR = []
        rescatesNuevos = []
        for dato in datosORs:
            clave = (dato['nombre'], dato['apellidos'], dato['nacionalidad'])
            veces = valores_duplicados1year.get(clave)  # Buscar en el diccionario
            if veces is not None:
                # print(veces)
                reincidentesOR.append({**dato, 'veces': veces})
            else:
                rescatesNuevos.append({**dato, 'veces': 0})
            # else:
            #     reincidentesOR.append({**dato, 'veces': 1})  # Si no existe, agregar 'veces': 0 o lo que prefieras

        # Comparar cada entrada de datos1 con valores_unicos y obtener el valor de veces si existe
        for dato in datosCHIS:
            clave = (dato['nombre'], dato['apellidos'], dato['nacionalidad'])
            veces = valores_duplicados1year.get(clave)  # Buscar en el diccionario
            if veces is not None:
                # print(veces)
                reincidentesOR.append({**dato, 'veces': veces + 1})
            else:
                reincidentesOR.append({**dato, 'veces': 1})  # Si no existe, agregar 'veces': 0 o lo que prefieras

        conteo = len(reincidentesOR)
        # # Crear el archivo Excel
        # ruta_archivo_excel = os.path.join(os.getcwd(), f'reincidetes_{fechaIN.day:02}_{fechaIN.month:02}_Pais.xlsx')
        
        # print(conteo)

        data = [
            {
                'fecha': fechas,
                'reincidentesOR': reincidentesOR,
                'conteo': conteo,
                'total_r1': total_dia,
                'rescatesNuevos1': rescatesNuevos,
            }
        ]
        return JsonResponse({'data': data}, safe=False)
    
    return JsonResponse({'error': 'Petición inválida'}, status=400)
  

@login_required
def buscar_reincidente_ajax(request):
    if request.method == 'GET' and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        nombre = request.GET.get('nombre', '')
        apellidos = request.GET.get('apellidos', '')
        nacionalidad = request.GET.get('nacionalidad', '')

        rescates = RescatePunto.objects.all()

        rescates = rescates.filter(nombre__icontains=nombre, apellidos__icontains=apellidos, nacionalidad__icontains=nacionalidad)

        # datetime.strptime(f"{rescate.fecha}", "%Y-%m-%d")

        data = [
            {
                'No': indice,
                'fecha': rescate.fecha,
                'oficina': rescate.oficinaRepre,
                'punto': rescate.puntoEstra,
                'nombre': rescate.nombre,
                'apellidos': rescate.apellidos,
                'nacionalidad': rescate.nacionalidad,
            }
            for indice , rescate in enumerate(rescates, start=1)
        ]
        return JsonResponse({'data': data}, safe=False)
    
    return JsonResponse({'error': 'Petición inválida'}, status=400)

@csrf_exempt
@login_required
def generar_pdfT(request):

    # obtenemos la fecha de consulta y el dato de los retornados
    fecha1 = request.POST.get('fechaI', '')
    datoRetorno = request.POST.get('retornos', '')

    # convertimos la fecha en formatos diferente para poder hacer las consultas
    fechaB = datetime.strptime(f"{fecha1}", "%Y-%m-%d")
    fecha = fechaB.strftime("%d/%m/%Y")
    # fechaIN = fechaB.strftime("%d-%m-%y")

    # ---------------------------------------------------------
    # -------------- generacion de consultas ------------------
    # ---------------------------------------------------------


    # -------------- consulta de todos los rescates ------------------

    # Obtenemos los nombres de las oficinas(Estados) de la base de datos
    # estadoF = EstadoFuerza.objects.all().order_by('oficinaR')
    oficinas = EstadoFuerza.objects.values_list("oficinaR", flat=True).distinct().order_by('oficinaR')

    fechaIN = fechaB
    array_fechasDia = [(fechaIN + timedelta(days=d)).strftime("%d-%m-%y") for d in range((fechaIN - fechaIN).days + 1)]

    # obtenemos las oficias
    oficinasSinC = list(oficinas)
    # Quitamos a chiapas para tratarlo de manera diferente
    oficinasSinC.remove('CHIAPAS')

    # Obtener Rescates del dia con todos los parametros
    rescates_por_dia = RescatePunto.objects.filter(fecha__in= array_fechasDia, oficinaRepre__in=oficinasSinC) \
        .exclude(aeropuerto=False, carretero=True, casaSeguridad=False, centralAutobus=False, 
                ferrocarril=False, hotel=False, puestosADispo=False, voluntarios=True, 
                otro=True) \
        .values('nombre', 'apellidos', 'nacionalidad', 'oficinaRepre','puntoEstra','fecha', 'sexo', 'edad', 'numFamilia') \
        .annotate(
            total=Count('idRescate'),
            total_aereos=Count('idRescate', filter=Q(aeropuerto=True)),
            total_carreteros=Count('idRescate', filter=Q(carretero=True)),
            total_central=Count('idRescate', filter=Q(centralAutobus=True)),
            total_ferro=Count('idRescate', filter=Q(ferrocarril=True)),
            total_puestos=Count('idRescate', filter=Q(puestosADispo=True)),
            total_otros=( Count('idRescate', Q(voluntarios=True)) + 
                         Count('idRescate', Q(otro=True)) + 
                         Count('idRescate', filter=Q(aeropuerto=False, carretero=False, centralAutobus=False, ferrocarril=False ,casaSeguridad=False, hotel=False, puestosADispo=False, voluntarios=False, otro=False)) +
                         Count('idRescate', Q(casaSeguridad=True)) + 
                         Count('idRescate', Q(hotel=True))
                         ),
            ) \
        .order_by("oficinaRepre", 'puntoEstra','nacionalidad')

    datosORs = list(rescates_por_dia)

    # Rescates por dia de la OR CHIS con todos los parametros
    rescates_por_dia_CHIS = RescatePunto.objects.filter(fecha__in=array_fechasDia, oficinaRepre="CHIAPAS") \
        .exclude(aeropuerto=False, carretero=True, casaSeguridad=False, centralAutobus=False, 
                ferrocarril=False, hotel=False, puestosADispo=False, voluntarios=True, 
                otro=True) \
        .values('nombre', 'apellidos', 'nacionalidad', 'oficinaRepre','puntoEstra','fecha', 'sexo', 'edad', 'numFamilia', 'idRescate') \
        .annotate(
            total=Count('idRescate'),
            total_aereos=Count('idRescate', filter=Q(aeropuerto=True)),
            total_carreteros=Count('idRescate', filter=Q(carretero=True)),
            total_central=Count('idRescate', filter=Q(centralAutobus=True)),
            total_ferro=Count('idRescate', filter=Q(ferrocarril=True)),
            total_puestos=Count('idRescate', filter=Q(puestosADispo=True)),
            total_otros=( Count('idRescate', Q(voluntarios=True)) + 
                         Count('idRescate', Q(otro=True)) + 
                         Count('idRescate', filter=Q(aeropuerto=False, carretero=False, centralAutobus=False, ferrocarril=False ,casaSeguridad=False, hotel=False, puestosADispo=False, voluntarios=False, otro=False)) +
                         Count('idRescate', Q(casaSeguridad=True)) + 
                         Count('idRescate', Q(hotel=True))
                         ),
            ) \
        .order_by("oficinaRepre", 'puntoEstra','nacionalidad')
    
    
    # rescates_raros = RescatePunto.objects.filter(fecha__in=array_fechasDia, oficinaRepre="CHIAPAS")
    
    # todos_ids = set(rescates_raros.values_list('idRescate', flat=True))
    # unos_ids = set(rescates_por_dia_CHIS.values_list('idRescate', flat=True))

    # print(todos_ids - unos_ids)
    
    datosCHIS = list(rescates_por_dia_CHIS)

    print(f" rescates ors {len(rescates_por_dia)} chis {len(rescates_por_dia_CHIS)}")

    # Valores duplicados desde un año atras
    valores_duplicados = RescatePunto.objects.all() \
        .values('nombre', 'apellidos', 'nacionalidad') \
        .annotate(veces=Count('idRescate')) \
        .filter(veces__gt=1) \
        .order_by('-veces')
    
    # print(valores_duplicados.count())

    valores_duplicados1year = {
        (valor['nombre'], valor['apellidos'], valor['nacionalidad']): valor['veces']
        for valor in valores_duplicados
    }

    # Se calculan los rescates reincidentes y por primera vez
    # Comparar cada entrada de los rescates diarios con valores_duplicados1year 
    # y obtener el valor de veces si existe con todos menos chiapas

    reincidentesOR = []
    rescatesNuevos = []
    rescatesTotales = []
    for dato in datosORs:
        clave = (dato['nombre'], dato['apellidos'], dato['nacionalidad'])
        veces = valores_duplicados1year.get(clave)  # Buscar en el diccionario

        rescatesTotales.append({**dato, 'veces': 1}) # genera los datos completos de las OR

        if veces is not None:
            # print(veces)
            reincidentesOR.append({**dato, 'veces': veces})
        else:
            rescatesNuevos.append({**dato, 'veces': 0})
        # else:
        #     reincidentesOR.append({**dato, 'veces': 1})  # Si no existe, agregar 'veces': 0 o lo que prefieras

    # Comparar cada entrada de los rescates diarios con valores_duplicados1year y obtener el valor de veces si existe 
    for dato in datosCHIS:
        clave = (dato['nombre'], dato['apellidos'], dato['nacionalidad'])
        veces = valores_duplicados1year.get(clave)  # Buscar en el diccionario

        rescatesTotales.append({**dato, 'veces': 1}) # agrega a los datos completos a CHIS

        if veces is not None:
            # print(veces)
            reincidentesOR.append({**dato, 'veces': veces + 1})
        else:
            reincidentesOR.append({**dato, 'veces': 1})  # Si no existe, agregar 'veces': 0 o lo que prefieras

    # ##############################################################################
    #-------================ Datos Informe de Operaciones =================----------
    # ##############################################################################
    
    # ---------------------------------------------------------------------------
    # ------------------ Generamos Datos para la primera tabla ------------------
    
    # Se genera un diccionario para guardar el conteo de datos
    conteo_rescates = {
        nombre: {
            "total": 0,
            "total_aereos": 0,
            "total_carreteros": 0,
            "total_central": 0,
            "total_ferro": 0,
            "total_puestos": 0,
            "total_otros": 0
        }
        for nombre in oficinas
    }

    conteo_rescates["Total"] = {
            "total": 0,
            "total_aereos": 0,
            "total_carreteros": 0,
            "total_central": 0,
            "total_ferro": 0,
            "total_puestos": 0,
            "total_otros": 0
        }

    # Se calcula el total de rescates carreteros, ferroviarios, etc
    # for dato in rescates_por_dia:
    for dato in rescatesNuevos:
        oficina = dato["oficinaRepre"]
        if oficina in conteo_rescates:
            a_aux = dato.get("total", 0)
            b_aux = dato.get("total_aereos", 0)
            c_aux = dato.get("total_carreteros", 0)
            d_aux = dato.get("total_central", 0)
            e_aux = dato.get("total_ferro", 0)
            f_aux = dato.get("total_puestos", 0)
            g_aux = dato.get("total_otros", 0)

            conteo_rescates[oficina]["total"] += a_aux
            conteo_rescates[oficina]["total_aereos"] += b_aux
            conteo_rescates[oficina]["total_carreteros"] += c_aux
            conteo_rescates[oficina]["total_central"] += d_aux
            conteo_rescates[oficina]["total_ferro"] += e_aux
            conteo_rescates[oficina]["total_puestos"] += f_aux
            conteo_rescates[oficina]["total_otros"] += g_aux

            conteo_rescates["Total"]["total"] += a_aux
            conteo_rescates["Total"]["total_aereos"] += b_aux
            conteo_rescates["Total"]["total_carreteros"] += c_aux
            conteo_rescates["Total"]["total_central"] += d_aux
            conteo_rescates["Total"]["total_ferro"] += e_aux
            conteo_rescates["Total"]["total_puestos"] += f_aux
            conteo_rescates["Total"]["total_otros"] += g_aux

    # --------------------------------------------------------------------------
    # ----------------------- Generar Datos segunda tabla ----------------------

    #  Se generan los tablas de las oficinas para agrupar
    reincidentes_oficina = Counter(d["oficinaRepre"] for d in reincidentesOR)
    nuevos_oficina = Counter(d["oficinaRepre"] for d in rescatesNuevos)

    conteo_reincidentes = {
        nombre: {
            "total": 0,
            "total_reincidentes": 0,
            "total_nuevos": 0,
        }
        for nombre in oficinas
    }

    conteo_reincidentes["Total"] = {
            "total": 0,
            "total_reincidentes": 0,
            "total_nuevos": 0,
        }

    for oficina, count in reincidentes_oficina.items():
        if oficina in conteo_reincidentes:
            conteo_reincidentes[oficina]["total_reincidentes"] = count
            conteo_reincidentes['Total']["total_reincidentes"] += count

    for oficina, count in nuevos_oficina.items():
        if oficina in conteo_reincidentes:
            conteo_reincidentes[oficina]["total_nuevos"] = count
            conteo_reincidentes['Total']["total_nuevos"] += count

    for nombre in conteo_reincidentes:
        total_aux = conteo_reincidentes[nombre]['total_reincidentes'] + conteo_reincidentes[nombre]['total_nuevos']
        conteo_reincidentes[nombre]["total"] = total_aux
        conteo_reincidentes['Total']["total"] = total_aux

    # --------------------------------------------------------------------------
    # ------------------------ Generar Datos 3: Tercera tabla ------------------

    nacionalidades_nuevos = {d["nacionalidad"] for d in rescatesNuevos}

    nuevos_datos_nacio = {nacionalidad: {"H_AS": 0, "M_AS": 0, "H_mS": 0, "M_mS": 0, "H_AA": 0, "M_AA": 0, "H_mA": 0, "M_mA": 0, 'total':0 } for nacionalidad in nacionalidades_nuevos}

    for d in rescatesNuevos:
        nuevos_datos_nacio[d["nacionalidad"]]["total"] += 1

        if d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_nacio[d["nacionalidad"]]["H_AS"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_nacio[d["nacionalidad"]]["M_AS"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_nacio[d["nacionalidad"]]["H_mS"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_nacio[d["nacionalidad"]]["M_mS"] += 1
        elif d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] > 0):
            nuevos_datos_nacio[d["nacionalidad"]]["H_AA"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] > 0):
            nuevos_datos_nacio[d["nacionalidad"]]["M_AA"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] > 0):
            nuevos_datos_nacio[d["nacionalidad"]]["H_mA"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] > 0):
            nuevos_datos_nacio[d["nacionalidad"]]["M_mA"] += 1
        else:
            print(d)


    # ----------------------------------------------------------------------
    # ------------------- Tratar Datos 4: Cuarta tabla ---------------------

    nacionalidades_reinc = {d["nacionalidad"] for d in reincidentesOR}

    reincidentes_datos_nacio = {nacionalidad: {"H_AS": 0, "M_AS": 0, "H_mS": 0, "M_mS": 0, "H_AA": 0, "M_AA": 0, "H_mA": 0, "M_mA": 0, 'total':0 } for nacionalidad in nacionalidades_reinc}

    for d in reincidentesOR:
        reincidentes_datos_nacio[d["nacionalidad"]]["total"] += 1

        if d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["H_AS"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["M_AS"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["H_mS"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["M_mS"] += 1
        elif d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] > 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["H_AA"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] > 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["M_AA"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] > 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["H_mA"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] > 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["M_mA"] += 1
        else:
            print(d)

    # ----------------------------------------------------------------------
    # ------------------- Tratar Datos 5: Quinta tabla ---------------------
    # rescates_Inadm = Inadmitido.objects.filter(fecha_hora__date=fechaB)
    
    rescates_Inadm = Inadmitido.objects.filter(fecha_hora__date=fechaB).values("nac", "genero", "edad")

    nacionalidades_inad = {d["nac"] for d in rescates_Inadm}

    inadm_datos_nacio = {nacionalidad: {"H_A": 0, "M_A": 0, "H_m": 0, "M_m": 0, 'total':0 } for nacionalidad in nacionalidades_inad}

    for d in rescates_Inadm:
        inadm_datos_nacio[d["nac"]]["total"] += 1

        if d['genero'] == "H" and d['edad'] >= 18:
            inadm_datos_nacio[d["nac"]]["H_A"] += 1
        elif d['genero'] == "M" and d['edad'] >= 18:
            inadm_datos_nacio[d["nac"]]["M_A"] += 1
        elif d['genero'] == "H" and d['edad'] < 18:
            inadm_datos_nacio[d["nacionalidad"]]["H_m"] += 1
        elif d['genero'] == "M" and d['edad'] < 18:
            inadm_datos_nacio[d["nacionalidad"]]["M_m"] += 1
        else:
            print(d)

    # ##############################################################################
    #-------------================ Datos CUADRO =================----------------
    # ##############################################################################


    # total_Inadm = RescatePunto.objects.filter(fecha__in=array_fechasDia, 
    #             aeropuerto=False, carretero=True, casaSeguridad=False, centralAutobus=False, 
    #             ferrocarril=False, hotel=False, puestosADispo=False, voluntarios=True, 
    #             otro=True) \
    #     .count()
    total_Inadm = rescates_Inadm.count()
    
    conteoReinci = len(reincidentesOR)
    conteoNuevos = len(rescatesNuevos)

    total_Rescates = conteoReinci + total_Inadm + conteoNuevos 

    nacionalidades_nuevos = {d["nacionalidad"] for d in rescatesNuevos}

    nuevos_datos_EM = {nacionalidad: {'total_EM':0} for nacionalidad in nacionalidades_nuevos}
    nuevos_datos_DIF = {nacionalidad: {'total_DIF':0} for nacionalidad in nacionalidades_nuevos}

    for d in rescatesNuevos:

        if d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_EM[d["nacionalidad"]]["total_EM"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_EM[d["nacionalidad"]]["total_EM"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_DIF[d["nacionalidad"]]["total_DIF"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_DIF[d["nacionalidad"]]["total_DIF"] += 1
        elif d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] > 0):
            nuevos_datos_DIF[d["nacionalidad"]]["total_DIF"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] > 0):
            nuevos_datos_DIF[d["nacionalidad"]]["total_DIF"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] > 0):
            nuevos_datos_DIF[d["nacionalidad"]]["total_DIF"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] > 0):
            nuevos_datos_DIF[d["nacionalidad"]]["total_DIF"] += 1
        else:
            print(d)

    res_EM = dict(sorted(nuevos_datos_EM.items(), key=lambda x: x[1]["total_EM"], reverse=True))
    res_DIF = dict(sorted(nuevos_datos_DIF.items(), key=lambda x: x[1]["total_DIF"], reverse=True))

    corteEM = 5
    if len(res_EM) <= 7:
        corteEM = 7

    corteDIF = 5
    if len(res_DIF) <= 7:
        corteDIF = 7

    top5_EM = dict(list(res_EM.items())[:corteEM])
    otros_suma_EM = sum(item["total_EM"] for item in list(res_EM.values())[corteEM:])

    if len(res_EM) > corteEM:
        top5_EM["Otras Nacs."] = {"total_EM": otros_suma_EM}

    total_EM = sum(item["total_EM"] for item in list(top5_EM.values()))
    top5_EM["Total"] = {"total_EM": total_EM}

    top5_DIF = dict(list(res_DIF.items())[:corteDIF])
    otros_suma_DIF = sum(item["total_DIF"] for item in list(res_DIF.values())[corteDIF:])

    if len(res_DIF) > corteDIF:
        top5_DIF["Otras Nacs."] = {"total_DIF": otros_suma_DIF}

    total_DIF = sum(item["total_DIF"] for item in list(top5_DIF.values()))
    top5_DIF["Total"] = {"total_DIF": total_DIF}


    # ##############################################################################
    #-------------================ Datos Para CECO =================----------------
    # ##############################################################################


    # --------------------------------------------------------------------------
    # ------------------------ Rescates por OR y punto  ------------------

    fechaIN = fechaB.strftime("%d-%m-%y")

    ORs_CECO_S = [
        "CAMPECHE",
        "CHIAPAS",
        "HIDALGO",
        "EDOMEX",
        "OAXACA",
        "PUEBLA",
        "QUINTANA ROO",
        "TABASCO",
        "TLAXCALA",
        "VERACRUZ",
        "YUCATÁN",
    ]

    ORs_CECO_N = [
        "BAJA CALIFORNIA",
        "CHIHUAHUA",
        "COAHUILA",
        "DURANGO",
        "NUEVO LEÓN",
        "SAN LUIS POTOSÍ",
        "SINALOA",
        "SONORA",
        "TAMAULIPAS",
    ]

    ORs_CECO_C = [
        "AGUASCALIENTES",
        "BAJA CALIFORNIA SUR",
        "COLIMA",
        "CDMX",
        "GUANAJUATO",
        "GUERRERO",
        "JALISCO",
        "MICHOACÁN",
        "MORELOS",
        "NAYARIT",
        "QUERÉTARO",
        "ZACATECAS",
    ]

    puntoE_totales = {
        nombre: {
            "puntos": {},
            "total": 0
        }
        for nombre in ORs_CECO_S
    }

    for dato in rescatesTotales:
        puntoEOr = dato["puntoEstra"]
        oficinaAux = dato["oficinaRepre"]

        if puntoEOr == '':
            puntoEOr = 'Voluntarios'
         
        if puntoE_totales.get(oficinaAux) is not None:
            if puntoEOr not in puntoE_totales[oficinaAux]['puntos']:
                puntoE_totales[oficinaAux]['puntos'][puntoEOr] = 0

            puntoE_totales[oficinaAux]['puntos'][puntoEOr] += 1

            puntoE_totales[oficinaAux]['total'] += 1

    # puntoE_nuevos = {
    #     nombre: {
    #         "puntos": {},
    #         "total": 0
    #     }
    #     for nombre in ORs_CECO_S
    # }

    # for dato in rescatesNuevos:
    #     puntoEOr = dato["puntoEstra"]
    #     oficinaAux = dato["oficinaRepre"]

    #     if puntoEOr == '':
    #         puntoEOr = 'Voluntarios'
         
    #     if puntoE_nuevos.get(oficinaAux) is not None:
    #         if puntoEOr not in puntoE_nuevos[oficinaAux]['puntos']:
    #             puntoE_nuevos[oficinaAux]['puntos'][puntoEOr] = 0

    #         puntoE_nuevos[oficinaAux]['puntos'][puntoEOr] += 1

    #         puntoE_nuevos[oficinaAux]['total'] += 1

    # puntoE_reinc = {
    #     nombre: {
    #         "puntos": {},
    #         "total": 0
    #     }
    #     for nombre in ORs_CECO_S
    # }

    # for dato in reincidentesOR:
    #     puntoEOr = dato["puntoEstra"]
    #     oficinaAux = dato["oficinaRepre"]

    #     if puntoEOr == '':
    #         puntoEOr = 'Voluntarios'
         
    #     if puntoE_reinc.get(oficinaAux) is not None:
    #         if puntoEOr not in puntoE_reinc[oficinaAux]['puntos']:
    #             puntoE_reinc[oficinaAux]['puntos'][puntoEOr] = 0

    #         puntoE_reinc[oficinaAux]['puntos'][puntoEOr] += 1

    #         puntoE_reinc[oficinaAux]['total'] += 1


    # --------------------------------------------------------------------------
    # ------------------------ Cuadro de rescates por OR del CECO  ------------------

    CECO_ORs_N = {
        nombre: {
            "nuevos": 0,
            "reincidentes": 0,
            "total": 0
        }
        for nombre in ORs_CECO_N
    }
    SubT_CECO_ORs_N = {
            "nuevos": 0,
            "reincidentes": 0,
            "total": 0
        }

    CECO_ORs_C = {
        nombre: {
            "nuevos": 0,
            "reincidentes": 0,
            "total": 0
        }
        for nombre in ORs_CECO_C
    }
    SubT_CECO_ORs_C = {
            "nuevos": 0,
            "reincidentes": 0,
            "total": 0
        }

    CECO_ORs_S = {
        nombre: {
            "nuevos": 0,
            "reincidentes": 0,
            "total": 0
        }
        for nombre in ORs_CECO_S
    }
    SubT_CECO_ORs_S = {
            "nuevos": 0,
            "reincidentes": 0,
            "total": 0
        }
    
    nac_1_reinc = {}
    total_nac_1_reinc = {
                "nuevos": 0,
                "reincidentes": 0,
                "total": 0
            }

    for dato in rescatesNuevos:
        oficinaAux = dato["oficinaRepre"]
        if CECO_ORs_N.get(oficinaAux) is not None:
            CECO_ORs_N[oficinaAux]['nuevos'] += 1
            CECO_ORs_N[oficinaAux]['total'] += 1
            SubT_CECO_ORs_N['nuevos'] += 1
            SubT_CECO_ORs_N['total'] += 1
        elif CECO_ORs_C.get(oficinaAux) is not None:
            CECO_ORs_C[oficinaAux]['nuevos'] += 1
            CECO_ORs_C[oficinaAux]['total'] += 1
            SubT_CECO_ORs_C['nuevos'] += 1
            SubT_CECO_ORs_C['total'] += 1
        elif CECO_ORs_S.get(oficinaAux) is not None:
            CECO_ORs_S[oficinaAux]['nuevos'] += 1
            CECO_ORs_S[oficinaAux]['total'] += 1
            SubT_CECO_ORs_S['nuevos'] += 1
            SubT_CECO_ORs_S['total'] += 1
        else:
            pass

        nacionalidadN = str(dato["nacionalidad"]).upper()

        if nacionalidadN not in nac_1_reinc:
            nac_1_reinc[nacionalidadN] = {
                "nuevos": 0,
                "reincidentes": 0,
                "total": 0
            }
        nac_1_reinc[nacionalidadN]['nuevos'] += 1
        nac_1_reinc[nacionalidadN]['total'] += 1

        total_nac_1_reinc['nuevos'] += 1
        total_nac_1_reinc['total'] += 1


    
    for dato in reincidentesOR:
        oficinaAux = dato["oficinaRepre"]
        if CECO_ORs_N.get(oficinaAux) is not None:
            CECO_ORs_N[oficinaAux]['reincidentes'] += 1
            CECO_ORs_N[oficinaAux]['total'] += 1
            SubT_CECO_ORs_N['reincidentes'] += 1
            SubT_CECO_ORs_N['total'] += 1
        elif CECO_ORs_C.get(oficinaAux) is not None:
            CECO_ORs_C[oficinaAux]['reincidentes'] += 1
            CECO_ORs_C[oficinaAux]['total'] += 1
            SubT_CECO_ORs_C['reincidentes'] += 1
            SubT_CECO_ORs_C['total'] += 1
        elif CECO_ORs_S.get(oficinaAux) is not None:
            CECO_ORs_S[oficinaAux]['reincidentes'] += 1
            CECO_ORs_S[oficinaAux]['total'] += 1
            SubT_CECO_ORs_S['reincidentes'] += 1
            SubT_CECO_ORs_S['total'] += 1
        else:
            pass

        nacionalidadN = str(dato["nacionalidad"]).upper()

        if nacionalidadN not in nac_1_reinc:
            nac_1_reinc[nacionalidadN] = {
                "nuevos": 0,
                "reincidentes": 0,
                "total": 0
            }
        nac_1_reinc[nacionalidadN]['reincidentes'] += 1
        nac_1_reinc[nacionalidadN]['total'] += 1

        total_nac_1_reinc['reincidentes'] += 1
        total_nac_1_reinc['total'] += 1
    
    # --------------------------------------------------------------------------
    # ------------------------ Rescates por OR y nacionalidad  ------------------

    conteo_nacionalidadN = { nombre: {} for nombre in oficinas }

    for d in rescatesNuevos:
        # print(d)
        oficinaR=d["oficinaRepre"]
        nacionalidad = d["nacionalidad"]

        if conteo_nacionalidadN.get(oficinaR) is not None:
            if nacionalidad not in conteo_nacionalidadN[oficinaR]:
                conteo_nacionalidadN[oficinaR][nacionalidad] = {"H_AS": 0, "M_AS": 0, "H_mS": 0, "M_mS": 0, "H_AA": 0, "M_AA": 0, "H_mA": 0, "M_mA": 0, 'total':0 }

            conteo_nacionalidadN[oficinaR][nacionalidad]["total"] +=1

            # print(d)

            if d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
                conteo_nacionalidadN[oficinaR][nacionalidad]["H_AS"] += 1
            elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
                conteo_nacionalidadN[oficinaR][nacionalidad]["M_AS"] += 1
            elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
                conteo_nacionalidadN[oficinaR][nacionalidad]["H_mS"] += 1
            elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
                conteo_nacionalidadN[oficinaR][nacionalidad]["M_mS"] += 1
            elif d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] > 0):
                conteo_nacionalidadN[oficinaR][nacionalidad]["H_AA"] += 1
            elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] > 0):
                conteo_nacionalidadN[oficinaR][nacionalidad]["M_AA"] += 1
            elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] > 0):
                conteo_nacionalidadN[oficinaR][nacionalidad]["H_mA"] += 1
            elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] > 0):
                conteo_nacionalidadN[oficinaR][nacionalidad]["M_mA"] += 1
            else:
                print(d)

    conteo_nacionalidadT = { nombre: {} for nombre in oficinas }

    for d in rescatesTotales:
        # print(d)
        oficinaR=d["oficinaRepre"]
        nacionalidad = d["nacionalidad"]

        if conteo_nacionalidadT.get(oficinaR) is not None:
            if nacionalidad not in conteo_nacionalidadT[oficinaR]:
                conteo_nacionalidadT[oficinaR][nacionalidad] = {"H_AS": 0, "M_AS": 0, "H_mS": 0, "M_mS": 0, "H_AA": 0, "M_AA": 0, "H_mA": 0, "M_mA": 0, 'total':0 }

            conteo_nacionalidadT[oficinaR][nacionalidad]["total"] +=1

            # print(d)

            if d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
                conteo_nacionalidadT[oficinaR][nacionalidad]["H_AS"] += 1
            elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
                conteo_nacionalidadT[oficinaR][nacionalidad]["M_AS"] += 1
            elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
                conteo_nacionalidadT[oficinaR][nacionalidad]["H_mS"] += 1
            elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
                conteo_nacionalidadT[oficinaR][nacionalidad]["M_mS"] += 1
            elif d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] > 0):
                conteo_nacionalidadT[oficinaR][nacionalidad]["H_AA"] += 1
            elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] > 0):
                conteo_nacionalidadT[oficinaR][nacionalidad]["M_AA"] += 1
            elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] > 0):
                conteo_nacionalidadT[oficinaR][nacionalidad]["H_mA"] += 1
            elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] > 0):
                conteo_nacionalidadT[oficinaR][nacionalidad]["M_mA"] += 1
            else:
                print(d)

    
    # conteo_nacionalidadR = { nombre: {} for nombre in oficinas }

    # for d in reincidentesOR:
    #     # print(d)
    #     oficinaR=d["oficinaRepre"]
    #     nacionalidad = d["nacionalidad"]

    #     if conteo_nacionalidadR.get(oficinaR) is not None:
    #         if nacionalidad not in conteo_nacionalidadR[oficinaR]:
    #             conteo_nacionalidadR[oficinaR][nacionalidad] = {"H_AS": 0, "M_AS": 0, "H_mS": 0, "M_mS": 0, "H_AA": 0, "M_AA": 0, "H_mA": 0, "M_mA": 0, 'total':0 }

    #         conteo_nacionalidadR[oficinaR][nacionalidad]["total"] +=1

    #         # print(d)

    #         if d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
    #             conteo_nacionalidadR[oficinaR][nacionalidad]["H_AS"] += 1
    #         elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
    #             conteo_nacionalidadR[oficinaR][nacionalidad]["M_AS"] += 1
    #         elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
    #             conteo_nacionalidadR[oficinaR][nacionalidad]["H_mS"] += 1
    #         elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
    #             conteo_nacionalidadR[oficinaR][nacionalidad]["M_mS"] += 1
    #         elif d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] > 0):
    #             conteo_nacionalidadR[oficinaR][nacionalidad]["H_AA"] += 1
    #         elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] > 0):
    #             conteo_nacionalidadR[oficinaR][nacionalidad]["M_AA"] += 1
    #         elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] > 0):
    #             conteo_nacionalidadR[oficinaR][nacionalidad]["H_mA"] += 1
    #         elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] > 0):
    #             conteo_nacionalidadR[oficinaR][nacionalidad]["M_mA"] += 1
    #         else:
    #             print(d)

    
    # Crear el contexto con los datos
    context = {
        "fecha_actual": fecha,
        "dato": datoRetorno,
        "rescates": conteo_rescates,
        "reincidentes": conteo_reincidentes,
        "nacionalidades": dict(sorted(nuevos_datos_nacio.items(), key=lambda x: x[1]["total"], reverse=True)),
        "nacionalidades_re": dict(sorted(reincidentes_datos_nacio.items(), key=lambda x: x[1]["total"], reverse=True)),

        "nacionalidades_inad": dict(sorted(inadm_datos_nacio.items(), key=lambda x: x[1]["total"], reverse=True)),

        # "rescOR_puntoN": puntoE_nuevos,
        # "rescOR_puntoR": puntoE_reinc,
        "rescOR_puntoT": puntoE_totales,
        "rescOR_nacN": conteo_nacionalidadN,
        "rescOR_nacT": conteo_nacionalidadT,

        "fecha": fechaB,
        "rescatados": total_Rescates,
        "reincidentesC": conteoReinci,
        "subtotal1": total_Rescates - conteoReinci,
        "inadmitidos": total_Inadm,
        "subtotal2": total_Rescates - conteoReinci - total_Inadm,
        "retornados": 0,
        "rescates_nuevos": conteoNuevos,
        "rescates_EM": top5_EM,
        "rescates_DIF": top5_DIF,
        "EM_total": total_EM,
        "DIF_total": total_DIF,

        "CECO_N": dict(sorted(CECO_ORs_N.items(), key=lambda x: x[1]["total"], reverse=True)),
        "CECO_C": dict(sorted(CECO_ORs_C.items(), key=lambda x: x[1]["total"], reverse=True)),
        "CECO_S": dict(sorted(CECO_ORs_S.items(), key=lambda x: x[1]["total"], reverse=True)),
        "Sub_CECO_N": SubT_CECO_ORs_N,
        "Sub_CECO_C": SubT_CECO_ORs_C,
        "Sub_CECO_S": SubT_CECO_ORs_S,
        "Nac_1_Rein": dict(sorted(nac_1_reinc.items(), key=lambda x: x[1]["total"], reverse=True)),
        "Total_Nac_1_Rein": total_nac_1_reinc,
    }

    return render(request, "estadistica/reporteA_js.html", context)


@login_required
def generar_pdf(request):

    fecha1 = request.POST.get('fechaI', '')

    datoRetorno = request.POST.get('retornos', '')
    # print(fecha1)
    # fecha a elegir
    fechaB = datetime.strptime(f"{fecha1}", "%Y-%m-%d")

    # estadoF = EstadoFuerza.objects.all().order_by('oficinaR')
    # Obtener los datos de la base de datos
    oficinas = EstadoFuerza.objects.values_list("oficinaR", flat=True).distinct().order_by('oficinaR')
    fecha = fechaB.strftime("%d/%m/%Y")
    fechaIN = fechaB.strftime("%d-%m-%y")

    rescates_por_dia = RescatePunto.objects.filter(fecha=fechaIN)\
        .values("oficinaRepre")\
        .annotate(
            total=Count('idRescate'),
            total_aereos=Count('idRescate', filter=Q(aeropuerto=True)),
            total_carreteros=Count('idRescate', filter=Q(carretero=True)),
            total_central=Count('idRescate', filter=Q(centralAutobus=True)),
            total_ferro=Count('idRescate', filter=Q(ferrocarril=True)),
            total_puestos=Count('idRescate', filter=Q(puestosADispo=True)),
            total_otros=Count('idRescate', Q(voluntarios=True)) + Count('idRescate', Q(otro=True)) + Count('idRescate', filter=Q(aeropuerto=False, carretero=False, centralAutobus=False, ferrocarril=False ,casaSeguridad=False, hotel=False, puestosADispo=False, voluntarios=False, otro=False)),
            ) \
        .order_by('oficinaRepre')
    
    # total_otros=Count('idRescate', filter=Q(casaSeguridad=True)) + Count('idRescate', Q(hotel=True)) + Count('idRescate', Q(puestosADispo=True)) + Count('idRescate', Q(voluntarios=True)) + Count('idRescate', Q(otro=True)),
    
    conteo_rescates = {
        nombre: {
            "total": 0,
            "total_aereos": 0,
            "total_carreteros": 0,
            "total_central": 0,
            "total_ferro": 0,
            "total_puestos": 0,
            "total_otros": 0
        }
        for nombre in oficinas
    }

    conteo_rescates["Total"] = {
            "total": 0,
            "total_aereos": 0,
            "total_carreteros": 0,
            "total_central": 0,
            "total_ferro": 0,
            "total_puestos": 0,
            "total_otros": 0
        }


    # print(conteo_rescates)

    for dato in rescates_por_dia:
        oficina = dato["oficinaRepre"]
        if oficina in conteo_rescates:
            a_aux = dato.get("total", 0)
            b_aux = dato.get("total_aereos", 0)
            c_aux = dato.get("total_carreteros", 0)
            d_aux = dato.get("total_central", 0)
            e_aux = dato.get("total_ferro", 0)
            f_aux = dato.get("total_puestos", 0)
            g_aux = dato.get("total_otros", 0)

            conteo_rescates[oficina]["total"] = a_aux
            conteo_rescates[oficina]["total_aereos"] = b_aux
            conteo_rescates[oficina]["total_carreteros"] = c_aux
            conteo_rescates[oficina]["total_central"] = d_aux
            conteo_rescates[oficina]["total_ferro"] = e_aux
            conteo_rescates[oficina]["total_puestos"] = f_aux
            conteo_rescates[oficina]["total_otros"] = g_aux

            conteo_rescates["Total"]["total"] += a_aux
            conteo_rescates["Total"]["total_aereos"] += b_aux
            conteo_rescates["Total"]["total_carreteros"] += c_aux
            conteo_rescates["Total"]["total_central"] += d_aux
            conteo_rescates["Total"]["total_ferro"] += e_aux
            conteo_rescates["Total"]["total_puestos"] += f_aux
            conteo_rescates["Total"]["total_otros"] += g_aux

    # -------------- Datos segunda tabla ------------------

    fechaIN = fechaB
    array_fechasDia = [(fechaIN + timedelta(days=d)).strftime("%d-%m-%y") for d in range((fechaIN - fechaIN).days + 1)]

    # Rescates por dia de las OR sin chiapas y tabasco
    rescates_por_dia = RescatePunto.objects.filter(fecha__in= array_fechasDia).exclude(oficinaRepre__in=["CHIAPAS"]) \
        .values('nombre', 'apellidos', 'nacionalidad', 'oficinaRepre','fecha', 'sexo', 'edad', 'numFamilia') \
        .order_by('nacionalidad')

    datosORs = list(rescates_por_dia)

    # Rescates por dia de la OR CHIS
    rescates_por_dia_CHIS = RescatePunto.objects.filter(fecha__in=array_fechasDia, oficinaRepre="CHIAPAS") \
        .values('nombre', 'apellidos', 'nacionalidad', 'oficinaRepre','fecha', 'sexo', 'edad', 'numFamilia') \
        .order_by('nacionalidad')
    
    total_dia = rescates_por_dia.count() + rescates_por_dia_CHIS.count()

    datosCHIS = list(rescates_por_dia_CHIS)

    # Valores duplicados desde un año atras
    valores_duplicados = RescatePunto.objects.all() \
        .values('nombre', 'apellidos', 'nacionalidad') \
        .annotate(veces=Count('idRescate')) \
        .filter(veces__gt=1) \
        .order_by('-veces')
    
    # print(valores_duplicados.count())

    valores_duplicados1year = {
        (valor['nombre'], valor['apellidos'], valor['nacionalidad']): valor['veces']
        for valor in valores_duplicados
    }

    # Comparar cada entrada de datos1 con valores_unicos y obtener el valor de veces si existe
    reincidentesOR = []
    rescatesNuevos = []
    for dato in datosORs:
        clave = (dato['nombre'], dato['apellidos'], dato['nacionalidad'])
        veces = valores_duplicados1year.get(clave)  # Buscar en el diccionario
        if veces is not None:
            # print(veces)
            reincidentesOR.append({**dato, 'veces': veces})
        else:
            rescatesNuevos.append({**dato, 'veces': 0})
        # else:
        #     reincidentesOR.append({**dato, 'veces': 1})  # Si no existe, agregar 'veces': 0 o lo que prefieras

    # Comparar cada entrada de datos1 con valores_unicos y obtener el valor de veces si existe
    for dato in datosCHIS:
        clave = (dato['nombre'], dato['apellidos'], dato['nacionalidad'])
        veces = valores_duplicados1year.get(clave)  # Buscar en el diccionario
        if veces is not None:
            # print(veces)
            reincidentesOR.append({**dato, 'veces': veces + 1})
        else:
            reincidentesOR.append({**dato, 'veces': 1})  # Si no existe, agregar 'veces': 0 o lo que prefieras

    #  Se generan los tablas de las oficinas para agrupar
    reincidentes_oficina = Counter(d["oficinaRepre"] for d in reincidentesOR)
    nuevos_oficina = Counter(d["oficinaRepre"] for d in rescatesNuevos)

    conteo_reincidentes = {
        nombre: {
            "total": 0,
            "total_reincidentes": 0,
            "total_nuevos": 0,
        }
        for nombre in oficinas
    }

    conteo_reincidentes["Total"] = {
            "total": 0,
            "total_reincidentes": 0,
            "total_nuevos": 0,
        }

    for oficina, count in reincidentes_oficina.items():
        if oficina in conteo_reincidentes:
            conteo_reincidentes[oficina]["total_reincidentes"] = count
            conteo_reincidentes['Total']["total_reincidentes"] += count

    for oficina, count in nuevos_oficina.items():
        if oficina in conteo_reincidentes:
            conteo_reincidentes[oficina]["total_nuevos"] = count
            conteo_reincidentes['Total']["total_nuevos"] += count

    for nombre in conteo_reincidentes:
        total_aux = conteo_reincidentes[nombre]['total_reincidentes'] + conteo_reincidentes[nombre]['total_nuevos']
        conteo_reincidentes[nombre]["total"] = total_aux
        conteo_reincidentes['Total']["total"] = total_aux

    # -------------- Datos 3: Tercera tabla ------------------
    # print("llego 3ra tabla")

    nacionalidades_nuevos = {d["nacionalidad"] for d in rescatesNuevos}

    nuevos_datos_nacio = {nacionalidad: {"H_AS": 0, "M_AS": 0, "H_mS": 0, "M_mS": 0, "H_AA": 0, "M_AA": 0, "H_mA": 0, "M_mA": 0, 'total':0 } for nacionalidad in nacionalidades_nuevos}

    for d in rescatesNuevos:
        nuevos_datos_nacio[d["nacionalidad"]]["total"] += 1

        if d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_nacio[d["nacionalidad"]]["H_AS"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_nacio[d["nacionalidad"]]["M_AS"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_nacio[d["nacionalidad"]]["H_mS"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_nacio[d["nacionalidad"]]["M_mS"] += 1
        elif d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] > 0):
            nuevos_datos_nacio[d["nacionalidad"]]["H_AA"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] > 0):
            nuevos_datos_nacio[d["nacionalidad"]]["M_AA"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] > 0):
            nuevos_datos_nacio[d["nacionalidad"]]["H_mA"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] > 0):
            nuevos_datos_nacio[d["nacionalidad"]]["M_mA"] += 1
        else:
            print(d)


    # -------------- Datos 4: Cuarta tabla ------------------

    nacionalidades_reinc = {d["nacionalidad"] for d in reincidentesOR}

    reincidentes_datos_nacio = {nacionalidad: {"H_AS": 0, "M_AS": 0, "H_mS": 0, "M_mS": 0, "H_AA": 0, "M_AA": 0, "H_mA": 0, "M_mA": 0, 'total':0 } for nacionalidad in nacionalidades_reinc}

    for d in reincidentesOR:
        reincidentes_datos_nacio[d["nacionalidad"]]["total"] += 1

        if d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["H_AS"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["M_AS"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["H_mS"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["M_mS"] += 1
        elif d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] > 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["H_AA"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] > 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["M_AA"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] > 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["H_mA"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] > 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["M_mA"] += 1
        else:
            print(d)

    
    # Crear el contexto con los datos
    context = {
        "fecha_actual": fecha,
        "dato": datoRetorno,
        "rescates": conteo_rescates,
        "reincidentes": conteo_reincidentes,
        "nacionalidades": dict(sorted(nuevos_datos_nacio.items(), key=lambda x: x[1]["total"], reverse=True)),
        "nacionalidades_re": dict(sorted(reincidentes_datos_nacio.items(), key=lambda x: x[1]["total"], reverse=True)),
    }

    # Renderizar el template HTML con los datos
    template = get_template("estadistica/reporteA.html")
    html_string = template.render(context)

    # Crear el PDF con WeasyPrint
    pdf_file = HTML(string=html_string).write_pdf()

    # Devolver el PDF como respuesta HTTP
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="reporte_Diario.pdf"'
    return response


@login_required
def generar_pdf_ceco(request):

    fecha1 = request.POST.get('fechaI', '')

    fechaB = datetime.strptime(f"{fecha1}", "%Y-%m-%d")

    # oficinas = EstadoFuerza.objects.values_list("oficinaR", flat=True).distinct().order_by('oficinaR')

    fechaIN = fechaB.strftime("%d-%m-%y")

    ORs_CECO_ = [
        "CAMPECHE",
        "CHIAPAS",
        "HIDALGO",
        "EDOMEX",
        "OAXACA",
        "PUEBLA",
        "QUINTANA ROO",
        "TABASCO",
        "TLAXCALA",
        "VERACRUZ",
        "YUCATÁN",
    ]

    rescates_or_punto = RescatePunto.objects.filter(fecha=fechaIN)\
        .values("oficinaRepre", 'puntoEstra')\
        .annotate(
            total=Count('idRescate'))\
        .order_by("oficinaRepre", 'puntoEstra')
    

    conteo_oficina = { nombre: {} for nombre in ORs_CECO_ }

    for dato in rescates_or_punto:
        puntoE = dato["puntoEstra"]
        if puntoE == '':
            puntoE = 'Voluntarios'
        try:
            conteo_oficina[dato["oficinaRepre"]][puntoE] = dato["total"]
        except:
            pass


    rescates_or_nacionalidad = RescatePunto.objects.filter(fecha=fechaIN)\
        .values("oficinaRepre", 'nacionalidad', 'sexo', 'edad', 'numFamilia')\
        .order_by("oficinaRepre", 'nacionalidad')
    
    conteo_nacionalidad = { nombre: {} for nombre in ORs_CECO_ }

    for d in rescates_or_nacionalidad:
        # print(d)
        oficinaR=d["oficinaRepre"]
        nacionalidad = d["nacionalidad"]

        # print(d)

        try:
            if nacionalidad not in list(conteo_nacionalidad[oficinaR].keys()):
                conteo_nacionalidad[oficinaR][nacionalidad] = {"H_AS": 0, "M_AS": 0, "H_mS": 0, "M_mS": 0, "H_AA": 0, "M_AA": 0, "H_mA": 0, "M_mA": 0, 'total':0 }
            
            conteo_nacionalidad[oficinaR][nacionalidad]["total"] +=1

            # print(d)

            if d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
                conteo_nacionalidad[oficinaR][nacionalidad]["H_AS"] += 1
            elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
                conteo_nacionalidad[oficinaR][nacionalidad]["M_AS"] += 1
            elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
                conteo_nacionalidad[oficinaR][nacionalidad]["H_mS"] += 1
            elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
                conteo_nacionalidad[oficinaR][nacionalidad]["M_mS"] += 1
            elif d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] > 0):
                conteo_nacionalidad[oficinaR][nacionalidad]["H_AA"] += 1
            elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] > 0):
                conteo_nacionalidad[oficinaR][nacionalidad]["M_AA"] += 1
            elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] > 0):
                conteo_nacionalidad[oficinaR][nacionalidad]["H_mA"] += 1
            elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] > 0):
                conteo_nacionalidad[oficinaR][nacionalidad]["M_mA"] += 1
            else:
                print(d)
        except:
            pass
    
    # print(conteo_nacionalidad)

    context = {
        "fecha_actual": fecha1,
        "rescOR_punto": conteo_oficina,
        "rescOR_nac": conteo_nacionalidad,
    }

    # Renderizar el template HTML con los datos
    template = get_template("estadistica/reporteCECO.html")
    html_string = template.render(context)

    # Crear el PDF con WeasyPrint
    pdf_file = HTML(string=html_string).write_pdf()

    # Devolver el PDF como respuesta HTTP
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="reporteCECO.pdf"'
    return response


@login_required
def generar_cuadro_diario(request):

    fecha1 = request.POST.get('fechaI', '')

    fechaB = datetime.strptime(f"{fecha1}", "%Y-%m-%d")

    # oficinas = EstadoFuerza.objects.values_list("oficinaR", flat=True).distinct().order_by('oficinaR')

    fechaIN = fechaB

    array_fechasDia = [(fechaIN + timedelta(days=d)).strftime("%d-%m-%y") for d in range((fechaIN - fechaIN).days + 1)]

    # Rescates por dia de las OR sin chiapas y tabasco
    rescates_por_dia = RescatePunto.objects.filter(fecha__in= array_fechasDia, oficinaRepre__in=ors_str) \
        .exclude(aeropuerto=False, carretero=False, casaSeguridad=False, centralAutobus=False, 
                 ferrocarril=False, hotel=False, puestosADispo=False, voluntarios=False, 
                 otro=False) \
        .values('nombre', 'apellidos', 'nacionalidad', 'sexo', 'edad', 'numFamilia') \
        .order_by('nacionalidad')

    datosORs = list(rescates_por_dia)

    # Rescates por dia de la OR CHIS
    rescates_por_dia_CHIS = RescatePunto.objects.filter(fecha__in=array_fechasDia, oficinaRepre="CHIAPAS") \
        .exclude(aeropuerto=False, carretero=False, casaSeguridad=False, centralAutobus=False, 
                 ferrocarril=False, hotel=False, puestosADispo=False, voluntarios=False, 
                 otro=False) \
        .values('nombre', 'apellidos', 'nacionalidad', 'puntoEstra', 'oficinaRepre', 'fecha', 'sexo', 'fechaNacimiento') \
        .order_by('nacionalidad')
    
    total_dia = rescates_por_dia.count() + rescates_por_dia_CHIS.count()

    print(rescates_por_dia.count())
    print(rescates_por_dia_CHIS.count())

    datosCHIS = list(rescates_por_dia_CHIS)

    # Valores duplicados desde un año atras
    valores_duplicados = RescatePunto.objects.all() \
        .exclude(aeropuerto=False, carretero=False, casaSeguridad=False, centralAutobus=False, 
                 ferrocarril=False, hotel=False, puestosADispo=False, voluntarios=False, 
                 otro=False ) \
        .values('nombre', 'apellidos', 'nacionalidad') \
        .annotate(veces=Count('idRescate')) \
        .filter(veces__gt=1) \
        .order_by('-veces')
    
    # print(valores_duplicados.count()) 

    valores_duplicados1year = {
        (valor['nombre'], valor['apellidos'], valor['nacionalidad']): valor['veces']
        for valor in valores_duplicados
    }


    reincidentesOR = []
    rescatesNuevos = []
    for dato in datosORs:
        clave = (dato['nombre'], dato['apellidos'], dato['nacionalidad'])
        veces = valores_duplicados1year.get(clave)  # Buscar en el diccionario
        if veces is not None:
            # print(veces)
            reincidentesOR.append({**dato, 'veces': veces})
        else:
            rescatesNuevos.append({**dato, 'veces': 0})

    for dato in datosCHIS:
        clave = (dato['nombre'], dato['apellidos'], dato['nacionalidad'])
        veces = valores_duplicados1year.get(clave)  # Buscar en el diccionario
        if veces is not None:
            # print(veces)
            reincidentesOR.append({**dato, 'veces': veces + 1})
        else:
            reincidentesOR.append({**dato, 'veces': 1})  # Si no existe, agregar 'veces': 0 o lo que prefieras

    total_Inadm = RescatePunto.objects.filter(fecha__in=array_fechasDia, aeropuerto=False, carretero=False, 
                casaSeguridad=False, centralAutobus=False, ferrocarril=False, hotel=False, 
                puestosADispo=False, voluntarios=False, otro=False ) \
        .count()
    
    conteoReinci = len(reincidentesOR)
    conteoNuevos = len(rescatesNuevos)

    total_Rescates = conteoReinci + total_Inadm + conteoNuevos 

    nacionalidades_nuevos = {d["nacionalidad"] for d in rescatesNuevos}

    nuevos_datos_EM = {nacionalidad: {'total_EM':0} for nacionalidad in nacionalidades_nuevos}
    nuevos_datos_DIF = {nacionalidad: {'total_DIF':0} for nacionalidad in nacionalidades_nuevos}

    for d in rescatesNuevos:

        if d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_EM[d["nacionalidad"]]["total_EM"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_EM[d["nacionalidad"]]["total_EM"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_DIF[d["nacionalidad"]]["total_DIF"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_DIF[d["nacionalidad"]]["total_DIF"] += 1
        elif d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] > 0):
            nuevos_datos_DIF[d["nacionalidad"]]["total_DIF"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] > 0):
            nuevos_datos_DIF[d["nacionalidad"]]["total_DIF"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] > 0):
            nuevos_datos_DIF[d["nacionalidad"]]["total_DIF"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] > 0):
            nuevos_datos_DIF[d["nacionalidad"]]["total_DIF"] += 1
        else:
            print(d)

    res_EM = dict(sorted(nuevos_datos_EM.items(), key=lambda x: x[1]["total_EM"], reverse=True))
    res_DIF = dict(sorted(nuevos_datos_DIF.items(), key=lambda x: x[1]["total_DIF"], reverse=True))

    corteEM = 5
    if len(res_EM) <= 7:
        corteEM = 7

    corteDIF = 5
    if len(res_DIF) <= 7:
        corteDIF = 7

    top5_EM = dict(list(res_EM.items())[:corteEM])
    otros_suma_EM = sum(item["total_EM"] for item in list(res_EM.values())[corteEM:])

    if len(res_EM) > corteEM:
        top5_EM["Otras Nacs."] = {"total_EM": otros_suma_EM}

    total_EM = sum(item["total_EM"] for item in list(top5_EM.values()))
    top5_EM["Total"] = {"total_EM": total_EM}

    top5_DIF = dict(list(res_DIF.items())[:corteDIF])
    otros_suma_DIF = sum(item["total_DIF"] for item in list(res_DIF.values())[corteDIF:])

    if len(res_DIF) > corteDIF:
        top5_DIF["Otras Nacs."] = {"total_DIF": otros_suma_DIF}

    total_DIF = sum(item["total_DIF"] for item in list(top5_DIF.values()))
    top5_DIF["Total"] = {"total_DIF": total_DIF}


    context = {
        "fecha": fechaB.strftime("%d %b %Y"),
        "rescatados": total_Rescates,
        "reincidentes": conteoReinci,
        "subtotal1": total_Rescates - conteoReinci,
        "inadmitidos": total_Inadm,
        "subtotal2": total_Rescates - conteoReinci - total_Inadm,
        "retornados": 0,
        "rescates_nuevos": conteoNuevos,
        "rescates_EM": top5_EM,
        "rescates_DIF": top5_DIF,
        "EM_total": total_EM,
        "DIF_total": total_DIF,
    }

    # Renderizar el template HTML con los datos
    template = get_template("estadistica/cuadroDATOS.html")
    html_string = template.render(context)

    # Crear el PDF con WeasyPrint
    pdf_file = HTML(string=html_string).write_pdf()

    # Devolver el PDF como respuesta HTTP
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="cuadro_datos.pdf"'
    return response

@csrf_exempt
@login_required
def exportar_excel_reporteT(request):
    # obtenemos la fecha de consulta y el dato de los retornados
    fecha1 = request.POST.get('fechaI', '')
    datoRetorno = request.POST.get('retornos', '')

    # convertimos la fecha en formatos diferente para poder hacer las consultas
    fechaB = datetime.strptime(f"{fecha1}", "%Y-%m-%d")
    fecha = fechaB.strftime("%d/%m/%Y")
    
    # ---------------------------------------------------------
    # -------------- Copia de logica de generar_pdfT ----------
    # ---------------------------------------------------------

    oficinas = EstadoFuerza.objects.values_list("oficinaR", flat=True).distinct().order_by('oficinaR')

    fechaIN = fechaB
    array_fechasDia = [(fechaIN + timedelta(days=d)).strftime("%d-%m-%y") for d in range((fechaIN - fechaIN).days + 1)]

    oficinasSinC = list(oficinas)
    
    if 'CHIAPAS' in oficinasSinC:
        oficinasSinC.remove('CHIAPAS')

    rescates_por_dia = RescatePunto.objects.filter(fecha__in= array_fechasDia, oficinaRepre__in=oficinasSinC) \
        .exclude(aeropuerto=False, carretero=True, casaSeguridad=False, centralAutobus=False, 
                ferrocarril=False, hotel=False, puestosADispo=False, voluntarios=True, 
                otro=True) \
        .values('nombre', 'apellidos', 'nacionalidad', 'oficinaRepre','puntoEstra','fecha', 'sexo', 'edad', 'numFamilia') \
        .annotate(
            total=Count('idRescate'),
            total_aereos=Count('idRescate', filter=Q(aeropuerto=True)),
            total_carreteros=Count('idRescate', filter=Q(carretero=True)),
            total_central=Count('idRescate', filter=Q(centralAutobus=True)),
            total_ferro=Count('idRescate', filter=Q(ferrocarril=True)),
            total_puestos=Count('idRescate', filter=Q(puestosADispo=True)),
            total_otros=( Count('idRescate', Q(voluntarios=True)) + 
                         Count('idRescate', Q(otro=True)) + 
                         Count('idRescate', filter=Q(aeropuerto=False, carretero=False, centralAutobus=False, ferrocarril=False ,casaSeguridad=False, hotel=False, puestosADispo=False, voluntarios=False, otro=False)) +
                         Count('idRescate', Q(casaSeguridad=True)) + 
                         Count('idRescate', Q(hotel=True))
                         ),
            ) \
        .order_by("oficinaRepre", 'puntoEstra','nacionalidad')

    datosORs = list(rescates_por_dia)

    rescates_por_dia_CHIS = RescatePunto.objects.filter(fecha__in=array_fechasDia, oficinaRepre="CHIAPAS") \
        .exclude(aeropuerto=False, carretero=True, casaSeguridad=False, centralAutobus=False, 
                ferrocarril=False, hotel=False, puestosADispo=False, voluntarios=True, 
                otro=True) \
        .values('nombre', 'apellidos', 'nacionalidad', 'oficinaRepre','puntoEstra','fecha', 'sexo', 'edad', 'numFamilia', 'idRescate') \
        .annotate(
            total=Count('idRescate'),
            total_aereos=Count('idRescate', filter=Q(aeropuerto=True)),
            total_carreteros=Count('idRescate', filter=Q(carretero=True)),
            total_central=Count('idRescate', filter=Q(centralAutobus=True)),
            total_ferro=Count('idRescate', filter=Q(ferrocarril=True)),
            total_puestos=Count('idRescate', filter=Q(puestosADispo=True)),
            total_otros=( Count('idRescate', Q(voluntarios=True)) + 
                         Count('idRescate', Q(otro=True)) + 
                         Count('idRescate', filter=Q(aeropuerto=False, carretero=False, centralAutobus=False, ferrocarril=False ,casaSeguridad=False, hotel=False, puestosADispo=False, voluntarios=False, otro=False)) +
                         Count('idRescate', Q(casaSeguridad=True)) + 
                         Count('idRescate', Q(hotel=True))
                         ),
            ) \
        .order_by("oficinaRepre", 'puntoEstra','nacionalidad')
    
    datosCHIS = list(rescates_por_dia_CHIS)

    valores_duplicados = RescatePunto.objects.all() \
        .values('nombre', 'apellidos', 'nacionalidad') \
        .annotate(veces=Count('idRescate')) \
        .filter(veces__gt=1) \
        .order_by('-veces')
    
    valores_duplicados1year = {
        (valor['nombre'], valor['apellidos'], valor['nacionalidad']): valor['veces']
        for valor in valores_duplicados
    }

    reincidentesOR = []
    rescatesNuevos = []
    rescatesTotales = []

    for dato in datosORs:
        clave = (dato['nombre'], dato['apellidos'], dato['nacionalidad'])
        veces = valores_duplicados1year.get(clave)
        rescatesTotales.append({**dato, 'veces': 1})
        if veces is not None:
            reincidentesOR.append({**dato, 'veces': veces})
        else:
            rescatesNuevos.append({**dato, 'veces': 0})

    for dato in datosCHIS:
        clave = (dato['nombre'], dato['apellidos'], dato['nacionalidad'])
        veces = valores_duplicados1year.get(clave)
        rescatesTotales.append({**dato, 'veces': 1})
        if veces is not None:
            reincidentesOR.append({**dato, 'veces': veces + 1})
        else:
            reincidentesOR.append({**dato, 'veces': 1}) # Nota: En el original agregan a reincidentes aunque sea nuevo si es CHIS? Revisar logica original. 
            # En original linea 425: reincidentesOR.append({**dato, 'veces': 1}) 
            # Parece que CHIS se trata diferente o es un bug del original, pero lo mantengo igual.

    # --------------------------------------------------------------------------
    # ------------------ Generacion de diccionarios de datos ------------------
    
    conteo_rescates = {nombre: {"total": 0, "total_aereos": 0, "total_carreteros": 0, "total_central": 0, "total_ferro": 0, "total_puestos": 0, "total_otros": 0} for nombre in oficinas}
    conteo_rescates["Total"] = {"total": 0, "total_aereos": 0, "total_carreteros": 0, "total_central": 0, "total_ferro": 0, "total_puestos": 0, "total_otros": 0}

    for dato in rescatesNuevos:
        oficina = dato["oficinaRepre"]
        if oficina in conteo_rescates:
            conteo_rescates[oficina]["total"] += dato.get("total", 0)
            conteo_rescates[oficina]["total_aereos"] += dato.get("total_aereos", 0)
            conteo_rescates[oficina]["total_carreteros"] += dato.get("total_carreteros", 0)
            conteo_rescates[oficina]["total_central"] += dato.get("total_central", 0)
            conteo_rescates[oficina]["total_ferro"] += dato.get("total_ferro", 0)
            conteo_rescates[oficina]["total_puestos"] += dato.get("total_puestos", 0)
            conteo_rescates[oficina]["total_otros"] += dato.get("total_otros", 0)

            conteo_rescates["Total"]["total"] += dato.get("total", 0)
            conteo_rescates["Total"]["total_aereos"] += dato.get("total_aereos", 0)
            conteo_rescates["Total"]["total_carreteros"] += dato.get("total_carreteros", 0)
            conteo_rescates["Total"]["total_central"] += dato.get("total_central", 0)
            conteo_rescates["Total"]["total_ferro"] += dato.get("total_ferro", 0)
            conteo_rescates["Total"]["total_puestos"] += dato.get("total_puestos", 0)
            conteo_rescates["Total"]["total_otros"] += dato.get("total_otros", 0)

    reincidentes_oficina = Counter(d["oficinaRepre"] for d in reincidentesOR)
    nuevos_oficina = Counter(d["oficinaRepre"] for d in rescatesNuevos)

    conteo_reincidentes = {nombre: {"total": 0, "total_reincidentes": 0, "total_nuevos": 0} for nombre in oficinas}
    conteo_reincidentes["Total"] = {"total": 0, "total_reincidentes": 0, "total_nuevos": 0}

    for oficina, count in reincidentes_oficina.items():
        if oficina in conteo_reincidentes:
            conteo_reincidentes[oficina]["total_reincidentes"] = count
            conteo_reincidentes['Total']["total_reincidentes"] += count

    for oficina, count in nuevos_oficina.items():
        if oficina in conteo_reincidentes:
            conteo_reincidentes[oficina]["total_nuevos"] = count
            conteo_reincidentes['Total']["total_nuevos"] += count

    for nombre in conteo_reincidentes:
        total_aux = conteo_reincidentes[nombre]['total_reincidentes'] + conteo_reincidentes[nombre]['total_nuevos']
        conteo_reincidentes[nombre]["total"] = total_aux
        conteo_reincidentes['Total']["total"] = total_aux
        
    # Nacionalidades Nuevos
    nacionalidades_nuevos = {d["nacionalidad"] for d in rescatesNuevos}
    nuevos_datos_nacio = {nacionalidad: {"H_AS": 0, "M_AS": 0, "H_mS": 0, "M_mS": 0, "H_AA": 0, "M_AA": 0, "H_mA": 0, "M_mA": 0, 'total':0 } for nacionalidad in nacionalidades_nuevos}

    for d in rescatesNuevos:
        nuevos_datos_nacio[d["nacionalidad"]]["total"] += 1
        if d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_nacio[d["nacionalidad"]]["H_AS"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_nacio[d["nacionalidad"]]["M_AS"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_nacio[d["nacionalidad"]]["H_mS"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            nuevos_datos_nacio[d["nacionalidad"]]["M_mS"] += 1
        elif d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] > 0):
            nuevos_datos_nacio[d["nacionalidad"]]["H_AA"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] > 0):
            nuevos_datos_nacio[d["nacionalidad"]]["M_AA"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] > 0):
            nuevos_datos_nacio[d["nacionalidad"]]["H_mA"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] > 0):
            nuevos_datos_nacio[d["nacionalidad"]]["M_mA"] += 1

    # Nacionalidades Reincidentes
    nacionalidades_reinc = {d["nacionalidad"] for d in reincidentesOR}
    reincidentes_datos_nacio = {nacionalidad: {"H_AS": 0, "M_AS": 0, "H_mS": 0, "M_mS": 0, "H_AA": 0, "M_AA": 0, "H_mA": 0, "M_mA": 0, 'total':0 } for nacionalidad in nacionalidades_reinc}

    for d in reincidentesOR:
        reincidentes_datos_nacio[d["nacionalidad"]]["total"] += 1
        if d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["H_AS"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["M_AS"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["H_mS"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] is None or d['numFamilia'] == 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["M_mS"] += 1
        elif d['sexo'] == True and d['edad'] >= 18 and (d['numFamilia'] > 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["H_AA"] += 1
        elif d['sexo'] == False and d['edad'] >= 18 and (d['numFamilia'] > 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["M_AA"] += 1
        elif d['sexo'] == True and d['edad'] < 18 and (d['numFamilia'] > 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["H_mA"] += 1
        elif d['sexo'] == False and d['edad'] < 18 and (d['numFamilia'] > 0):
            reincidentes_datos_nacio[d["nacionalidad"]]["M_mA"] += 1

    # Inadmitidos
    rescates_Inadm = Inadmitido.objects.filter(fecha_hora__date=fechaB).values("nac", "genero", "edad")
    nacionalidades_inad = {d["nac"] for d in rescates_Inadm}
    inadm_datos_nacio = {nacionalidad: {"H_A": 0, "M_A": 0, "H_m": 0, "M_m": 0, 'total':0 } for nacionalidad in nacionalidades_inad}

    for d in rescates_Inadm:
        inadm_datos_nacio[d["nac"]]["total"] += 1
        if d['genero'] == "H" and d['edad'] >= 18:
            inadm_datos_nacio[d["nac"]]["H_A"] += 1
        elif d['genero'] == "M" and d['edad'] >= 18:
            inadm_datos_nacio[d["nac"]]["M_A"] += 1
        elif d['genero'] == "H" and d['edad'] < 18:
            inadm_datos_nacio[d["nac"]]["H_m"] += 1 # Nota: corregido d["nacionalidad"] a d["nac"] para key, en original era nacionalidad pero dict key es nac
        elif d['genero'] == "M" and d['edad'] < 18:
             inadm_datos_nacio[d["nac"]]["M_m"] += 1 # Nota: corregido aqui tambien

    # CECO Logic 
    ORs_CECO_S = ["CAMPECHE", "CHIAPAS", "HIDALGO", "EDOMEX", "OAXACA", "PUEBLA", "QUINTANA ROO", "TABASCO", "TLAXCALA", "VERACRUZ", "YUCATÁN"]
    ORs_CECO_N = ["BAJA CALIFORNIA", "CHIHUAHUA", "COAHUILA", "DURANGO", "NUEVO LEÓN", "SAN LUIS POTOSÍ", "SINALOA", "SONORA", "TAMAULIPAS"]
    ORs_CECO_C = ["AGUASCALIENTES", "BAJA CALIFORNIA SUR", "COLIMA", "CDMX", "GUANAJUATO", "GUERRERO", "JALISCO", "MICHOACÁN", "MORELOS", "NAYARIT", "QUERÉTARO", "ZACATECAS"]

    puntoE_totales = {nombre: {"puntos": {}, "total": 0} for nombre in ORs_CECO_S}
    for dato in rescatesTotales:
        puntoEOr = dato["puntoEstra"]
        oficinaAux = dato["oficinaRepre"]
        if puntoEOr == '': puntoEOr = 'Voluntarios'
        if puntoE_totales.get(oficinaAux) is not None:
            if puntoEOr not in puntoE_totales[oficinaAux]['puntos']:
                puntoE_totales[oficinaAux]['puntos'][puntoEOr] = 0
            puntoE_totales[oficinaAux]['puntos'][puntoEOr] += 1
            puntoE_totales[oficinaAux]['total'] += 1

    # Excel Generation with OpenPyXL
    wb = Workbook()
    
    # 1. Informe Operativo
    ws1 = wb.active
    ws1.title = "Informe Operativo"
    ws1.append(["Oficina", "Aeropuertos", "Carreteros", "Central Autobus", "Ferroviarios", "Puestos a Dispo", "Otros", "Total"])
    for oficina, datos in conteo_rescates.items():
        ws1.append([oficina, datos["total_aereos"], datos["total_carreteros"], datos["total_central"], datos["total_ferro"], datos["total_puestos"], datos["total_otros"], datos["total"]])

    # 2. Reincidencias
    ws2 = wb.create_sheet("Reincidencias")
    ws2.append(["Oficina", "Registros Nuevos", "Reincidentes", "Total"])
    for oficina, datos in conteo_reincidentes.items():
        ws2.append([oficina, datos["total_nuevos"], datos["total_reincidentes"], datos["total"]])

    # 3. Nacionalidades Nuevos
    ws3 = wb.create_sheet("Nac. Nuevos")
    ws3.append(["Nacionalidad", "H_AS", "M_AS", "H_AA", "M_AA", "H_mA", "M_mA", "H_mS", "M_mS", "Total"])
    for nac, datos in nuevos_datos_nacio.items():
        ws3.append([nac, datos["H_AS"], datos["M_AS"], datos["H_AA"], datos["M_AA"], datos["H_mA"], datos["M_mA"], datos["H_mS"], datos["M_mS"], datos["total"]])

    # 4. Nacionalidades Reincidentes
    ws4 = wb.create_sheet("Nac. Reincidentes")
    ws4.append(["Nacionalidad", "H_AS", "M_AS", "H_AA", "M_AA", "H_mA", "M_mA", "H_mS", "M_mS", "Total"])
    for nac, datos in reincidentes_datos_nacio.items():
        ws4.append([nac, datos["H_AS"], datos["M_AS"], datos["H_AA"], datos["M_AA"], datos["H_mA"], datos["M_mA"], datos["H_mS"], datos["M_mS"], datos["total"]])

    # 5. Inadmitidos
    ws5 = wb.create_sheet("Inadmitidos")
    ws5.append(["Nacionalidad", "Hombres Adultos", "Mujeres Adultos", "Hombres Menores", "Mujeres Menores", "Total"])
    for nac, datos in inadm_datos_nacio.items():
        ws5.append([nac, datos["H_A"], datos["M_A"], datos["H_m"], datos["M_m"], datos["total"]])

    # 6. Puntos de Rescate
    ws6 = wb.create_sheet("Puntos Rescate")
    ws6.append(["Oficina", "Punto", "Cantidad"])
    for oficina, datos in puntoE_totales.items():
        for punto, total in datos['puntos'].items():
             ws6.append([oficina, punto, total])

    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Reporte_Completo_{fechaB.strftime("%d-%m-%Y")}.xlsx'
    wb.save(response)

    return response
